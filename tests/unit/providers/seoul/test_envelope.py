"""서울 API envelope 파서의 오류·가장자리 경로 회귀 테스트 (#454).

이 파서가 응답 형상을 판정한다 — 깨지면 downstream 이 예외가 아니라 **빈 결과**를
받는다. 그래서 여기서는 성공 왕복보다 "어떤 응답을 어떤 예외로 분류하는가"와
"비어 있음과 실패를 어떻게 구분하는가"를 고정한다.
"""

from __future__ import annotations

from types import MappingProxyType

import pytest

from kpubdata.core.models import DatasetRef
from kpubdata.core.representation import Representation
from kpubdata.exceptions import AuthError, InvalidRequestError, ProviderResponseError
from kpubdata.providers.seoul.envelope import validate_envelope

_SERVICE = "TestService"


def _ref(**raw: object) -> DatasetRef:
    return DatasetRef(
        id="seoul:test",
        provider="seoul",
        dataset_key="test",
        name="Test",
        representation=Representation.API_JSON,
        raw_metadata=MappingProxyType(dict(raw)),
    )


def _envelope(code: str, *, rows: object = None, message: str = "msg") -> dict[str, object]:
    body: dict[str, object] = {"RESULT": {"CODE": code, "MESSAGE": message}}
    if rows is not None:
        body["row"] = rows
    return {_SERVICE: body}


# --- 성공/비어있음 ---------------------------------------------------------


def test_success_returns_body_and_rows() -> None:
    body, rows = validate_envelope(
        _envelope("INFO-000", rows=[{"a": 1}, {"a": 2}]), _SERVICE, _ref()
    )
    assert rows == [{"a": 1}, {"a": 2}]
    assert body["RESULT"] == {"CODE": "INFO-000", "MESSAGE": "msg"}


def test_empty_result_code_is_not_an_error() -> None:
    """INFO-200(데이터 없음)은 예외가 아니라 빈 목록이다."""
    _, rows = validate_envelope(_envelope("INFO-200"), _SERVICE, _ref())
    assert rows == []


def test_success_with_no_row_key_yields_no_rows() -> None:
    _, rows = validate_envelope(_envelope("INFO-000"), _SERVICE, _ref())
    assert rows == []


def test_single_row_object_is_wrapped_in_a_list() -> None:
    """행이 하나면 서울 API 가 dict 를 그대로 준다 — 목록으로 정규화해야 한다."""
    _, rows = validate_envelope(_envelope("INFO-000", rows={"a": 1}), _SERVICE, _ref())
    assert rows == [{"a": 1}]


@pytest.mark.parametrize("rows", ["not-a-list", 42, True])
def test_unusable_row_payload_yields_no_rows(rows: object) -> None:
    _, parsed = validate_envelope(_envelope("INFO-000", rows=rows), _SERVICE, _ref())
    assert parsed == []


def test_non_mapping_row_entries_are_dropped() -> None:
    """섞여 들어온 비-객체 항목은 버리고 나머지는 살린다."""
    _, rows = validate_envelope(
        _envelope("INFO-000", rows=[{"a": 1}, "junk", None, {"b": 2}]), _SERVICE, _ref()
    )
    assert rows == [{"a": 1}, {"b": 2}]


# --- 결과 코드 → 예외 분류 -------------------------------------------------


@pytest.mark.parametrize("code", ["INFO-100", "INFO-300"])
def test_auth_codes_raise_auth_error(code: str) -> None:
    with pytest.raises(AuthError) as exc:
        validate_envelope(_envelope(code, message="인증키 오류"), _SERVICE, _ref())
    assert exc.value.provider_code == code


@pytest.mark.parametrize("code", ["INFO-400", "ERROR-300", "ERROR-301", "ERROR-310", "ERROR-336"])
def test_request_codes_raise_invalid_request_error(code: str) -> None:
    with pytest.raises(InvalidRequestError) as exc:
        validate_envelope(_envelope(code), _SERVICE, _ref())
    assert exc.value.provider_code == code


@pytest.mark.parametrize("code", ["INFO-500", "ERROR-500", "ERROR-600", "ERROR-601"])
def test_server_codes_raise_provider_response_error(code: str) -> None:
    with pytest.raises(ProviderResponseError) as exc:
        validate_envelope(_envelope(code), _SERVICE, _ref())
    assert exc.value.provider_code == code


def test_unknown_code_still_raises_rather_than_returning_empty() -> None:
    """분류되지 않은 코드를 성공으로 흘려보내면 빈 결과가 조용히 내려간다."""
    with pytest.raises(ProviderResponseError) as exc:
        validate_envelope(_envelope("ERROR-999", message="알 수 없음"), _SERVICE, _ref())
    assert exc.value.provider_code == "ERROR-999"


def test_non_string_code_and_message_get_placeholders() -> None:
    payload: dict[str, object] = {_SERVICE: {"RESULT": {"CODE": 500, "MESSAGE": None}}}
    with pytest.raises(ProviderResponseError) as exc:
        validate_envelope(payload, _SERVICE, _ref())
    assert exc.value.provider_code == "ERROR-UNKNOWN"
    assert "Provider returned error" in str(exc.value)


