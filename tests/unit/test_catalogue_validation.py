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
