"""테스트 모듈.

이 파일은 ``tests/unit/providers/datago/test_adapter_coverage.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.core.representation import Representation
from kpubdata.exceptions import ConfigError, ParseError, ProviderResponseError
from kpubdata.providers._common import build_dataset_ref, coerce_int, require_string_field
from kpubdata.providers.datago.adapter import DataGoAdapter
from kpubdata.transport.http import HttpTransport


class FakeResponse:
    """
    FakeResponse 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/providers/datago/test_adapter_coverage.py`` 모듈 안에서 FakeResponse의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    def __init__(self, data: bytes, content_type: str = "application/json") -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        매개변수:
            data (bytes): 호출자가 제공하는 입력 값이다.
            content_type (str): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self.headers: dict[str, str] = {"content-type": content_type}
        self.content: bytes = data
        self.text: str = data.decode("utf-8")


class FakeTransport:
    """
    FakeTransport 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/providers/datago/test_adapter_coverage.py`` 모듈 안에서 FakeTransport의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__, request.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    def __init__(self, responses: list[FakeResponse]) -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        매개변수:
            responses (list[FakeResponse]): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self._responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> FakeResponse:
        """
        request 동작을 수행한다.

        매개변수:
            method (str): 호출자가 제공하는 입력 값이다.
            url (str): 호출자가 제공하는 입력 값이다.
            **kwargs (object): 호출자가 제공하는 입력 값이다.

        반환값:
            FakeResponse: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self.calls.append({"method": method, "url": url, **kwargs})
        if not self._responses:
            raise AssertionError("No responses queued")
        return self._responses.pop(0)


def _dataset(raw_metadata: dict[str, object]) -> DatasetRef:
    """
    내부 헬퍼로서 dataset 처리를 담당한다.

    매개변수:
        raw_metadata (dict[str, object]): 호출자가 제공하는 입력 값이다.

    반환값:
        DatasetRef: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    return DatasetRef(
        id="datago.test",
        provider="datago",
        dataset_key="test",
        name="Test Dataset",
        representation=Representation.API_JSON,
        operations=frozenset(),
        raw_metadata=MappingProxyType(raw_metadata),
    )


def _adapter(
    transport: FakeTransport,
    dataset: DatasetRef,
) -> DataGoAdapter:
    """
    내부 헬퍼로서 adapter 처리를 담당한다.

    매개변수:
        transport (FakeTransport): 호출자가 제공하는 입력 값이다.
        dataset (DatasetRef): 호출자가 제공하는 입력 값이다.

    반환값:
        DataGoAdapter: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    return DataGoAdapter(
        config=KPubDataConfig(provider_keys={"datago": "test-key"}),
        transport=cast(HttpTransport, cast(object, transport)),
        catalogue=[dataset],
    )


def _ok_payload(*, items: object, total_count: object, num_of_rows: object) -> dict[str, object]:
    """
    내부 헬퍼로서 ok payload 처리를 담당한다.

    매개변수:
        items (object): 호출자가 제공하는 입력 값이다.
        total_count (object): 호출자가 제공하는 입력 값이다.
        num_of_rows (object): 호출자가 제공하는 입력 값이다.

    반환값:
        dict[str, object]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    return {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
            "body": {
                "items": {"item": items},
                "totalCount": total_count,
                "numOfRows": num_of_rows,
                "pageNo": 1,
            },
        }
    }


# test name property returns datago 테스트가 검증하는 시나리오를 설명한다.
def test_name_property_returns_datago() -> None:
    """
    test name property returns datago 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    assert DataGoAdapter(catalogue=[]).name == "datago"


