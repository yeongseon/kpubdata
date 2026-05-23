"""테스트 모듈.

이 파일은 ``tests/unit/providers/lofin/test_lofin_adapter.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

import json
import logging
from types import MappingProxyType
from typing import cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.exceptions import ProviderResponseError
from kpubdata.providers.lofin.adapter import LofinAdapter
from kpubdata.transport.http import HttpTransport


class FakeResponse:
    """
    FakeResponse 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/providers/lofin/test_lofin_adapter.py`` 모듈 안에서 FakeResponse의 상태와 동작을 함께 관리한다.
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

    이 클래스는 ``tests/unit/providers/lofin/test_lofin_adapter.py`` 모듈 안에서 FakeTransport의 상태와 동작을 함께 관리한다.
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
        "AJGCF": [
            {
                "head": [
                    {"list_total_count": total_count},
                    {"RESULT": {"CODE": "INFO-000", "MESSAGE": "OK"}},
                ]
            },
            {"row": items},
        ]
    }


def _build_adapter_with_transport(
    responses: list[FakeResponse],
) -> tuple[LofinAdapter, DatasetRef, FakeTransport]:
    """
    내부 헬퍼로서 build adapter with transport 처리를 담당한다.

    매개변수:
        responses (list[FakeResponse]): 호출자가 제공하는 입력 값이다.

    반환값:
        tuple[LofinAdapter, DatasetRef, FakeTransport]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    transport = FakeTransport(responses)
    adapter = LofinAdapter(
        config=KPubDataConfig(provider_keys={"datago": "test-key"}),
        transport=cast(HttpTransport, cast(object, transport)),
    )
    dataset = adapter.get_dataset("expenditure_budget")
    return adapter, dataset, transport


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

    batch = adapter.query_records(dataset, Query(page=1, page_size=2))

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

    _ = adapter.query_records(dataset, Query())

    request_url = cast(str, transport.calls[0]["url"])
    assert "pSize=100" in request_url


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

    batch = adapter.query_records(dataset, Query(page=1, page_size=2))

    assert batch.total_count is None
    assert batch.next_page == 2


# test build request url missing base url logs debug 테스트가 검증하는 시나리오를 설명한다.
def test_build_request_url_missing_base_url_logs_debug(caplog: pytest.LogCaptureFixture) -> None:
    """
    test build request url missing base url logs debug 시나리오를 검증한다.

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
    dataset = DatasetRef(
        id=dataset.id,
        provider=dataset.provider,
        dataset_key=dataset.dataset_key,
        name=dataset.name,
        representation=dataset.representation,
        operations=dataset.operations,
        raw_metadata=MappingProxyType(
            {k: v for k, v in dataset.raw_metadata.items() if k != "base_url"}
        ),
        query_support=dataset.query_support,
    )

    caplog.set_level(logging.DEBUG, logger="kpubdata.provider.lofin")
    with pytest.raises(ProviderResponseError, match="base_url"):
        adapter.query_records(dataset, Query())

    record = next(
        record
        for record in caplog.records
        if record.getMessage() == "LOFIN dataset metadata missing base_url"
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

    caplog.set_level(logging.DEBUG, logger="kpubdata.provider.lofin")
    batch = adapter.query_records(dataset, Query(page=1, page_size=10))

    assert batch.items == []
    record = next(
        record for record in caplog.records if record.getMessage() == "LOFIN envelope: zero items"
    )
    assert record.__dict__["dataset_id"] == dataset.id
    assert record.__dict__["page"] == 1
    assert record.__dict__["page_size"] == 10
    assert record.__dict__["total_count"] == 0


def test_transport_requirements_includes_ssl_context_factory() -> None:
    """LofinAdapter exposes transport_requirements with an SSL context factory."""
    reqs = LofinAdapter.transport_requirements
    assert reqs is not None
    assert reqs.ssl_context_factory is not None

    ctx = reqs.ssl_context_factory()
    import ssl

    assert isinstance(ctx, ssl.SSLContext)


def test_client_applies_lofin_ssl_context() -> None:
    """Client detects LofinAdapter.transport_requirements and builds custom transport."""
    from unittest.mock import patch

    from kpubdata.client import Client
    from kpubdata.transport.http import HttpTransport

    with patch.object(
        HttpTransport, "with_requirements", wraps=HttpTransport.with_requirements
    ) as spy:
        client = Client()
        _ = client.datasets.list()

    assert spy.call_count >= 1
    for call in spy.call_args_list:
        reqs = call[0][1] if len(call[0]) > 1 else call.kwargs.get("requirements")
        if reqs and reqs.ssl_context_factory is not None:
            return
    raise AssertionError(
        "HttpTransport.with_requirements was never called with ssl_context_factory"
    )
