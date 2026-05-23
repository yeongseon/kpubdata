"""테스트 모듈.

이 파일은 ``tests/unit/providers/bok/test_bok_adapter.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

import json
import logging
from importlib.resources import files
from typing import cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.exceptions import InvalidRequestError
from kpubdata.providers.bok.adapter import BokAdapter
from kpubdata.transport.http import HttpTransport


class FakeResponse:
    """
    FakeResponse 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/providers/bok/test_bok_adapter.py`` 모듈 안에서 FakeResponse의 상태와 동작을 함께 관리한다.
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

    이 클래스는 ``tests/unit/providers/bok/test_bok_adapter.py`` 모듈 안에서 FakeTransport의 상태와 동작을 함께 관리한다.
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


def _success_payload(*, items: object, total_count: object) -> dict[str, object]:
    """
    내부 헬퍼로서 success payload 처리를 담당한다.

    매개변수:
        items (object): 호출자가 제공하는 입력 값이다.
        total_count (object): 호출자가 제공하는 입력 값이다.

    반환값:
        dict[str, object]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    return {
        "StatisticSearch": {
            "list_total_count": total_count,
            "row": items,
        }
    }


def _build_adapter_with_transport(
    responses: list[FakeResponse], *, dataset_key: str = "base_rate"
) -> tuple[BokAdapter, DatasetRef, FakeTransport]:
    """
    내부 헬퍼로서 build adapter with transport 처리를 담당한다.

    매개변수:
        responses (list[FakeResponse]): 호출자가 제공하는 입력 값이다.
        dataset_key (str): 호출자가 제공하는 입력 값이다.

    반환값:
        tuple[BokAdapter, DatasetRef, FakeTransport]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    transport = FakeTransport(responses)
    adapter = BokAdapter(
        config=KPubDataConfig(provider_keys={"bok": "test-key"}),
        transport=cast(HttpTransport, cast(object, transport)),
    )
    dataset = adapter.get_dataset(dataset_key)
    return adapter, dataset, transport


# test catalogue includes usd krw daily dataset 테스트가 검증하는 시나리오를 설명한다.
def test_catalogue_includes_usd_krw_daily_dataset() -> None:
    """
    test catalogue includes usd krw daily dataset 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    _, dataset, _ = _build_adapter_with_transport([], dataset_key="usd_krw")
    catalogue = cast(
        list[dict[str, object]],
        json.loads(files("kpubdata.providers.bok").joinpath("catalogue.json").read_text()),
    )
    usd_krw_entry = next(entry for entry in catalogue if entry["dataset_key"] == "usd_krw")

    assert dataset.id == "bok.usd_krw"
    assert dataset.name == "원/달러 환율 매매기준율 (USD/KRW Exchange Rate)"
    assert dataset.description == "Bank of Korea ECOS USD/KRW exchange rate historical data"
    assert dataset.raw_metadata["stat_code"] == "731Y003"
    assert dataset.raw_metadata["item_code1"] == "0000003"
    assert dataset.tags == ("finance", "exchange-rate", "fx")
    assert dataset.query_support is not None
    assert dataset.query_support.pagination.value == "offset"
    assert dataset.query_support.max_page_size == 1000
    assert usd_krw_entry["query_support"] == {
        "pagination": "offset",
        "max_page_size": 1000,
        "frequency": ["D"],
    }
    raw_fields = cast(list[dict[str, object]], dataset.raw_metadata["fields"])
    assert [field["name"] for field in raw_fields] == [
        "TIME",
        "DATA_VALUE",
        "UNIT_NAME",
        "STAT_CODE",
        "ITEM_CODE1",
        "ITEM_NAME1",
    ]


# test catalogue includes bond yield 3y daily dataset 테스트가 검증하는 시나리오를 설명한다.
def test_catalogue_includes_bond_yield_3y_daily_dataset() -> None:
    """
    test catalogue includes bond yield 3y daily dataset 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    _, dataset, _ = _build_adapter_with_transport([], dataset_key="bond_yield_3y")
    catalogue = cast(
        list[dict[str, object]],
        json.loads(files("kpubdata.providers.bok").joinpath("catalogue.json").read_text()),
    )
    bond_yield_3y_entry = next(
        entry for entry in catalogue if entry["dataset_key"] == "bond_yield_3y"
    )

    assert dataset.id == "bok.bond_yield_3y"
    assert dataset.name == "국고채 3년물 수익률 (Korea Treasury Bond 3Y Yield)"
    assert dataset.description == "Bank of Korea ECOS Korea Treasury Bond 3Y yield historical data"
    assert dataset.raw_metadata["stat_code"] == "817Y002"
    assert dataset.raw_metadata["item_code1"] == "010200000"
    assert dataset.tags == ("finance", "interest-rate", "bond", "treasury")
    assert dataset.query_support is not None
    assert dataset.query_support.pagination.value == "offset"
    assert dataset.query_support.max_page_size == 1000
    assert bond_yield_3y_entry["query_support"] == {
        "pagination": "offset",
        "max_page_size": 1000,
        "frequency": ["D"],
    }
    raw_fields = cast(list[dict[str, object]], dataset.raw_metadata["fields"])
    assert [field["name"] for field in raw_fields] == [
        "TIME",
        "DATA_VALUE",
        "UNIT_NAME",
        "STAT_CODE",
        "ITEM_CODE1",
        "ITEM_NAME1",
    ]


