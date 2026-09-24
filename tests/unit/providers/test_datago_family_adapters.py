"""localdata·semas 어댑터의 파라미터 매핑과 오류 응답 회귀 테스트 (#454).

두 어댑터는 data.go.kr 인증 체계를 공유하고 envelope·result code 처리 구조가 거의
같다. 한 곳을 고치고 다른 곳을 잊는 일이 생기기 쉬우므로, 공통 계약은 같은
파라미터 세트로 두 어댑터에 동시에 건다.

기존 `tests/unit/providers/{localdata,semas}/test_adapter.py` 는 fixture 기반 성공
경로를 다룬다. 여기서는 그 바깥 — **요청을 어떻게 만드는가**와 **잘못된 응답을 어떤
예외로 분류하는가** — 를 고정한다.
"""

from __future__ import annotations

import json
from types import MappingProxyType
from typing import Any, cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef
from kpubdata.core.representation import Representation
from kpubdata.exceptions import (
    AuthError,
    ConfigError,
    DatasetNotFoundError,
    InvalidRequestError,
    ParseError,
    ProviderResponseError,
    RateLimitError,
    ServiceUnavailableError,
)
from kpubdata.providers.localdata.adapter import LocaldataAdapter
from kpubdata.providers.semas.adapter import SemasAdapter
from kpubdata.transport.http import HttpTransport

_ADAPTERS = [
    pytest.param(LocaldataAdapter, "localdata", id="localdata"),
    pytest.param(SemasAdapter, "semas", id="semas"),
]

# data.go.kr 키가 붙을 수 있는 env var. ``KPubDataConfig(provider_keys={})`` 는 키가
# "없는" 설정이 아니다 — ``get_provider_key`` 가 이 둘을 차례로 본다(config.py). 지우지
# 않으면 키를 export 해 둔 개발자 머신에서만 "요청 전에 막는다" 테스트가 실패한다.
_KEY_ENV_VARS = ("KPUBDATA_DATAGO_API_KEY", "DATAGO_API_KEY")


@pytest.fixture(autouse=True)
def _no_ambient_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in _KEY_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


class _FakeResponse:
    def __init__(self, payload: object, *, content_type: str = "application/json") -> None:
        self.headers: dict[str, str] = {"content-type": content_type}
        body = payload if isinstance(payload, str) else json.dumps(payload)
        self.text: str = body
        self.content: bytes = body.encode("utf-8")


class _FakeTransport:
    def __init__(self, *responses: _FakeResponse) -> None:
        self._responses: list[_FakeResponse] = list(responses)
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> _FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        return self._responses.pop(0)


def _adapter(cls: Any, *responses: _FakeResponse, api_key: str | None = "test-key") -> Any:
    keys = {"datago": api_key} if api_key is not None else {}
    return cls(
        config=KPubDataConfig(provider_keys=keys),
        transport=cast(HttpTransport, cast(object, _FakeTransport(*responses))),
    )


def _ref(provider: str, **raw: object) -> DatasetRef:
    return DatasetRef(
        id=f"{provider}:probe",
        provider=provider,
        dataset_key="probe",
        name="Probe",
        representation=Representation.API_JSON,
        raw_metadata=MappingProxyType(dict(raw)),
    )


def _envelope(code: str, *, msg: str = "결과", items: object = None) -> dict[str, object]:
    body: dict[str, object] = {}
    if items is not None:
        body["items"] = items
    return {"response": {"header": {"resultCode": code, "resultMsg": msg}, "body": body}}


# --- API 키 요구 -----------------------------------------------------------


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_adapter_declares_it_requires_an_api_key(cls: Any, provider: str) -> None:
    assert cls.requires_api_key is True


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_missing_api_key_fails_before_any_request(cls: Any, provider: str) -> None:
    """두 어댑터 모두 data.go.kr 키 하나(``datago``)를 공유한다 — 없으면 요청 전에 막는다."""
    adapter = _adapter(cls, api_key=None)
    with pytest.raises(ConfigError):
        adapter._build_base_params(_ref(provider, base_url="https://api.test/svc"))


