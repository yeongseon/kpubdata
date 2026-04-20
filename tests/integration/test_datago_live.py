from __future__ import annotations

import pytest

from kpubdata.client import Client
from kpubdata.core.models import RecordBatch


@pytest.mark.integration
def test_datago_village_fcst(require_datago_key: None, live_client: Client) -> None:
    _ = require_datago_key
    ds = live_client.dataset("datago.village_fcst")

    result = ds.list(base_date="20250401", base_time="0500", nx="55", ny="127")

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0
    assert isinstance(result.items[0], dict)


@pytest.mark.integration
def test_datago_ultra_srt_ncst(require_datago_key: None, live_client: Client) -> None:
    _ = require_datago_key
    ds = live_client.dataset("datago.ultra_srt_ncst")

    result = ds.list(base_date="20250401", base_time="0600", nx="55", ny="127")

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
def test_datago_bus_arrival(require_datago_key: None, live_client: Client) -> None:
    _ = require_datago_key
    ds = live_client.dataset("datago.bus_arrival")

    result = ds.call_raw("getBusArrivalList", stationId="228000704", numOfRows="5")

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
def test_datago_apt_rent(require_datago_key: None, live_client: Client) -> None:
    _ = require_datago_key
    ds = live_client.dataset("datago.apt_rent")

    result = ds.list(LAWD_CD="11110", DEAL_YMD="202401")

    assert isinstance(result, RecordBatch)
    assert isinstance(result.items, list)


@pytest.mark.integration
def test_datago_offi_trade(require_datago_key: None, live_client: Client) -> None:
    _ = require_datago_key
    ds = live_client.dataset("datago.offi_trade")

    result = ds.list(LAWD_CD="11110", DEAL_YMD="202401")

    assert isinstance(result, RecordBatch)
    assert isinstance(result.items, list)


@pytest.mark.integration
def test_datago_offi_rent(require_datago_key: None, live_client: Client) -> None:
    _ = require_datago_key
    ds = live_client.dataset("datago.offi_rent")

    result = ds.list(LAWD_CD="11110", DEAL_YMD="202401")

    assert isinstance(result, RecordBatch)
    assert isinstance(result.items, list)


@pytest.mark.integration
def test_datago_rh_trade(require_datago_key: None, live_client: Client) -> None:
    _ = require_datago_key
    ds = live_client.dataset("datago.rh_trade")

    result = ds.list(LAWD_CD="11110", DEAL_YMD="202401")

    assert isinstance(result, RecordBatch)
    assert isinstance(result.items, list)


@pytest.mark.integration
def test_datago_rh_rent(require_datago_key: None, live_client: Client) -> None:
    _ = require_datago_key
    ds = live_client.dataset("datago.rh_rent")

    result = ds.list(LAWD_CD="11110", DEAL_YMD="202401")

    assert isinstance(result, RecordBatch)
    assert isinstance(result.items, list)


@pytest.mark.integration
def test_datago_sh_trade(require_datago_key: None, live_client: Client) -> None:
    _ = require_datago_key
    ds = live_client.dataset("datago.sh_trade")

    result = ds.list(LAWD_CD="11110", DEAL_YMD="202401")

    assert isinstance(result, RecordBatch)
    assert isinstance(result.items, list)


@pytest.mark.integration
def test_datago_sh_rent(require_datago_key: None, live_client: Client) -> None:
    _ = require_datago_key
    ds = live_client.dataset("datago.sh_rent")

    result = ds.list(LAWD_CD="11110", DEAL_YMD="202401")

    assert isinstance(result, RecordBatch)
    assert isinstance(result.items, list)
