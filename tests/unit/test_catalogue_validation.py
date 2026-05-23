"""테스트 모듈.

이 파일은 ``tests/unit/test_catalogue_validation.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

import pytest

from kpubdata.exceptions import ConfigError
from kpubdata.providers._common import build_dataset_ref, load_catalogue


class _FakeCatalogueFile:
    """
    _FakeCatalogueFile 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/test_catalogue_validation.py`` 모듈 안에서 _FakeCatalogueFile의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__, read_text.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    def __init__(self, text: str) -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        매개변수:
            text (str): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self._text: str = text

    def read_text(self, *, encoding: str = "utf-8") -> str:
        """
        read text 동작을 수행한다.

        매개변수:
            encoding (str): 호출자가 제공하는 입력 값이다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        assert encoding == "utf-8"
        return self._text


class _FakePackageFiles:
    """
    _FakePackageFiles 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/test_catalogue_validation.py`` 모듈 안에서 _FakePackageFiles의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__, joinpath.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    def __init__(self, text: str) -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        매개변수:
            text (str): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self._text: str = text

    def joinpath(self, path: str) -> _FakeCatalogueFile:
        """
        joinpath 동작을 수행한다.

        매개변수:
            path (str): 호출자가 제공하는 입력 값이다.

        반환값:
            _FakeCatalogueFile: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        assert path == "catalogue.json"
        return _FakeCatalogueFile(self._text)


# test load catalogue raises for duplicate dataset ids 테스트가 검증하는 시나리오를 설명한다.
def test_load_catalogue_raises_for_duplicate_dataset_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    test load catalogue raises for duplicate dataset ids 시나리오를 검증한다.

    매개변수:
        monkeypatch (pytest.MonkeyPatch): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    import kpubdata.providers._common as common_module

    def _fake_files(_package_name: str) -> _FakePackageFiles:
        """
        내부 헬퍼로서 fake files 처리를 담당한다.

        매개변수:
            _package_name (str): 호출자가 제공하는 입력 값이다.

        반환값:
            _FakePackageFiles: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
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


# test build dataset ref raises for invalid representation 테스트가 검증하는 시나리오를 설명한다.
def test_build_dataset_ref_raises_for_invalid_representation() -> None:
    """
    test build dataset ref raises for invalid representation 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    with pytest.raises(ConfigError, match="invalid representation"):
        _ = build_dataset_ref(
            "test",
            {
                "dataset_key": "sample",
                "name": "Sample",
                "representation": "not_real",
            },
        )


# test build dataset ref raises for invalid operation 테스트가 검증하는 시나리오를 설명한다.
def test_build_dataset_ref_raises_for_invalid_operation() -> None:
    """
    test build dataset ref raises for invalid operation 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
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


# test build dataset ref raises for invalid pagination mode 테스트가 검증하는 시나리오를 설명한다.
def test_build_dataset_ref_raises_for_invalid_pagination_mode() -> None:
    """
    test build dataset ref raises for invalid pagination mode 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
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


# test build dataset ref raises for missing required fields 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.parametrize("field_name", ["dataset_key", "name", "representation"])
def test_build_dataset_ref_raises_for_missing_required_fields(field_name: str) -> None:
    """
    test build dataset ref raises for missing required fields 시나리오를 검증한다.

    매개변수:
        field_name (str): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    entry: dict[str, object] = {
        "dataset_key": "sample",
        "name": "Sample",
        "representation": "api_json",
    }
    del entry[field_name]

    with pytest.raises(ConfigError, match=rf"missing non-empty string field: {field_name}"):
        _ = build_dataset_ref("test", entry)