# test catalogue includes money supply monthly dataset 테스트가 검증하는 시나리오를 설명한다.
def test_catalogue_includes_money_supply_monthly_dataset() -> None:
    """
    test catalogue includes money supply monthly dataset 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    _, dataset, _ = _build_adapter_with_transport([], dataset_key="money_supply")
    catalogue = cast(
        list[dict[str, object]],
        json.loads(files("kpubdata.providers.bok").joinpath("catalogue.json").read_text()),
    )
    money_supply_entry = next(
        entry for entry in catalogue if entry["dataset_key"] == "money_supply"
    )

    assert dataset.id == "bok.money_supply"
    assert dataset.name == "통화량(M2) 구 통계 (Money Supply M2, Legacy Series)"
    assert (
        dataset.description
        == "Bank of Korea ECOS M2 money supply monthly data (legacy series, 198601-200409)"
    )
    assert dataset.raw_metadata["stat_code"] == "101Y003"
    assert dataset.raw_metadata["item_code1"] == "BBHS00"
    assert dataset.tags == ("finance", "money-supply", "monetary-aggregate")
    assert dataset.query_support is not None
    assert dataset.query_support.pagination.value == "offset"
    assert dataset.query_support.max_page_size == 1000
    assert money_supply_entry["query_support"] == {
        "pagination": "offset",
        "max_page_size": 1000,
        "frequency": ["M"],
    }
    raw_fields = cast(list[dict[str, object]], dataset.raw_metadata["fields"])
    assert [field["name"] for field in raw_fields] == [
        "TIME",
        "DATA_VALUE",
        "UNIT_NAME",
        "STAT_CODE",
        "ITEM_CODE1",
        "ITEM_NAME1",
    ]


# test query records returns single page and sets next page 테스트가 검증하는 시나리오를 설명한다.
def test_query_records_returns_single_page_and_sets_next_page() -> None:
    """
    test query records returns single page and sets next page 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    payload = _success_payload(items=[{"id": 1}, {"id": 2}], total_count=5)
    adapter, dataset, transport = _build_adapter_with_transport([FakeResponse(payload)])

    batch = adapter.query_records(
        dataset,
        Query(page=1, page_size=2, start_date="202401", end_date="202403"),
    )

    assert batch.items == [{"id": 1}, {"id": 2}]
    assert batch.total_count == 5
    assert batch.next_page == 2
    assert batch.raw == payload
    assert len(transport.calls) == 1


# test query records uses default page size 100 테스트가 검증하는 시나리오를 설명한다.
def test_query_records_uses_default_page_size_100() -> None:
    """
    test query records uses default page size 100 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    payload = _success_payload(items=[{"id": 1}], total_count=1)
    adapter, dataset, transport = _build_adapter_with_transport([FakeResponse(payload)])

    _batch = adapter.query_records(dataset, Query(start_date="202401", end_date="202403"))

    request_url = cast(str, transport.calls[0]["url"])
    assert "/1/100/" in request_url


# test query records uses heuristic next page without total count 테스트가 검증하는 시나리오를 설명한다.
def test_query_records_uses_heuristic_next_page_without_total_count() -> None:
    """
    test query records uses heuristic next page without total count 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    payload = _success_payload(items=[{"id": 1}, {"id": 2}], total_count=None)
    adapter, dataset, _ = _build_adapter_with_transport([FakeResponse(payload)])

    batch = adapter.query_records(
        dataset,
        Query(page=1, page_size=2, start_date="202401", end_date="202403"),
    )

    assert batch.total_count is None
    assert batch.next_page == 2


# test query records missing dates logs debug 테스트가 검증하는 시나리오를 설명한다.
def test_query_records_missing_dates_logs_debug(caplog: pytest.LogCaptureFixture) -> None:
    """
    test query records missing dates logs debug 시나리오를 검증한다.

    매개변수:
        caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset, _ = _build_adapter_with_transport([])

    caplog.set_level(logging.DEBUG, logger="kpubdata.provider.bok")
    with pytest.raises(InvalidRequestError, match="start_date and end_date"):
        _ = adapter.query_records(dataset, Query())

    record = next(
        record
        for record in caplog.records
        if record.getMessage() == "BOK ECOS invalid query: missing start/end date"
    )
    assert record.__dict__["dataset_id"] == dataset.id


# test query records zero items logs debug 테스트가 검증하는 시나리오를 설명한다.
def test_query_records_zero_items_logs_debug(caplog: pytest.LogCaptureFixture) -> None:
    """
    test query records zero items logs debug 시나리오를 검증한다.

    매개변수:
        caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    payload = _success_payload(items=[], total_count=0)
    adapter, dataset, _ = _build_adapter_with_transport([FakeResponse(payload)])

    caplog.set_level(logging.DEBUG, logger="kpubdata.provider.bok")
    batch = adapter.query_records(
        dataset,
        Query(page=1, page_size=10, start_date="202401", end_date="202403"),
    )

    assert batch.items == []
    record = next(
        record for record in caplog.records if record.getMessage() == "BOK envelope: zero items"
    )
    assert record.__dict__["dataset_id"] == dataset.id
    assert record.__dict__["page"] == 1
    assert record.__dict__["page_size"] == 10
    assert record.__dict__["total_count"] == 0
