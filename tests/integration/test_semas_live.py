"""테스트 모듈.

이 파일은 ``tests/integration/test_semas_live.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

import pytest

from kpubdata.client import Client
from kpubdata.core.models import RecordBatch


# test store radius returns record batch 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
@pytest.mark.usefixtures("require_semas_key")
def test_store_radius_returns_record_batch(live_client: Client) -> None:
    """
    test store radius returns record batch 시나리오를 검증한다.

    매개변수:
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    ds = live_client.dataset("semas.store_radius")

    result = ds.list(cx="127.02758", cy="37.49794", radius="500")

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0
    assert isinstance(result.items[0], dict)


# test store radius raw returns envelope 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
@pytest.mark.usefixtures("require_semas_key")
def test_store_radius_raw_returns_envelope(live_client: Client) -> None:
    """
    test store radius raw returns envelope 시나리오를 검증한다.

    매개변수:
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    ds = live_client.dataset("semas.store_radius")

    raw = ds.call_raw("storeListInRadius", cx="127.02758", cy="37.49794", radius="500")

    assert isinstance(raw, dict)


# test store radius item has business name 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
@pytest.mark.usefixtures("require_semas_key")
def test_store_radius_item_has_business_name(live_client: Client) -> None:
    """
    test store radius item has business name 시나리오를 검증한다.

    매개변수:
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    ds = live_client.dataset("semas.store_radius")
    result = ds.list(cx="127.02758", cy="37.49794", radius="500")

    assert len(result.items) > 0
    item = result.items[0]
    assert "bizesNm" in item


# test upjong large returns categories 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
@pytest.mark.usefixtures("require_semas_key")
def test_upjong_large_returns_categories(live_client: Client) -> None:
    """
    test upjong large returns categories 시나리오를 검증한다.

    매개변수:
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    ds = live_client.dataset("semas.upjong_large")

    result = ds.list()

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0


# test zone one returns record batch 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
@pytest.mark.usefixtures("require_semas_key")
def test_zone_one_returns_record_batch(live_client: Client) -> None:
    """
    test zone one returns record batch 시나리오를 검증한다.

    매개변수:
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    ds = live_client.dataset("semas.zone_one")

    result = ds.list(key="D00001")

    assert isinstance(result, RecordBatch)