# --- 형상이 어긋난 envelope ------------------------------------------------


def test_missing_service_key_is_reported_by_name() -> None:
    with pytest.raises(ProviderResponseError, match=f"missing {_SERVICE}"):
        payload: dict[str, object] = {"SomethingElse": {}}
        validate_envelope(payload, _SERVICE, _ref())


def test_service_value_that_is_not_a_mapping_is_rejected() -> None:
    with pytest.raises(ProviderResponseError, match=f"missing {_SERVICE}"):
        payload: dict[str, object] = {_SERVICE: ["not", "a", "mapping"]}
        validate_envelope(payload, _SERVICE, _ref())


def test_missing_result_block_is_rejected() -> None:
    with pytest.raises(ProviderResponseError, match="missing RESULT"):
        payload: dict[str, object] = {_SERVICE: {"row": []}}
        validate_envelope(payload, _SERVICE, _ref())


def test_result_that_is_not_a_mapping_is_rejected() -> None:
    with pytest.raises(ProviderResponseError, match="missing RESULT"):
        payload: dict[str, object] = {_SERVICE: {"RESULT": "INFO-000"}}
        validate_envelope(payload, _SERVICE, _ref())


# --- top-level RESULT 변형 -------------------------------------------------


def test_top_level_result_success() -> None:
    """일부 서비스는 RESULT 를 최상위에 두고 키 이름도 'RESULT.CODE' 형태다."""
    payload: dict[str, object] = {
        "RESULT": {"RESULT.CODE": "INFO-000", "RESULT.MESSAGE": "정상"},
        _SERVICE: [{"a": 1}],
    }
    _, rows = validate_envelope(payload, _SERVICE, _ref(top_level_result=True))
    assert rows == [{"a": 1}]


def test_top_level_result_empty_code() -> None:
    payload: dict[str, object] = {"RESULT": {"RESULT.CODE": "INFO-200", "RESULT.MESSAGE": "없음"}}
    _, rows = validate_envelope(payload, _SERVICE, _ref(top_level_result=True))
    assert rows == []


def test_top_level_result_error_code_raises() -> None:
    payload: dict[str, object] = {
        "RESULT": {"RESULT.CODE": "INFO-100", "RESULT.MESSAGE": "인증 필요"}
    }
    with pytest.raises(AuthError):
        validate_envelope(payload, _SERVICE, _ref(top_level_result=True))


def test_top_level_result_missing_block_is_rejected() -> None:
    with pytest.raises(ProviderResponseError, match="missing RESULT"):
        payload: dict[str, object] = {_SERVICE: []}
        validate_envelope(payload, _SERVICE, _ref(top_level_result=True))


# --- 최상위 code/message 오류 응답 -----------------------------------------


def test_bare_error_object_is_classified_before_envelope_parsing() -> None:
    """서비스 키 없이 code/message 만 오는 오류 응답도 같은 분류를 거친다."""
    with pytest.raises(AuthError) as exc:
        validate_envelope({"code": "INFO-100", "message": "키 없음"}, _SERVICE, _ref())
    assert exc.value.provider_code == "INFO-100"


def test_bare_error_object_with_non_string_fields() -> None:
    with pytest.raises(ProviderResponseError) as exc:
        validate_envelope({"code": 1, "message": 2}, _SERVICE, _ref())
    assert exc.value.provider_code == "ERROR-UNKNOWN"


def test_code_and_message_alongside_the_service_key_are_not_an_error() -> None:
    """정상 응답이 code/message 를 함께 담고 있어도 오류로 오판하면 안 된다."""
    payload: dict[str, object] = {
        "code": "INFO-000",
        "message": "정상",
        _SERVICE: {"RESULT": {"CODE": "INFO-000", "MESSAGE": "정상"}, "row": [{"a": 1}]},
    }
    _, rows = validate_envelope(payload, _SERVICE, _ref())
    assert rows == [{"a": 1}]


# --- envelope_key 재정의 ---------------------------------------------------


def test_envelope_key_override_is_used_when_present() -> None:
    payload: dict[str, object] = {"OtherKey": {"RESULT": {"CODE": "INFO-000"}, "row": [{"a": 1}]}}
    _, rows = validate_envelope(payload, _SERVICE, _ref(envelope_key="OtherKey"))
    assert rows == [{"a": 1}]


def test_envelope_key_override_falls_back_when_absent_from_payload() -> None:
    """재정의한 키가 응답에 없으면 서비스 이름으로 돌아간다 — 바로 실패하지 않는다."""
    payload = _envelope("INFO-000", rows=[{"a": 1}])
    _, rows = validate_envelope(payload, _SERVICE, _ref(envelope_key="Missing"))
    assert rows == [{"a": 1}]


@pytest.mark.parametrize("override", ["", 123, None])
def test_unusable_envelope_key_override_is_ignored(override: object) -> None:
    payload = _envelope("INFO-000", rows=[{"a": 1}])
    _, rows = validate_envelope(payload, _SERVICE, _ref(envelope_key=override))
    assert rows == [{"a": 1}]