# test query records sets next page for full page with remaining total 테스트가 검증하는 시나리오를 설명한다.
def test_query_records_sets_next_page_for_full_page_with_remaining_total(monkeypatch) -> None:
    """
    test query records sets next page for full page with remaining total 시나리오를 검증한다.

    매개변수:
        monkeypatch (object): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    import kpubdata.providers.datago.adapter as adapter_module

    payload = _ok_payload(items=[{"id": 1}, {"id": 2}], total_count=5, num_of_rows=2)
    transport = FakeTransport([FakeResponse(b"{}")])
    dataset = _dataset({"base_url": "https://example.test", "default_operation": "list"})
    adapter = _adapter(transport, dataset)

    monkeypatch.setattr(adapter_module, "detect_content_type", lambda _resp: "json")
    monkeypatch.setattr(adapter_module, "decode_json", lambda _content: payload)

    batch = adapter.query_records(dataset, Query(page_size=2))

    assert len(transport.calls) == 1
    assert batch.next_page == 2


# test query records stops when page size times page reaches total 테스트가 검증하는 시나리오를 설명한다.
def test_query_records_stops_when_page_size_times_page_reaches_total(monkeypatch) -> None:
    """
    test query records stops when page size times page reaches total 시나리오를 검증한다.

    매개변수:
        monkeypatch (object): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    import kpubdata.providers.datago.adapter as adapter_module

    payload = _ok_payload(items=[{"id": 1}, {"id": 2}], total_count=2, num_of_rows=2)
    transport = FakeTransport([FakeResponse(b"{}")])
    dataset = _dataset({"base_url": "https://example.test", "default_operation": "list"})
    adapter = _adapter(transport, dataset)

    monkeypatch.setattr(adapter_module, "detect_content_type", lambda _resp: "json")
    monkeypatch.setattr(adapter_module, "decode_json", lambda _content: payload)

    batch = adapter.query_records(dataset, Query(page_size=2))

    assert len(transport.calls) == 1
    assert batch.next_page is None


# test get schema returns none when all fields are filtered out 테스트가 검증하는 시나리오를 설명한다.
def test_get_schema_returns_none_when_all_fields_are_filtered_out() -> None:
    """
    test get schema returns none when all fields are filtered out 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    dataset = _dataset(
        {
            "base_url": "https://example.test",
            "fields": [{"title": "no-name"}, {"name": ""}, {"name": None}],
        }
    )
    adapter = DataGoAdapter(catalogue=[dataset])

    assert adapter.get_schema(dataset) is None


# test build request url raises when base url missing 테스트가 검증하는 시나리오를 설명한다.
def test_build_request_url_raises_when_base_url_missing() -> None:
    """
    test build request url raises when base url missing 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = DataGoAdapter(catalogue=[])
    with pytest.raises(ProviderResponseError, match="missing base_url"):
        _ = adapter._build_request_url(_dataset({}))


# test build request url returns base url when operation missing 테스트가 검증하는 시나리오를 설명한다.
def test_build_request_url_returns_base_url_when_operation_missing() -> None:
    """
    test build request url returns base url when operation missing 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = DataGoAdapter(catalogue=[])
    dataset = _dataset({"base_url": "https://example.test/api"})

    assert adapter._build_request_url(dataset) == "https://example.test/api"


# test request and decode falls back to json for unknown content type 테스트가 검증하는 시나리오를 설명한다.
def test_request_and_decode_falls_back_to_json_for_unknown_content_type(monkeypatch) -> None:
    """
    test request and decode falls back to json for unknown content type 시나리오를 검증한다.

    매개변수:
        monkeypatch (object): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    import kpubdata.providers.datago.adapter as adapter_module

    transport = FakeTransport([FakeResponse(b"ignored")])
    adapter = DataGoAdapter(
        config=KPubDataConfig(provider_keys={"datago": "test-key"}),
        transport=cast(HttpTransport, cast(object, transport)),
        catalogue=[],
    )

    called = {"decode_json": False}

    monkeypatch.setattr(adapter_module, "detect_content_type", lambda _resp: "unknown")

    def _decode_json(_content: bytes) -> dict[str, object]:
        """
        내부 헬퍼로서 decode json 처리를 담당한다.

        매개변수:
            _content (bytes): 호출자가 제공하는 입력 값이다.

        반환값:
            dict[str, object]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        called["decode_json"] = True
        return {"response": {}}

    monkeypatch.setattr(adapter_module, "decode_json", _decode_json)

    decoded = adapter._request_and_decode("https://example.test", {"a": "1"})
    assert called["decode_json"] is True
    assert decoded == {"response": {}}


# test request and decode raises parse error when decoded payload not object 테스트가 검증하는 시나리오를 설명한다.
def test_request_and_decode_raises_parse_error_when_decoded_payload_not_object(monkeypatch) -> None:
    """
    test request and decode raises parse error when decoded payload not object 시나리오를 검증한다.

    매개변수:
        monkeypatch (object): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    import kpubdata.providers.datago.adapter as adapter_module

    transport = FakeTransport([FakeResponse(b"[]")])
    adapter = DataGoAdapter(
        config=KPubDataConfig(provider_keys={"datago": "test-key"}),
        transport=cast(HttpTransport, cast(object, transport)),
        catalogue=[],
    )

    monkeypatch.setattr(adapter_module, "detect_content_type", lambda _resp: "json")
    monkeypatch.setattr(adapter_module, "decode_json", lambda _content: [{"x": 1}])

    with pytest.raises(ParseError, match="not an object"):
        _ = adapter._request_and_decode("https://example.test", {})