# --- 요청 URL 구성 ---------------------------------------------------------


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_url_uses_the_default_operation(cls: Any, provider: str) -> None:
    adapter = _adapter(cls)
    dataset = _ref(provider, base_url="https://api.test/svc", default_operation="getList")
    assert adapter._build_request_url(dataset) == "https://api.test/svc/getList"


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_explicit_operation_overrides_the_default(cls: Any, provider: str) -> None:
    adapter = _adapter(cls)
    dataset = _ref(provider, base_url="https://api.test/svc", default_operation="getList")
    assert adapter._build_request_url(dataset, "getOne") == "https://api.test/svc/getOne"


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_url_without_any_operation_is_the_base_url(cls: Any, provider: str) -> None:
    adapter = _adapter(cls)
    assert (
        adapter._build_request_url(_ref(provider, base_url="https://api.test/svc"))
        == "https://api.test/svc"
    )


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
@pytest.mark.parametrize("operation", ["", 123, None])
def test_unusable_operation_metadata_falls_back_to_the_base_url(
    cls: Any, provider: str, operation: object
) -> None:
    adapter = _adapter(cls)
    dataset = _ref(provider, base_url="https://api.test/svc", default_operation=operation)
    assert adapter._build_request_url(dataset) == "https://api.test/svc"


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
@pytest.mark.parametrize("base_url", ["", None, 42])
def test_missing_base_url_is_a_provider_response_error(
    cls: Any, provider: str, base_url: object
) -> None:
    """카탈로그 메타데이터가 비면 엉뚱한 URL 로 요청하지 말고 즉시 실패해야 한다."""
    adapter = _adapter(cls)
    with pytest.raises(ProviderResponseError, match="missing base_url"):
        adapter._build_request_url(_ref(provider, base_url=base_url))


# --- 기본 파라미터 매핑 ----------------------------------------------------


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_default_parameter_names_are_used_when_metadata_is_silent(cls: Any, provider: str) -> None:
    params = _adapter(cls)._build_base_params(_ref(provider, base_url="https://api.test/svc"))
    assert params == {"serviceKey": "test-key", "type": "json"}


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_metadata_can_rename_the_key_and_format_parameters(cls: Any, provider: str) -> None:
    """서비스마다 파라미터 이름이 다르다 — 카탈로그가 이름을 갈아끼울 수 있어야 한다."""
    params = _adapter(cls)._build_base_params(
        _ref(
            provider,
            base_url="https://api.test/svc",
            service_key_param="authKey",
            format_param="resultType",
        )
    )
    assert params == {"authKey": "test-key", "resultType": "json"}


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
@pytest.mark.parametrize("bad", ["", None, 7])
def test_unusable_parameter_name_metadata_falls_back_to_defaults(
    cls: Any, provider: str, bad: object
) -> None:
    params = _adapter(cls)._build_base_params(
        _ref(provider, base_url="https://api.test/svc", service_key_param=bad, format_param=bad)
    )
    assert params == {"serviceKey": "test-key", "type": "json"}


# --- 응답 디코딩 -----------------------------------------------------------


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_json_response_is_decoded(cls: Any, provider: str) -> None:
    adapter = _adapter(cls, _FakeResponse({"response": {"ok": True}}))
    assert adapter._request_and_decode("https://api.test/svc", {"page": 1}, "d") == {
        "response": {"ok": True}
    }


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_request_parameters_are_stringified(cls: Any, provider: str) -> None:
    """transport 는 문자열 파라미터를 받는다 — 숫자/불리언이 그대로 새면 안 된다."""
    adapter = _adapter(cls, _FakeResponse({"response": {}}))
    adapter._request_and_decode("https://api.test/svc", {"page": 1, "all": True}, "d")
    call = adapter._transport.calls[0]
    assert call["params"] == {"page": "1", "all": "True"}
    assert call["method"] == "GET"
    assert call["provider"] == provider


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_xml_response_is_decoded_by_content_type(cls: Any, provider: str) -> None:
    xml = "<response><header><resultCode>00</resultCode></header></response>"
    adapter = _adapter(cls, _FakeResponse(xml, content_type="application/xml"))
    decoded = adapter._request_and_decode("https://api.test/svc", {}, "d")
    assert "response" in decoded


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_unparsable_body_raises_parse_error_tagged_with_the_provider(
    cls: Any, provider: str
) -> None:
    adapter = _adapter(cls, _FakeResponse("{not json", content_type="application/json"))
    with pytest.raises(ParseError) as exc:
        adapter._request_and_decode("https://api.test/svc", {}, "d")
    assert exc.value.provider == provider


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_non_object_payload_raises_parse_error(cls: Any, provider: str) -> None:
    """최상위가 배열이면 envelope 검증이 불가능하다 — 빈 결과로 넘기지 않는다."""
    adapter = _adapter(cls, _FakeResponse([1, 2, 3]))
    with pytest.raises(ParseError, match="not an object"):
        adapter._request_and_decode("https://api.test/svc", {}, "d")


