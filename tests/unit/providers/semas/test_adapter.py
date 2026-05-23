"""테스트 모듈.

이 파일은 ``tests/unit/providers/semas/test_adapter.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.exceptions import AuthError, InvalidRequestError
from kpubdata.providers.semas.adapter import SemasAdapter
from kpubdata.transport.http import HttpTransport


def _fixture_path(name: str) -> Path:
    """
    내부 헬퍼로서 fixture path 처리를 담당한다.

    매개변수:
        name (str): 호출자가 제공하는 입력 값이다.

    반환값:
        Path: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    return Path(__file__).resolve().parents[3] / "fixtures" / "semas" / name


def _load_fixture(name: str) -> dict[str, object]:
    """
    내부 헬퍼로서 load fixture 처리를 담당한다.

    매개변수:
        name (str): 호출자가 제공하는 입력 값이다.

    반환값:
        dict[str, object]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    payload = cast(object, json.loads(_fixture_path(name).read_text(encoding="utf-8")))
    if isinstance(payload, dict):
        return cast(dict[str, object], payload)
    raise ValueError(f"Fixture must be object: {name}")


class FakeResponse:
    """
    FakeResponse 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/providers/semas/test_adapter.py`` 모듈 안에서 FakeResponse의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    def __init__(self, payload: dict[str, object]) -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        매개변수:
            payload (dict[str, object]): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self.headers: dict[str, str] = {"content-type": "application/json"}
        self.text: str = json.dumps(payload)
        self.content: bytes = self.text.encode()


class FakeTransport:
    """
    FakeTransport 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/providers/semas/test_adapter.py`` 모듈 안에서 FakeTransport의 상태와 동작을 함께 관리한다.
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
        self._responses: list[FakeResponse] = list(responses)
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
        return self._responses.pop(0)


def _build_adapter_with_transport(
    dataset_key: str,
    responses: list[FakeResponse],
) -> tuple[SemasAdapter, DatasetRef, FakeTransport]:
    """
    내부 헬퍼로서 build adapter with transport 처리를 담당한다.

    매개변수:
        dataset_key (str): 호출자가 제공하는 입력 값이다.
        responses (list[FakeResponse]): 호출자가 제공하는 입력 값이다.

    반환값:
        tuple[SemasAdapter, DatasetRef, FakeTransport]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    transport = FakeTransport(responses)
    adapter = SemasAdapter(
        config=KPubDataConfig(provider_keys={"datago": "test-key"}),
        transport=cast(HttpTransport, cast(object, transport)),
    )
    dataset = adapter.get_dataset(dataset_key)
    return adapter, dataset, transport


# test query records parses zone success fixture 테스트가 검증하는 시나리오를 설명한다.
def test_query_records_parses_zone_success_fixture() -> None:
    """
    test query records parses zone success fixture 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    payload = _load_fixture("zone_one_success.json")
    adapter, dataset, transport = _build_adapter_with_transport("zone_one", [FakeResponse(payload)])

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert batch.total_count == 2
    assert batch.next_page is None
    assert batch.raw == payload
    assert batch.items[0]["mainTrarNm"] == "강남역 상권"
    assert len(transport.calls) == 1


# test query records parses store success fixture 테스트가 검증하는 시나리오를 설명한다.
def test_query_records_parses_store_success_fixture() -> None:
    """
    test query records parses store success fixture 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    payload = _load_fixture("store_one_success.json")
    adapter, dataset, _ = _build_adapter_with_transport("store_one", [FakeResponse(payload)])

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 3
    assert batch.total_count == 3
    assert batch.items[0]["bizesNm"] == "테스트카페"


# test query records parses upjong success fixture 테스트가 검증하는 시나리오를 설명한다.
def test_query_records_parses_upjong_success_fixture() -> None:
    """
    test query records parses upjong success fixture 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    payload = _load_fixture("upjong_large_success.json")
    adapter, dataset, _ = _build_adapter_with_transport("upjong_large", [FakeResponse(payload)])

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 3
    assert batch.items[1]["indsLclsNm"] == "음식"


# test query records sets next page with total count 테스트가 검증하는 시나리오를 설명한다.
def test_query_records_sets_next_page_with_total_count() -> None:
    """
    test query records sets next page with total count 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    payload = _load_fixture("store_one_success.json")
    adapter, dataset, _ = _build_adapter_with_transport("store_one", [FakeResponse(payload)])

    batch = adapter.query_records(dataset, Query(page=1, page_size=2))

    assert batch.total_count == 3
    assert batch.next_page == 2