# test request and decode raises parse error when decode fails 테스트가 검증하는 시나리오를 설명한다.
def test_request_and_decode_raises_parse_error_when_decode_fails(monkeypatch) -> None:
    """
    test request and decode raises parse error when decode fails 시나리오를 검증한다.

    매개변수:
        monkeypatch (object): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    import kpubdata.providers.datago.adapter as adapter_module

    transport = FakeTransport([FakeResponse(b"invalid")])
    adapter = DataGoAdapter(
        config=KPubDataConfig(provider_keys={"datago": "test-key"}),
        transport=cast(HttpTransport, cast(object, transport)),
        catalogue=[],
    )

    monkeypatch.setattr(adapter_module, "detect_content_type", lambda _resp: "unknown")

    def _raises_parse_error(_content: bytes) -> dict[str, object]:
        """
        내부 헬퍼로서 raises parse error 처리를 담당한다.

        매개변수:
            _content (bytes): 호출자가 제공하는 입력 값이다.

        반환값:
            dict[str, object]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        raise ParseError("bad payload")

    monkeypatch.setattr(adapter_module, "decode_json", _raises_parse_error)

    with pytest.raises(ParseError, match="bad payload"):
        _ = adapter._request_and_decode("https://example.test", {})


# test validate envelope raises when response missing 테스트가 검증하는 시나리오를 설명한다.
def test_validate_envelope_raises_when_response_missing() -> None:
    """
    test validate envelope raises when response missing 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = DataGoAdapter(catalogue=[])

    with pytest.raises(ProviderResponseError, match="missing response"):
        _ = adapter._validate_envelope({})


# test validate envelope raises when header missing 테스트가 검증하는 시나리오를 설명한다.
def test_validate_envelope_raises_when_header_missing() -> None:
    """
    test validate envelope raises when header missing 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = DataGoAdapter(catalogue=[])

    with pytest.raises(ProviderResponseError, match="missing header"):
        _ = adapter._validate_envelope({"response": {"body": {}}})


# test validate envelope raises when result code not string 테스트가 검증하는 시나리오를 설명한다.
def test_validate_envelope_raises_when_result_code_not_string() -> None:
    """
    test validate envelope raises when result code not string 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = DataGoAdapter(catalogue=[])

    with pytest.raises(ProviderResponseError, match="missing resultCode"):
        _ = adapter._validate_envelope({"response": {"header": {"resultCode": 0}, "body": {}}})


# test raise for result code unknown code raises provider response error 테스트가 검증하는 시나리오를 설명한다.
def test_raise_for_result_code_unknown_code_raises_provider_response_error() -> None:
    """
    test raise for result code unknown code raises provider response error 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = DataGoAdapter(catalogue=[])

    with pytest.raises(ProviderResponseError):
        adapter._raise_for_result_code("99", "unknown code", "datago.test")


# test normalize items accepts direct list wrapper 테스트가 검증하는 시나리오를 설명한다.
def test_normalize_items_accepts_direct_list_wrapper() -> None:
    """
    test normalize items accepts direct list wrapper 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = DataGoAdapter(catalogue=[])

    normalized = adapter._normalize_items([{"id": 1}, "x", {"id": 2}])

    assert normalized == [{"id": 1}, {"id": 2}]


# test normalize items returns empty for unsupported wrapper 테스트가 검증하는 시나리오를 설명한다.
def test_normalize_items_returns_empty_for_unsupported_wrapper() -> None:
    """
    test normalize items returns empty for unsupported wrapper 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = DataGoAdapter(catalogue=[])
    assert adapter._normalize_items("not-a-list-or-dict") == []


# test coerce int returns default for non numeric string 테스트가 검증하는 시나리오를 설명한다.
def test_coerce_int_returns_default_for_non_numeric_string() -> None:
    """
    test coerce int returns default for non numeric string 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    assert coerce_int("not-a-number", 7) == 7


# test coerce int returns default for non string non int 테스트가 검증하는 시나리오를 설명한다.
def test_coerce_int_returns_default_for_non_string_non_int() -> None:
    """
    test coerce int returns default for non string non int 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    assert coerce_int(3.14, 11) == 11