# --- envelope 검증 ---------------------------------------------------------


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_missing_response_block_is_rejected(cls: Any, provider: str) -> None:
    with pytest.raises(ProviderResponseError, match="missing response"):
        _adapter(cls)._validate_envelope({"nothing": "here"}, "d")


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_missing_header_is_rejected(cls: Any, provider: str) -> None:
    with pytest.raises(ProviderResponseError, match="missing header"):
        _adapter(cls)._validate_envelope({"response": {"body": {}}}, "d")


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_missing_result_code_is_rejected(cls: Any, provider: str) -> None:
    """resultCode 가 없으면 성공 여부를 알 수 없다 — 성공으로 가정하지 않는다."""
    with pytest.raises(ProviderResponseError, match="missing resultCode"):
        _adapter(cls)._validate_envelope({"response": {"header": {}, "body": {}}}, "d")


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_non_mapping_body_becomes_an_empty_body(cls: Any, provider: str) -> None:
    payload = {"response": {"header": {"resultCode": "00"}, "body": "oops"}}
    body, items = _adapter(cls)._validate_envelope(payload, "d")
    assert body == {}
    assert items == []


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_non_string_result_message_gets_a_placeholder(cls: Any, provider: str) -> None:
    payload = {"response": {"header": {"resultCode": "99", "resultMsg": None}, "body": {}}}
    with pytest.raises(ProviderResponseError, match="Provider returned error"):
        _adapter(cls)._validate_envelope(payload, "d")


# --- result code 분류 ------------------------------------------------------


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
@pytest.mark.parametrize("code", ["20", "30", "31", "32"])
def test_auth_codes_raise_auth_error(cls: Any, provider: str, code: str) -> None:
    with pytest.raises(AuthError) as exc:
        _adapter(cls)._validate_envelope(_envelope(code), "d")
    assert exc.value.provider_code == code
    assert exc.value.provider == provider


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_quota_code_raises_a_non_retryable_rate_limit_error(cls: Any, provider: str) -> None:
    """22 는 일일 한도 초과다 — 재시도해도 풀리지 않으므로 retryable 이 아니어야 한다."""
    with pytest.raises(RateLimitError) as exc:
        _adapter(cls)._validate_envelope(_envelope("22"), "d")
    assert exc.value.retryable is False


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_bad_request_code_raises_invalid_request_error(cls: Any, provider: str) -> None:
    with pytest.raises(InvalidRequestError):
        _adapter(cls)._validate_envelope(_envelope("10"), "d")


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_unknown_service_code_raises_dataset_not_found(cls: Any, provider: str) -> None:
    with pytest.raises(DatasetNotFoundError) as exc:
        _adapter(cls)._validate_envelope(_envelope("12"), "probe-dataset")
    assert exc.value.dataset_id == "probe-dataset"


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
@pytest.mark.parametrize("code", ["01", "02"])
def test_service_codes_raise_service_unavailable(cls: Any, provider: str, code: str) -> None:
    with pytest.raises(ServiceUnavailableError):
        _adapter(cls)._validate_envelope(_envelope(code), "d")


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_unmapped_failure_code_still_raises(cls: Any, provider: str) -> None:
    """분류표에 없는 코드를 성공으로 흘리면 빈 결과가 조용히 내려간다."""
    with pytest.raises(ProviderResponseError) as exc:
        _adapter(cls)._validate_envelope(_envelope("77", msg="알 수 없음"), "d")
    assert exc.value.provider_code == "77"


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
@pytest.mark.parametrize("code", ["00", "0", "000"])
def test_numerically_zero_codes_are_success(cls: Any, provider: str, code: str) -> None:
    """성공 코드는 문자열 비교가 아니라 숫자 0 판정이다 — '0'/'00'/'000' 이 모두 성공이다."""
    _, items = _adapter(cls)._validate_envelope(_envelope(code, items={"item": [{"a": 1}]}), "d")
    assert items == [{"a": 1}]


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_non_numeric_code_is_not_treated_as_success(cls: Any, provider: str) -> None:
    with pytest.raises(ProviderResponseError):
        _adapter(cls)._validate_envelope(_envelope("OK"), "d")


