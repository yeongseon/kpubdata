"""Localdata (data.go.kr) real API integration tests.

Run with:
    export KPUBDATA_LOCALDATA_API_KEY="your-key"
    uv run pytest -m integration -k localdata -ra -v
"""

from __future__ import annotations

import pytest

from kpubdata.client import Client
from kpubdata.core.models import RecordBatch


# test general restaurant returns record batch 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
@pytest.mark.usefixtures("require_localdata_key")
def test_general_restaurant_returns_record_batch(live_client: Client) -> None:
    """
    test general restaurant returns record batch 시나리오를 검증한다.

    매개변수:
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    ds = live_client.dataset("localdata.general_restaurant")
    result = ds.list(page_size=5)

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0


# test general restaurant raw returns envelope 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
@pytest.mark.usefixtures("require_localdata_key")
def test_general_restaurant_raw_returns_envelope(live_client: Client) -> None:
    """
    test general restaurant raw returns envelope 시나리오를 검증한다.

    매개변수:
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    ds = live_client.dataset("localdata.general_restaurant")
    result = ds.call_raw("info", numOfRows="3")

    assert isinstance(result, dict)
    assert "response" in result


# test rest cafe returns record batch 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
@pytest.mark.usefixtures("require_localdata_key")
def test_rest_cafe_returns_record_batch(live_client: Client) -> None:
    """
    test rest cafe returns record batch 시나리오를 검증한다.

    매개변수:
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    ds = live_client.dataset("localdata.rest_cafe")
    result = ds.list(page_size=5)

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0


LOCALDATA_COMMON_KEYS = {"BPLC_NM", "SALS_STTS_NM", "ROAD_NM_ADDR", "STTUS_ADDR"}


# test general restaurant has required fields 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
@pytest.mark.usefixtures("require_localdata_key")
def test_general_restaurant_has_required_fields(live_client: Client) -> None:
    """
    test general restaurant has required fields 시나리오를 검증한다.

    매개변수:
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    ds = live_client.dataset("localdata.general_restaurant")
    result = ds.list(page_size=5)
    item = result.items[0]

    assert LOCALDATA_COMMON_KEYS.issubset(item.keys())


# test general restaurant total count 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
@pytest.mark.usefixtures("require_localdata_key")
def test_general_restaurant_total_count(live_client: Client) -> None:
    """
    test general restaurant total count 시나리오를 검증한다.

    매개변수:
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    ds = live_client.dataset("localdata.general_restaurant")
    result = ds.list(page_size=5)

    assert result.total_count is not None
    assert result.total_count > 0


ALL_DATASETS = [
    "localdata.general_restaurant",
    "localdata.rest_cafe",
]


# test all datasets return data 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
@pytest.mark.usefixtures("require_localdata_key")
@pytest.mark.parametrize("dataset_id", ALL_DATASETS)
def test_all_datasets_return_data(live_client: Client, dataset_id: str) -> None:
    """
    test all datasets return data 시나리오를 검증한다.

    매개변수:
        live_client (Client): 호출자가 제공하는 입력 값이다.
        dataset_id (str): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    ds = live_client.dataset(dataset_id)
    result = ds.list(page_size=3)

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0
    assert result.total_count is not None
    assert result.total_count > 0
