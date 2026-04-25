from __future__ import annotations

import pytest

from kpubdata.exceptions import ConfigError
from kpubdata.providers._common import build_dataset_ref, load_catalogue


class _FakeCatalogueFile:
    def __init__(self, text: str) -> None:
        self._text: str = text

    def read_text(self, *, encoding: str = "utf-8") -> str:
        assert encoding == "utf-8"
        return self._text


class _FakePackageFiles:
    def __init__(self, text: str) -> None:
        self._text: str = text

    def joinpath(self, path: str) -> _FakeCatalogueFile:
        assert path == "catalogue.json"
        return _FakeCatalogueFile(self._text)


def test_load_catalogue_raises_for_duplicate_dataset_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    import kpubdata.providers._common as common_module

    def _fake_files(_package_name: str) -> _FakePackageFiles:
        return _FakePackageFiles(
            """
            [
              {"dataset_key": "dup", "name": "First", "representation": "api_json"},
              {"dataset_key": "dup", "name": "Second", "representation": "api_xml"}
            ]
            """
        )

    monkeypatch.setattr(
        common_module,
        "files",
        _fake_files,
    )

    with pytest.raises(ConfigError, match=r"duplicate dataset ids: test\.dup"):
        _ = load_catalogue("fake.package", "test")


def test_build_dataset_ref_raises_for_invalid_representation() -> None:
    with pytest.raises(ConfigError, match="invalid representation"):
        _ = build_dataset_ref(
            "test",
            {
                "dataset_key": "sample",
                "name": "Sample",
                "representation": "not_real",
            },
        )


def test_build_dataset_ref_raises_for_invalid_operation() -> None:
    with pytest.raises(ConfigError, match="invalid operation"):
        _ = build_dataset_ref(
            "test",
            {
                "dataset_key": "sample",
                "name": "Sample",
                "representation": "api_json",
                "operations": ["list", "bogus"],
            },
        )


def test_build_dataset_ref_raises_for_invalid_pagination_mode() -> None:
    with pytest.raises(ConfigError, match=r"query_support\.pagination has invalid value"):
        _ = build_dataset_ref(
            "test",
            {
                "dataset_key": "sample",
                "name": "Sample",
                "representation": "api_json",
                "query_support": {"pagination": "page_number"},
            },
        )


@pytest.mark.parametrize("field_name", ["dataset_key", "name", "representation"])
def test_build_dataset_ref_raises_for_missing_required_fields(field_name: str) -> None:
    entry: dict[str, object] = {
        "dataset_key": "sample",
        "name": "Sample",
        "representation": "api_json",
    }
    del entry[field_name]

    with pytest.raises(ConfigError, match=rf"missing non-empty string field: {field_name}"):
        _ = build_dataset_ref("test", entry)


@pytest.mark.parametrize(
    ("package_name", "provider"),
    [
        ("kpubdata.providers.datago", "datago"),
        ("kpubdata.providers.bok", "bok"),
        ("kpubdata.providers.kosis", "kosis"),
    ],
)
def test_valid_provider_catalogues_pass_validation(package_name: str, provider: str) -> None:
    datasets = load_catalogue(package_name, provider)

    assert datasets
    assert all(dataset.provider == provider for dataset in datasets)


