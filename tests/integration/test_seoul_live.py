"""테스트 모듈.

이 파일은 ``tests/integration/test_seoul_live.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from kpubdata.client import Client


def _three_months_ago_kst_yyyymm() -> str:
    """
    내부 헬퍼로서 three months ago kst yyyymm 처리를 담당한다.

    반환값:
        str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    year = now.year
    month = now.month - 3
    while month <= 0:
        month += 12
        year -= 1
    return f"{year:04d}{month:02d}"


# test seoul subway realtime arrival 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_seoul_subway_realtime_arrival(require_seoul_key: None, live_client: Client) -> None:
    """
    test seoul subway realtime arrival 시나리오를 검증한다.

    매개변수:
        require_seoul_key (None): 호출자가 제공하는 입력 값이다.
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    _ = require_seoul_key
    ds = live_client.dataset("seoul.subway_realtime_arrival")

    result = ds.call_raw("realtimeStationArrival", stationName="강남", page_no=1, page_size=5)

    assert isinstance(result, dict)
    assert "realtimeStationArrival" in result


# test seoul bike rent month 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_seoul_bike_rent_month(require_seoul_key: None, live_client: Client) -> None:
    """
    test seoul bike rent month 시나리오를 검증한다.

    매개변수:
        require_seoul_key (None): 호출자가 제공하는 입력 값이다.
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    _ = require_seoul_key
    ds = live_client.dataset("seoul.bike_rent_month")

    result = ds.call_raw(
        "tbCycleRentUseMonthInfo",
        RENT_NM=_three_months_ago_kst_yyyymm(),
        page_no=1,
        page_size=5,
    )

    assert isinstance(result, dict)
    assert "tbCycleRentUseMonthInfo" in result
