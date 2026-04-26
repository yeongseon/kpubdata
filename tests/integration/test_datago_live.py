from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from kpubdata.client import Client
from kpubdata.core.models import RecordBatch


def _yesterday_kst_ymd() -> str:
    return (datetime.now(ZoneInfo("Asia/Seoul")) - timedelta(days=1)).strftime("%Y%m%d")


@pytest.mark.integration
def test_datago_village_fcst(require_datago_key: None, live_client: Client) -> None:
    _ = require_datago_key
    ds = live_client.dataset("datago.village_fcst")

    result = ds.list(base_date=_yesterday_kst_ymd(), base_time="2300", nx="55", ny="127")

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0
    assert isinstance(result.items[0], dict)


@pytest.mark.integration
def test_datago_ultra_srt_ncst(require_datago_key: None, live_client: Client) -> None:
    _ = require_datago_key
    ds = live_client.dataset("datago.ultra_srt_ncst")

    result = ds.list(base_date=_yesterday_kst_ymd(), base_time="2300", nx="55", ny="127")

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0
    assert isinstance(result.items[0], dict)


@pytest.mark.integration
def test_datago_air_quality(require_datago_key: None, live_client: Client) -> None:
    _ = require_datago_key
    ds = live_client.dataset("datago.air_quality")

    result = ds.call_raw("getCtprvnRltmMesureDnsty", sidoName="서울", numOfRows="5")

    assert isinstance(result, dict)
    assert "response" in result


@pytest.mark.integration
def test_datago_bus_arrival(
    require_datago_key: None,
    require_realestate_key: None,
    live_client: Client,
) -> None:
    _ = require_datago_key
    _ = require_realestate_key
    ds = live_client.dataset("datago.bus_arrival")

    result = ds.call_raw("getBusArrivalListv2", stationId="228000704", numOfRows="5")

    assert isinstance(result, dict)
    assert "response" in result


@pytest.mark.integration
def test_datago_hospital_info(require_datago_key: None, live_client: Client) -> None:
    _ = require_datago_key
    ds = live_client.dataset("datago.hospital_info")

    result = ds.call_raw("getHospBasisList", numOfRows="5")

    assert isinstance(result, dict)
    assert "response" in result


@pytest.mark.integration
def test_datago_apt_trade(require_datago_key: None, live_client: Client) -> None:
    _ = require_datago_key
    ds = live_client.dataset("datago.apt_trade")

    result = ds.list(LAWD_CD="11110", DEAL_YMD="202401")

    assert isinstance(result, RecordBatch)
    assert isinstance(result.items, list)


@pytest.mark.integration
def test_datago_apt_rent(
    require_datago_key: None,
    require_realestate_key: None,
    live_client: Client,
) -> None:
    _ = require_datago_key
    _ = require_realestate_key
    ds = live_client.dataset("datago.apt_rent")

    result = ds.list(LAWD_CD="11110", DEAL_YMD="202401")

    assert isinstance(result, RecordBatch)
    assert isinstance(result.items, list)


@pytest.mark.integration
def test_datago_offi_trade(
    require_datago_key: None,
    require_realestate_key: None,
    live_client: Client,
) -> None:
    _ = require_datago_key
    _ = require_realestate_key
    ds = live_client.dataset("datago.offi_trade")

    result = ds.list(LAWD_CD="11110", DEAL_YMD="202401")

    assert isinstance(result, RecordBatch)
    assert isinstance(result.items, list)


@pytest.mark.integration
def test_datago_offi_rent(
    require_datago_key: None,
    require_realestate_key: None,
    live_client: Client,
) -> None:
    _ = require_datago_key
    _ = require_realestate_key
    ds = live_client.dataset("datago.offi_rent")

    result = ds.list(LAWD_CD="11110", DEAL_YMD="202401")

    assert isinstance(result, RecordBatch)
    assert isinstance(result.items, list)


@pytest.mark.integration
def test_datago_rh_trade(
    require_datago_key: None,
    require_realestate_key: None,
    live_client: Client,
) -> None:
    _ = require_datago_key
    _ = require_realestate_key
    ds = live_client.dataset("datago.rh_trade")

    result = ds.list(LAWD_CD="11110", DEAL_YMD="202401")

    assert isinstance(result, RecordBatch)
    assert isinstance(result.items, list)


@pytest.mark.integration
def test_datago_rh_rent(
    require_datago_key: None,
    require_realestate_key: None,
    live_client: Client,
) -> None:
    _ = require_datago_key
    _ = require_realestate_key
    ds = live_client.dataset("datago.rh_rent")

    result = ds.list(LAWD_CD="11110", DEAL_YMD="202401")

    assert isinstance(result, RecordBatch)
    assert isinstance(result.items, list)


