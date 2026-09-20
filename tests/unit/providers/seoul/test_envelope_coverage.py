"""envelope.py 미커버 라인을 보강하는 추가 테스트."""

from __future__ import annotations

from types import MappingProxyType

import pytest

from kpubdata.core.models import DatasetRef
from kpubdata.core.representation import Representation as Rep
from kpubdata.exceptions import ProviderResponseError
from kpubdata.providers.seoul.envelope import _normalize_rows, validate_envelope


def _make_dataset(
    *,
    dataset_key: str = "SampleService",
    top_level_result: bool = False,
) -> DatasetRef:
    """테스트용 DatasetRef를 생성한다."""
    meta: dict[str, object] = {}
    if top_level_result:
        meta["top_level_result"] = True
    return DatasetRef(
        id="seoul.sample",
        provider="seoul",
        dataset_key=dataset_key,
        name="샘플 데이터셋",
        representation=Rep.API_JSON,
        raw_metadata=MappingProxyType(meta),
    )


# -- validate_envelope: 최상위 에러 (code+message, service_name 키 없음) --


def test_top_level_error_raises(
) -> None:
    """최상위에 code/message만 있고 service_name 키가 없으면 ProviderResponseError를 발생한다."""
    payload: dict[str, object] = {
        "code": "ERROR-500",
        "message": "서버 오류 발생",
    }
    ds = _make_dataset(dataset_key="SampleService")

    with pytest.raises(ProviderResponseError):
        validate_envelope(payload, "SampleService", ds)


# -- validate_envelope: top_level_result 시나리오 --


def test_top_level_result_missing_result(
) -> None:
    """top_level_result인데 RESULT가 없으면 ProviderResponseError를 발생한다."""
    payload: dict[str, object] = {"SampleService": [{"a": 1}]}
    ds = _make_dataset(dataset_key="SampleService", top_level_result=True)

    with pytest.raises(ProviderResponseError, match="missing RESULT"):
        validate_envelope(payload, "SampleService", ds)


def test_top_level_result_success(
) -> None:
    """top_level_result이고 성공 코드면 행 목록을 반환한다."""
    rows = [{"col": "val"}]
    payload: dict[str, object] = {
        "RESULT": {"RESULT.CODE": "INFO-000", "RESULT.MESSAGE": "정상"},
        "SampleService": rows,
    }
    ds = _make_dataset(dataset_key="SampleService", top_level_result=True)

    body, result_rows = validate_envelope(payload, "SampleService", ds)

    assert body is payload
    assert result_rows == rows


def test_top_level_result_empty(
) -> None:
    """top_level_result이고 INFO-200이면 빈 리스트를 반환한다."""
    payload: dict[str, object] = {
        "RESULT": {"RESULT.CODE": "INFO-200", "RESULT.MESSAGE": "해당 데이터 없음"},
        "SampleService": [],
    }
    ds = _make_dataset(dataset_key="SampleService", top_level_result=True)

    body, result_rows = validate_envelope(payload, "SampleService", ds)

    assert result_rows == []


def test_top_level_result_error_code(
) -> None:
    """top_level_result이고 에러 코드면 ProviderResponseError를 발생한다."""
    payload: dict[str, object] = {
        "RESULT": {"RESULT.CODE": "ERROR-500", "RESULT.MESSAGE": "서버 오류"},
        "SampleService": [],
    }
    ds = _make_dataset(dataset_key="SampleService", top_level_result=True)

    with pytest.raises(ProviderResponseError):
        validate_envelope(payload, "SampleService", ds)


# -- validate_envelope: body_obj가 dict가 아닌 경우 --


def test_envelope_body_not_dict(
) -> None:
    """envelope_key에 해당하는 값이 dict가 아니면 ProviderResponseError를 발생한다."""
    payload: dict[str, object] = {"SampleService": "not-a-dict"}
    ds = _make_dataset(dataset_key="SampleService")

    with pytest.raises(ProviderResponseError, match="missing SampleService"):
        validate_envelope(payload, "SampleService", ds)


# -- _normalize_rows 엣지 케이스 --


def test_normalize_rows_dict_input() -> None:
    """dict 입력 시 단일 요소 리스트로 감싼다."""
    row: dict[str, object] = {"key": "value"}
    result = _normalize_rows(row)
    assert result == [row]


def test_normalize_rows_none() -> None:
    """None 입력 시 빈 리스트를 반환한다."""
    assert _normalize_rows(None) == []


def test_normalize_rows_non_list_non_dict() -> None:
    """list/dict가 아닌 입력 시 빈 리스트를 반환한다."""
    assert _normalize_rows("unexpected-string") == []
    assert _normalize_rows(42) == []