# test valid provider catalogues pass validation 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.parametrize(
    ("package_name", "provider"),
    [
        ("kpubdata.providers.datago", "datago"),
        ("kpubdata.providers.bok", "bok"),
        ("kpubdata.providers.kosis", "kosis"),
    ],
)
def test_valid_provider_catalogues_pass_validation(package_name: str, provider: str) -> None:
    """
    test valid provider catalogues pass validation 시나리오를 검증한다.

    매개변수:
        package_name (str): 호출자가 제공하는 입력 값이다.
        provider (str): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    datasets = load_catalogue(package_name, provider)

    assert datasets
    assert all(dataset.provider == provider for dataset in datasets)


class TestBuildDatasetRefMetadata:
    """
    TestBuildDatasetRefMetadata 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/test_catalogue_validation.py`` 모듈 안에서 TestBuildDatasetRefMetadata의 상태와 동작을 함께 관리한다.
    주요 메서드: test_description_parsed, test_description_empty_string_becomes_none, test_description_absent_is_none, test_tags_parsed, test_tags_absent_is_empty.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    # test description parsed 테스트가 검증하는 시나리오를 설명한다.
    def test_description_parsed(self) -> None:
        """
        test description parsed 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
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

    # test description empty string becomes none 테스트가 검증하는 시나리오를 설명한다.
    def test_description_empty_string_becomes_none(self) -> None:
        """
        test description empty string becomes none 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        ref = build_dataset_ref(
            "test",
            {"dataset_key": "s", "name": "S", "representation": "api_json", "description": ""},
        )
        assert ref.description is None

    # test description absent is none 테스트가 검증하는 시나리오를 설명한다.
    def test_description_absent_is_none(self) -> None:
        """
        test description absent is none 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        ref = build_dataset_ref(
            "test",
            {"dataset_key": "s", "name": "S", "representation": "api_json"},
        )
        assert ref.description is None

    # test tags parsed 테스트가 검증하는 시나리오를 설명한다.
    def test_tags_parsed(self) -> None:
        """
        test tags parsed 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
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

    # test tags absent is empty 테스트가 검증하는 시나리오를 설명한다.
    def test_tags_absent_is_empty(self) -> None:
        """
        test tags absent is empty 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        ref = build_dataset_ref(
            "test",
            {"dataset_key": "s", "name": "S", "representation": "api_json"},
        )
        assert ref.tags == ()

    # test tags filters non strings 테스트가 검증하는 시나리오를 설명한다.
    def test_tags_filters_non_strings(self) -> None:
        """
        test tags filters non strings 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
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

    # test source url parsed 테스트가 검증하는 시나리오를 설명한다.
    def test_source_url_parsed(self) -> None:
        """
        test source url parsed 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
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

    # test source url absent is none 테스트가 검증하는 시나리오를 설명한다.
    def test_source_url_absent_is_none(self) -> None:
        """
        test source url absent is none 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        ref = build_dataset_ref(
            "test",
            {"dataset_key": "s", "name": "S", "representation": "api_json"},
        )
        assert ref.source_url is None

    # test existing description removed from raw metadata 테스트가 검증하는 시나리오를 설명한다.
    def test_existing_description_removed_from_raw_metadata(self) -> None:
        """
        test existing description removed from raw metadata 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
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
    """
    TestBuildSchemaConstraints 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/test_catalogue_validation.py`` 모듈 안에서 TestBuildSchemaConstraints의 상태와 동작을 함께 관리한다.
    주요 메서드: _make_ref_with_fields, test_no_constraints_returns_none_on_field, test_constraints_parsed, test_constraints_max_length_and_values, test_constraints_numeric.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    def _make_ref_with_fields(self, fields: list[dict[str, object]]) -> object:
        """
        내부 헬퍼로서 make ref with fields 처리를 담당한다.

        매개변수:
            fields (list[dict[str, object]]): 호출자가 제공하는 입력 값이다.

        반환값:
            object: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        from kpubdata.providers._common import build_dataset_ref, build_schema_from_metadata

        raw = {
            "dataset_key": "test_ds",
            "name": "Test",
            "representation": "api_json",
            "fields": fields,
        }
        ref = build_dataset_ref("test", raw)
        return build_schema_from_metadata(ref)

    # test no constraints returns none on field 테스트가 검증하는 시나리오를 설명한다.
    def test_no_constraints_returns_none_on_field(self) -> None:
        """
        test no constraints returns none on field 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        schema = self._make_ref_with_fields([{"name": "col1", "type": "string"}])
        assert schema is not None
        assert schema.fields[0].constraints is None

    # test constraints parsed 테스트가 검증하는 시나리오를 설명한다.
    def test_constraints_parsed(self) -> None:
        """
        test constraints parsed 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
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

    # test constraints max length and values 테스트가 검증하는 시나리오를 설명한다.
    def test_constraints_max_length_and_values(self) -> None:
        """
        test constraints max length and values 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
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

    # test constraints numeric 테스트가 검증하는 시나리오를 설명한다.
    def test_constraints_numeric(self) -> None:
        """
        test constraints numeric 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
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

    # test empty constraints dict returns none 테스트가 검증하는 시나리오를 설명한다.
    def test_empty_constraints_dict_returns_none(self) -> None:
        """
        test empty constraints dict returns none 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        schema = self._make_ref_with_fields([{"name": "col", "type": "string", "constraints": {}}])
        assert schema is not None
        assert schema.fields[0].constraints is None

    # test invalid constraints type ignored 테스트가 검증하는 시나리오를 설명한다.
    def test_invalid_constraints_type_ignored(self) -> None:
        """
        test invalid constraints type ignored 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        schema = self._make_ref_with_fields(
            [{"name": "col", "type": "string", "constraints": "invalid"}]
        )
        assert schema is not None
        assert schema.fields[0].constraints is None