@pytest.mark.integration
def test_datago_sh_trade(
    require_datago_key: None,
    require_realestate_key: None,
    live_client: Client,
) -> None:
    _ = require_datago_key
    _ = require_realestate_key
    ds = live_client.dataset("datago.sh_trade")

    result = ds.list(LAWD_CD="11110", DEAL_YMD="202401")

    assert isinstance(result, RecordBatch)
    assert isinstance(result.items, list)


@pytest.mark.integration
def test_datago_sh_rent(
    require_datago_key: None,
    require_realestate_key: None,
    live_client: Client,
) -> None:
    _ = require_datago_key
    _ = require_realestate_key
    ds = live_client.dataset("datago.sh_rent")

    result = ds.list(LAWD_CD="11110", DEAL_YMD="202401")

    assert isinstance(result, RecordBatch)
    assert isinstance(result.items, list)


@pytest.mark.integration
def test_datago_tour_kor_area(require_datago_key: None, live_client: Client) -> None:
    _ = require_datago_key
    ds = live_client.dataset("datago.tour_kor_area")

    result = ds.call_raw(
        "areaBasedList2",
        MobileOS="ETC",
        MobileApp="kpubdata",
        numOfRows="5",
        pageNo="1",
        areaCode="1",
    )

    assert isinstance(result, dict)
    assert "response" in result


@pytest.mark.integration
def test_datago_tour_kor_location(require_datago_key: None, live_client: Client) -> None:
    _ = require_datago_key
    ds = live_client.dataset("datago.tour_kor_location")

    result = ds.call_raw(
        "locationBasedList2",
        MobileOS="ETC",
        MobileApp="kpubdata",
        numOfRows="5",
        pageNo="1",
        mapX="126.9784",
        mapY="37.5665",
        radius="1000",
    )

    assert isinstance(result, dict)
    assert "response" in result


@pytest.mark.integration
def test_datago_tour_kor_keyword(require_datago_key: None, live_client: Client) -> None:
    _ = require_datago_key
    ds = live_client.dataset("datago.tour_kor_keyword")

    result = ds.call_raw(
        "searchKeyword2",
        MobileOS="ETC",
        MobileApp="kpubdata",
        numOfRows="5",
        pageNo="1",
        keyword="경복궁",
    )

    assert isinstance(result, dict)
    assert "response" in result


@pytest.mark.integration
def test_datago_tour_kor_festival(require_datago_key: None, live_client: Client) -> None:
    _ = require_datago_key
    ds = live_client.dataset("datago.tour_kor_festival")

    result = ds.call_raw(
        "searchFestival2",
        MobileOS="ETC",
        MobileApp="kpubdata",
        numOfRows="5",
        pageNo="1",
        eventStartDate="20250101",
    )

    assert isinstance(result, dict)
    assert "response" in result


@pytest.mark.integration
@pytest.mark.skip(
    reason="External infra issue: see https://github.com/yeongseon/kpubdata/issues/139"
)
def test_datago_metro_fare(require_datago_key: None, live_client: Client) -> None:
    _ = require_datago_key
    ds = live_client.dataset("datago.metro_fare")

    result = ds.call_raw(
        "getRltmFare2",
        numOfRows="5",
        pageNo="1",
        dptreStnNm="서울역",
        avrlStnNm="시청",
    )

    assert isinstance(result, dict)
    assert "response" in result


@pytest.mark.integration
@pytest.mark.skip(
    reason="Blocked by metro_fare upstream SSL issue (#139); params confirmed per #140"
)
def test_datago_metro_path(require_datago_key: None, live_client: Client) -> None:
    _ = require_datago_key
    ds = live_client.dataset("datago.metro_path")

    result = ds.call_raw(
        "getShtrmPath",
        dptreStnNm="신도림",
        arvlStnNm="서울역",
        searchDt="2026-04-22 13:00:00",
    )

    assert isinstance(result, dict)
    assert "response" in result


@pytest.mark.integration
def test_datago_g2b_contract(require_datago_key: None, live_client: Client) -> None:
    _ = require_datago_key
    ds = live_client.dataset("datago.g2b_contract")

    result = ds.list(page_size=5)

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0
    assert isinstance(result.items[0], dict)


@pytest.mark.integration
def test_datago_social_enterprise(require_datago_key: None, live_client: Client) -> None:
    _ = require_datago_key
    ds = live_client.dataset("datago.social_enterprise")

    result = ds.list(page_size=5)

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0
    assert isinstance(result.items[0], dict)


@pytest.mark.integration
def test_datago_g2b_catalog(require_datago_key: None, live_client: Client) -> None:
    _ = require_datago_key
    ds = live_client.dataset("datago.g2b_catalog")

    result = ds.list(page_size=5)

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0
    assert isinstance(result.items[0], dict)