class TestBuildDatasetRefMetadata:
    def test_description_parsed(self) -> None:
        ref = build_dataset_ref(
            "test",
            {
                "dataset_key": "s",
                "name": "S",
                "representation": "api_json",
                "description": "A test dataset",
            },
        )
        assert ref.description == "A test dataset"
        assert "description" not in ref.raw_metadata

    def test_description_empty_string_becomes_none(self) -> None:
        ref = build_dataset_ref(
            "test",
            {"dataset_key": "s", "name": "S", "representation": "api_json", "description": ""},
        )
        assert ref.description is None

    def test_description_absent_is_none(self) -> None:
        ref = build_dataset_ref(
            "test",
            {"dataset_key": "s", "name": "S", "representation": "api_json"},
        )
        assert ref.description is None

    def test_tags_parsed(self) -> None:
        ref = build_dataset_ref(
            "test",
            {
                "dataset_key": "s",
                "name": "S",
                "representation": "api_json",
                "tags": ["weather", "forecast"],
            },
        )
        assert ref.tags == ("weather", "forecast")
        assert "tags" not in ref.raw_metadata

    def test_tags_absent_is_empty(self) -> None:
        ref = build_dataset_ref(
            "test",
            {"dataset_key": "s", "name": "S", "representation": "api_json"},
        )
        assert ref.tags == ()

    def test_tags_filters_non_strings(self) -> None:
        ref = build_dataset_ref(
            "test",
            {
                "dataset_key": "s",
                "name": "S",
                "representation": "api_json",
                "tags": ["valid", 123, None, "also_valid"],
            },
        )
        assert ref.tags == ("valid", "also_valid")

    def test_source_url_parsed(self) -> None:
        ref = build_dataset_ref(
            "test",
            {
                "dataset_key": "s",
                "name": "S",
                "representation": "api_json",
                "source_url": "https://data.go.kr/example",
            },
        )
        assert ref.source_url == "https://data.go.kr/example"
        assert "source_url" not in ref.raw_metadata

    def test_source_url_absent_is_none(self) -> None:
        ref = build_dataset_ref(
            "test",
            {"dataset_key": "s", "name": "S", "representation": "api_json"},
        )
        assert ref.source_url is None

    def test_existing_description_removed_from_raw_metadata(self) -> None:
        ref = build_dataset_ref(
            "test",
            {
                "dataset_key": "s",
                "name": "S",
                "representation": "api_json",
                "description": "test",
                "base_url": "http://example.com",
            },
        )
        assert "description" not in ref.raw_metadata
        assert "base_url" in ref.raw_metadata


class TestBuildSchemaConstraints:
    def _make_ref_with_fields(self, fields: list[dict[str, object]]) -> object:
        from kpubdata.providers._common import build_dataset_ref, build_schema_from_metadata

        raw = {
            "dataset_key": "test_ds",
            "name": "Test",
            "representation": "api_json",
            "fields": fields,
        }
        ref = build_dataset_ref("test", raw)
        return build_schema_from_metadata(ref)

    def test_no_constraints_returns_none_on_field(self) -> None:
        schema = self._make_ref_with_fields([{"name": "col1", "type": "string"}])
        assert schema is not None
        assert schema.fields[0].constraints is None

    def test_constraints_parsed(self) -> None:
        schema = self._make_ref_with_fields(
            [
                {
                    "name": "time",
                    "type": "string",
                    "constraints": {"format": "YYYYMM", "pattern": r"^\d{6}$"},
                }
            ]
        )
        assert schema is not None
        fc = schema.fields[0].constraints
        assert fc is not None
        assert fc.format == "YYYYMM"
        assert fc.pattern == r"^\d{6}$"
        assert fc.max_length is None

    def test_constraints_max_length_and_values(self) -> None:
        schema = self._make_ref_with_fields(
            [
                {
                    "name": "status",
                    "type": "string",
                    "constraints": {
                        "max_length": 10,
                        "allowed_values": ["A", "B", "C"],
                    },
                }
            ]
        )
        assert schema is not None
        fc = schema.fields[0].constraints
        assert fc is not None
        assert fc.max_length == 10
        assert fc.allowed_values == ("A", "B", "C")

    def test_constraints_numeric(self) -> None:
        schema = self._make_ref_with_fields(
            [
                {
                    "name": "score",
                    "type": "number",
                    "constraints": {"min_value": 0, "max_value": 100.5},
                }
            ]
        )
        assert schema is not None
        fc = schema.fields[0].constraints
        assert fc is not None
        assert fc.min_value == 0
        assert fc.max_value == 100.5

    def test_empty_constraints_dict_returns_none(self) -> None:
        schema = self._make_ref_with_fields([{"name": "col", "type": "string", "constraints": {}}])
        assert schema is not None
        assert schema.fields[0].constraints is None

    def test_invalid_constraints_type_ignored(self) -> None:
        schema = self._make_ref_with_fields(
            [{"name": "col", "type": "string", "constraints": "invalid"}]
        )
        assert schema is not None
        assert schema.fields[0].constraints is None