class _FakeCatalogueFile:
    """
    _FakeCatalogueFile 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/providers/datago/test_adapter_coverage.py`` 모듈 안에서 _FakeCatalogueFile의 상태와 동작을 함께 관리한다.
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
        self._text = text

    def read_text(self, encoding: str = "utf-8") -> str:
        """
        read text 동작을 수행한다.

        매개변수:
            encoding (str): 호출자가 제공하는 입력 값이다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        del encoding
        return self._text


class _FakePackageFiles:
    """
    _FakePackageFiles 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/providers/datago/test_adapter_coverage.py`` 모듈 안에서 _FakePackageFiles의 상태와 동작을 함께 관리한다.
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
        self._text = text

    def joinpath(self, _name: str) -> _FakeCatalogueFile:
        """
        joinpath 동작을 수행한다.

        매개변수:
            _name (str): 호출자가 제공하는 입력 값이다.

        반환값:
            _FakeCatalogueFile: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return _FakeCatalogueFile(self._text)


# test load default catalogue raises when top level json not list 테스트가 검증하는 시나리오를 설명한다.
def test_load_default_catalogue_raises_when_top_level_json_not_list(monkeypatch) -> None:
    """
    test load default catalogue raises when top level json not list 시나리오를 검증한다.

    매개변수:
        monkeypatch (object): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    import kpubdata.providers._common as common_module

    monkeypatch.setattr(common_module, "files", lambda _pkg: _FakePackageFiles("{}"))

    with pytest.raises(ConfigError, match="top-level JSON array"):
        _ = DataGoAdapter._load_default_catalogue()


# test load default catalogue raises when entry not dict 테스트가 검증하는 시나리오를 설명한다.
def test_load_default_catalogue_raises_when_entry_not_dict(monkeypatch) -> None:
    """
    test load default catalogue raises when entry not dict 시나리오를 검증한다.

    매개변수:
        monkeypatch (object): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    import kpubdata.providers._common as common_module

    monkeypatch.setattr(common_module, "files", lambda _pkg: _FakePackageFiles("[1]"))

    with pytest.raises(ConfigError, match="entries must be JSON objects"):
        _ = DataGoAdapter._load_default_catalogue()


# test load default catalogue raises when entry key not string 테스트가 검증하는 시나리오를 설명한다.
def test_load_default_catalogue_raises_when_entry_key_not_string(monkeypatch) -> None:
    """
    test load default catalogue raises when entry key not string 시나리오를 검증한다.

    매개변수:
        monkeypatch (object): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    import kpubdata.providers._common as common_module

    monkeypatch.setattr(common_module, "files", lambda _pkg: _FakePackageFiles("[]"))
    monkeypatch.setattr(common_module.json, "loads", lambda _text: [{1: "bad-key"}])

    with pytest.raises(ConfigError, match="entry keys must be strings"):
        _ = DataGoAdapter._load_default_catalogue()


# test build dataset ref parses string max page size 테스트가 검증하는 시나리오를 설명한다.
def test_build_dataset_ref_parses_string_max_page_size() -> None:
    """
    test build dataset ref parses string max page size 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    dataset = build_dataset_ref(
        "datago",
        {
            "dataset_key": "test",
            "name": "Test",
            "representation": "api_json",
            "query_support": {"pagination": "offset", "max_page_size": "250"},
            "base_url": "https://example.test",
        },
    )

    assert dataset.query_support is not None
    assert dataset.query_support.max_page_size == 250


# test build dataset ref raises for invalid max page size type 테스트가 검증하는 시나리오를 설명한다.
def test_build_dataset_ref_raises_for_invalid_max_page_size_type() -> None:
    """
    test build dataset ref raises for invalid max page size type 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    with pytest.raises(ConfigError, match="max_page_size must be int-like"):
        _ = build_dataset_ref(
            "datago",
            {
                "dataset_key": "test",
                "name": "Test",
                "representation": "api_json",
                "query_support": {"pagination": "offset", "max_page_size": {}},
            },
        )


# test require string field raises when field missing 테스트가 검증하는 시나리오를 설명한다.
def test_require_string_field_raises_when_field_missing() -> None:
    """
    test require string field raises when field missing 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    with pytest.raises(ConfigError, match="missing non-empty string field"):
        _ = require_string_field({}, "dataset_key", "datago")
