from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from kpubdata.client import Client


def _three_months_ago_kst_yyyymm() -> str:
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    year = now.year
    month = now.month - 3
    while month <= 0:
        month += 12
        year -= 1
    return f"{year:04d}{month:02d}"


@pytest.mark.integration
def test_seoul_subway_realtime_arrival(require_seoul_key: None, live_client: Client) -> None:
    _ = require_seoul_key
    ds = live_client.dataset("seoul.subway_realtime_arrival")

    result = ds.call_raw("realtimeStationArrival", stationName="강남", page_no=1, page_size=5)

    assert isinstance(result, dict)
    assert "realtimeStationArrival" in result


@pytest.mark.integration
def test_seoul_bike_rent_month(require_seoul_key: None, live_client: Client) -> None:
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
