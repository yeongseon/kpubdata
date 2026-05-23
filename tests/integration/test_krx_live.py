"""테스트 모듈.

이 파일은 ``tests/integration/test_krx_live.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

import os

import pytest

from kpubdata.client import Client
from kpubdata.core.models import RecordBatch


@pytest.fixture(scope="module")
def require_krx_integration() -> None:
    """
    require krx integration 동작을 수행한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    if os.environ.get("KPUBDATA_KRX_INTEGRATION") != "1":
        pytest.skip("Set KPUBDATA_KRX_INTEGRATION=1 to run live KRX integration tests")


@pytest.fixture(scope="module")
def krx_client(require_krx_integration: None) -> Client:
    """
    krx client 동작을 수행한다.

    매개변수:
        require_krx_integration (None): 호출자가 제공하는 입력 값이다.

    반환값:
        Client: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    return Client()


# test kospi index live returns rows 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_kospi_index_live_returns_rows(krx_client: Client) -> None:
    """
    test kospi index live returns rows 시나리오를 검증한다.

    매개변수:
        krx_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    dataset = krx_client.dataset("krx.kospi_index")

    result = dataset.list(start_date="20240102", end_date="20240108")

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0


# test investor flow live returns rows 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_investor_flow_live_returns_rows(krx_client: Client) -> None:
    """
    test investor flow live returns rows 시나리오를 검증한다.

    매개변수:
        krx_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    dataset = krx_client.dataset("krx.investor_flow")

    result = dataset.list(start_date="20240102", end_date="20240108")

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0


# test market valuation live returns rows 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_market_valuation_live_returns_rows(krx_client: Client) -> None:
    """
    test market valuation live returns rows 시나리오를 검증한다.

    매개변수:
        krx_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    dataset = krx_client.dataset("krx.market_valuation")

    result = dataset.list(start_date="20240102", end_date="20240108")

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0