# test query records passes filters 테스트가 검증하는 시나리오를 설명한다.
def test_query_records_passes_filters() -> None:
    """
    test query records passes filters 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    payload = _load_fixture("store_one_success.json")
    adapter, dataset, transport = _build_adapter_with_transport(
        "store_radius", [FakeResponse(payload)]
    )

    _ = adapter.query_records(dataset, Query(filters={"radius": "250", "cx": "127.0"}))

    request_params = cast(dict[str, str], transport.calls[0]["params"])
    assert request_params["serviceKey"] == "test-key"
    assert request_params["type"] == "json"
    assert request_params["pageNo"] == "1"
    assert request_params["numOfRows"] == "100"
    assert request_params["radius"] == "250"
    assert request_params["cx"] == "127.0"


# test call raw returns payload and uses requested operation 테스트가 검증하는 시나리오를 설명한다.
def test_call_raw_returns_payload_and_uses_requested_operation() -> None:
    """
    test call raw returns payload and uses requested operation 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    payload = _load_fixture("zone_one_success.json")
    adapter, dataset, transport = _build_adapter_with_transport("zone_one", [FakeResponse(payload)])

    raw = adapter.call_raw(
        dataset,
        "storeZoneInRadius",
        {"radius": "250", "serviceKey": "ignored-user-key"},
    )

    request_params = cast(dict[str, str], transport.calls[0]["params"])
    assert raw == payload
    assert cast(str, transport.calls[0]["url"]).endswith("/storeZoneInRadius")
    assert request_params["serviceKey"] == "test-key"
    assert request_params["type"] == "json"
    assert request_params["radius"] == "250"


# test query records handles empty response 테스트가 검증하는 시나리오를 설명한다.
def test_query_records_handles_empty_response() -> None:
    """
    test query records handles empty response 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    payload = _load_fixture("empty_response.json")
    adapter, dataset, _ = _build_adapter_with_transport("store_one", [FakeResponse(payload)])

    batch = adapter.query_records(dataset, Query())

    assert batch.items == []
    assert batch.total_count is None
    assert batch.next_page is None


# test query records raises auth error on auth fixture 테스트가 검증하는 시나리오를 설명한다.
def test_query_records_raises_auth_error_on_auth_fixture() -> None:
    """
    test query records raises auth error on auth fixture 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    payload = _load_fixture("error_auth.json")
    adapter, dataset, _ = _build_adapter_with_transport("store_one", [FakeResponse(payload)])

    with pytest.raises(AuthError, match="SERVICE KEY") as exc_info:
        _ = adapter.query_records(dataset, Query())

    assert exc_info.value.provider_code == "30"


# test query records raises invalid request error 테스트가 검증하는 시나리오를 설명한다.
def test_query_records_raises_invalid_request_error() -> None:
    """
    test query records raises invalid request error 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    payload = _load_fixture("error_invalid_request.json")
    adapter, dataset, _ = _build_adapter_with_transport("store_one", [FakeResponse(payload)])

    with pytest.raises(InvalidRequestError, match="INVALID REQUEST") as exc_info:
        _ = adapter.query_records(dataset, Query())

    assert exc_info.value.provider_code == "10"


# test adapter lists all datasets 테스트가 검증하는 시나리오를 설명한다.
def test_adapter_lists_all_datasets() -> None:
    """
    test adapter lists all datasets 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = SemasAdapter(config=KPubDataConfig(provider_keys={"datago": "test-key"}))

    datasets = adapter.list_datasets()

    assert len(datasets) == 17
    assert [dataset.dataset_key for dataset in datasets] == [
        "zone_one",
        "zone_radius",
        "zone_rect",
        "zone_admi",
        "store_one",
        "store_building",
        "store_pnu",
        "store_dong",
        "store_area",
        "store_radius",
        "store_rect",
        "store_polygon",
        "store_upjong",
        "store_date",
        "upjong_large",
        "upjong_middle",
        "upjong_small",
    ]


# test get schema returns catalogue schema 테스트가 검증하는 시나리오를 설명한다.
def test_get_schema_returns_catalogue_schema() -> None:
    """
    test get schema returns catalogue schema 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = SemasAdapter(config=KPubDataConfig(provider_keys={"datago": "test-key"}))
    dataset = adapter.get_dataset("store_one")

    schema = adapter.get_schema(dataset)

    assert schema is not None
    assert schema.fields[0].name == "bizesId"
    assert schema.fields[-1].name == "lat"
    assert len(schema.fields) == 39
