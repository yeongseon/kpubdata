"""core/spec.py 로더 단위 테스트 — fixture 표본과 번들 골든 spec 검증."""

from pathlib import Path

import pytest

from kpubdata.core.spec import (
    discover_specs,
    find_spec,
    load_spec_file,
    spec_index,
)
from kpubdata.exceptions import InvalidRequestError

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "specs"


# ----------------------------------------------------------------------
# from_mapping / load_spec_file
# ----------------------------------------------------------------------


def test_from_mapping_minimal() -> None:
    """최소 필수 필드만으로 로드에 성공한다."""
    spec = load_spec_file(FIXTURES_DIR / "valid_minimal.yaml")
    assert spec.id == "test.minimal"
    assert spec.provider == "test"
    assert spec.dataset_key == "minimal"
    assert spec.auth.type == "none"
    assert spec.pagination.type == "none"
    assert spec.params == ()
    assert spec.fields == ()
    assert spec.examples == ()


def test_from_mapping_full_sections() -> None:
    """모든 스키마 섹션이 올바르게 해석된다."""
    spec = load_spec_file(FIXTURES_DIR / "valid_full.yaml")
    assert spec.endpoint.format_param is not None
    assert spec.endpoint.format_param.name == "_type"
    assert spec.endpoint.format_param.values == {"json": "json", "xml": "xml"}
    assert spec.auth.param_name == "serviceKey"
    assert spec.auth.provider_key == "datago"

    param = spec.params[0]
    assert param.name == "LAWD_CD"
    assert param.alias == "region_code"
    assert param.exposed_name == "region_code"
    assert param.required is True

    assert spec.response.format == "xml"
    assert spec.response.total_count_path == "response.body.totalCount"
    assert spec.response.error.ok_values == ("00", "000", 0)

    assert spec.pagination.type == "page_no_rows"
    assert spec.pagination.max_size == 1000

    field = spec.fields[0]
    assert field.source_name == "거래금액"
    assert field.transform == "strip_comma"

    example = spec.examples[0]
    assert example.params == {"region_code": "11110"}
    assert example.format == "xml"

    assert spec.last_verified is not None
    assert spec.source is not None and spec.source.doc_version == "v1.2"

    # 미선언 키는 raw_metadata에 보존된다(상위 호환).
    assert spec.raw_metadata.get("custom_future_field") == "보존되어야 하는 미선언 키"


def test_from_mapping_invalid_id_format() -> None:
    """provider.dataset 형식이 아닌 id는 모든 문제와 함께 실패한다."""
    with pytest.raises(InvalidRequestError) as exc_info:
        load_spec_file(FIXTURES_DIR / "invalid_bad_id.yaml")
    assert "형식이어야 합니다" in str(exc_info.value)


def test_from_mapping_invalid_enum_lists_all_problems() -> None:
    """enum 위반 여러 건이 하나의 메시지에 모두 나열된다."""
    with pytest.raises(InvalidRequestError) as exc_info:
        load_spec_file(FIXTURES_DIR / "invalid_bad_enum.yaml")
    message = str(exc_info.value)
    assert "auth.type" in message
    assert "response.format" in message
    assert "pagination.type" in message
    assert "status" in message


def test_from_mapping_missing_required() -> None:
    """endpoint·response·pagination 누락이 각각 보고된다."""
    with pytest.raises(InvalidRequestError) as exc_info:
        load_spec_file(FIXTURES_DIR / "invalid_missing_required.yaml")
    message = str(exc_info.value)
    assert "endpoint" in message
    assert "response" in message
    assert "pagination" in message


def test_from_mapping_id_provider_mismatch() -> None:
    """id 접두사와 provider 불일치가 보고된다."""
    with pytest.raises(InvalidRequestError, match="불일치"):
        load_spec_file(FIXTURES_DIR / "invalid_id_mismatch.yaml")


# ----------------------------------------------------------------------
# discover_specs / find_spec / spec_index
# ----------------------------------------------------------------------


def test_discover_specs_valid_only_root(tmp_path: Path) -> None:
    """유효한 spec만 있는 디렉터리는 전부 로드한다(invalid_* 제외 검증)."""
    valid_dir = tmp_path / "valid"
    valid_dir.mkdir()
    for name in ("valid_minimal.yaml", "valid_full.yaml"):
        target = valid_dir / name
        target.write_text((FIXTURES_DIR / name).read_text(encoding="utf-8"), encoding="utf-8")
    specs = discover_specs(valid_dir)
    assert {spec.id for spec in specs} == {"test.minimal", "test.full"}


def test_discover_specs_invalid_fixture_raises() -> None:
    """무효 spec이 포함된 디렉터리 스캔은 구조 검증 예외를 전파한다."""
    with pytest.raises(InvalidRequestError):
        discover_specs(FIXTURES_DIR)


def test_discover_bundled_golden_specs() -> None:
    """패키지에 번들된 골든 예제 3종이 발견된다."""
    specs = discover_specs()
    ids = {spec.id for spec in specs}
    assert {
        "datago.apt_trade",
        "datago.hospital_info",
        "datago.village_fcst",
    } <= ids


def test_spec_index_and_find_spec_lookup() -> None:
    """full id·bare key·provider 한정 조회가 모두 동작한다."""
    index = spec_index()
    assert "datago.apt_trade" in index

    by_full = find_spec("datago.apt_trade")
    assert by_full is not None and by_full.id == "datago.apt_trade"

    by_bare = find_spec("village_fcst", provider="datago")
    assert by_bare is not None and by_bare.id == "datago.village_fcst"

    assert find_spec("no.such_dataset") is None