# --- items 정규화 ----------------------------------------------------------


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_items_absent_yields_no_rows(cls: Any, provider: str) -> None:
    _, items = _adapter(cls)._validate_envelope(_envelope("00"), "d")
    assert items == []


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_single_item_object_is_wrapped_in_a_list(cls: Any, provider: str) -> None:
    """행이 하나면 data.go.kr 이 item 을 dict 로 준다 — 목록으로 정규화해야 한다."""
    _, items = _adapter(cls)._validate_envelope(_envelope("00", items={"item": {"a": 1}}), "d")
    assert items == [{"a": 1}]


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_item_list_drops_non_mapping_entries(cls: Any, provider: str) -> None:
    _, items = _adapter(cls)._validate_envelope(
        _envelope("00", items={"item": [{"a": 1}, "junk", None, {"b": 2}]}), "d"
    )
    assert items == [{"a": 1}, {"b": 2}]


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_items_given_directly_as_a_list(cls: Any, provider: str) -> None:
    _, items = _adapter(cls)._validate_envelope(_envelope("00", items=[{"a": 1}, 5, {"b": 2}]), "d")
    assert items == [{"a": 1}, {"b": 2}]


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
@pytest.mark.parametrize("items", ["text", 7, True])
def test_unusable_items_payload_yields_no_rows(cls: Any, provider: str, items: object) -> None:
    _, parsed = _adapter(cls)._validate_envelope(_envelope("00", items=items), "d")
    assert parsed == []


# --- 카탈로그 조회 ---------------------------------------------------------


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_adapter_reports_its_provider_name(cls: Any, provider: str) -> None:
    assert _adapter(cls).name == provider


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_search_matches_id_and_name_case_insensitively(cls: Any, provider: str) -> None:
    adapter = _adapter(cls)
    catalogue = adapter.list_datasets()
    assert catalogue, "어댑터에 기본 카탈로그가 있어야 한다"

    sample = catalogue[0]
    assert sample in adapter.search_datasets(sample.dataset_key.upper())
    assert sample in adapter.search_datasets(sample.name.casefold())


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_search_with_no_match_returns_empty(cls: Any, provider: str) -> None:
    assert _adapter(cls).search_datasets("존재하지-않는-데이터셋-xyz") == []


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_get_dataset_returns_the_catalogue_entry(cls: Any, provider: str) -> None:
    adapter = _adapter(cls)
    sample = adapter.list_datasets()[0]
    assert adapter.get_dataset(sample.dataset_key) is sample


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_unknown_dataset_key_raises_with_the_qualified_id(cls: Any, provider: str) -> None:
    adapter = _adapter(cls)
    with pytest.raises(DatasetNotFoundError) as exc:
        adapter.get_dataset("no-such-key")
    assert exc.value.dataset_id == f"{provider}.no-such-key"


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_schema_comes_from_catalogue_metadata(cls: Any, provider: str) -> None:
    adapter = _adapter(cls)
    # 메타데이터에 필드 정보가 없으면 None 이어야 한다 — 빈 스키마를 지어내지 않는다.
    assert adapter.get_schema(_ref(provider, base_url="https://api.test/svc")) is None


# --- call_raw --------------------------------------------------------------


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_call_raw_merges_caller_params_and_returns_the_whole_payload(
    cls: Any, provider: str
) -> None:
    payload = _envelope("00", items={"item": [{"a": 1}]})
    adapter = _adapter(cls, _FakeResponse(payload))
    dataset = _ref(provider, base_url="https://api.test/svc", default_operation="getList")

    assert adapter.call_raw(dataset, "getOne", {"pageNo": 2}) == payload

    call = adapter._transport.calls[0]
    assert call["url"] == "https://api.test/svc/getOne"
    assert call["params"]["pageNo"] == "2"
    assert call["params"]["serviceKey"] == "test-key"


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_call_raw_never_lets_a_caller_override_the_service_key(cls: Any, provider: str) -> None:
    """호출자가 serviceKey 를 넘겨도 설정된 키가 이긴다 — 키 주입 경로를 열지 않는다."""
    adapter = _adapter(cls, _FakeResponse(_envelope("00")))
    dataset = _ref(provider, base_url="https://api.test/svc")

    adapter.call_raw(dataset, "getList", {"serviceKey": "attacker-key"})

    assert adapter._transport.calls[0]["params"]["serviceKey"] == "test-key"


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_call_raw_respects_a_renamed_service_key_parameter(cls: Any, provider: str) -> None:
    adapter = _adapter(cls, _FakeResponse(_envelope("00")))
    dataset = _ref(provider, base_url="https://api.test/svc", service_key_param="authKey")

    adapter.call_raw(dataset, "getList", {"authKey": "attacker-key"})

    assert adapter._transport.calls[0]["params"]["authKey"] == "test-key"


@pytest.mark.parametrize(("cls", "provider"), _ADAPTERS)
def test_call_raw_propagates_an_error_envelope(cls: Any, provider: str) -> None:
    """raw 호출이라도 오류 응답을 그대로 돌려주지 않는다 — 호출부가 실패를 못 본다."""
    adapter = _adapter(cls, _FakeResponse(_envelope("30", msg="인증 실패")))
    dataset = _ref(provider, base_url="https://api.test/svc")

    with pytest.raises(AuthError):
        adapter.call_raw(dataset, "getList", {})
