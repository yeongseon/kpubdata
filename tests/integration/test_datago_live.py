"""테스트 모듈.

이 파일은 ``tests/integration/test_datago_live.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from kpubdata.client import Client
from kpubdata.core.models import RecordBatch


def _yesterday_kst_ymd() -> str:
    """
    내부 헬퍼로서 yesterday kst ymd 처리를 담당한다.

    반환값:
        str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    return (datetime.now(ZoneInfo("Asia/Seoul")) - timedelta(days=1)).strftime("%Y%m%d")


# test datago village fcst 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_datago_village_fcst(require_datago_key: None, live_client: Client) -> None:
    """
    test datago village fcst 시나리오를 검증한다.

    매개변수:
        require_datago_key (None): 호출자가 제공하는 입력 값이다.
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    _ = require_datago_key
    ds = live_client.dataset("datago.village_fcst")

    result = ds.list(base_date=_yesterday_kst_ymd(), base_time="2300", nx="55", ny="127")

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0
    assert isinstance(result.items[0], dict)


# test datago ultra srt ncst 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_datago_ultra_srt_ncst(require_datago_key: None, live_client: Client) -> None:
    """
    test datago ultra srt ncst 시나리오를 검증한다.

    매개변수:
        require_datago_key (None): 호출자가 제공하는 입력 값이다.
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    _ = require_datago_key
    ds = live_client.dataset("datago.ultra_srt_ncst")

    result = ds.list(base_date=_yesterday_kst_ymd(), base_time="2300", nx="55", ny="127")

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0
    assert isinstance(result.items[0], dict)


# test datago air quality 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_datago_air_quality(require_datago_key: None, live_client: Client) -> None:
    """
    test datago air quality 시나리오를 검증한다.

    매개변수:
        require_datago_key (None): 호출자가 제공하는 입력 값이다.
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    _ = require_datago_key
    ds = live_client.dataset("datago.air_quality")

    result = ds.call_raw("getCtprvnRltmMesureDnsty", sidoName="서울", numOfRows="5")

    assert isinstance(result, dict)
    assert "response" in result


# test datago bus arrival 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_datago_bus_arrival(
    require_datago_key: None,
    require_realestate_key: None,
    live_client: Client,
) -> None:
    """
    test datago bus arrival 시나리오를 검증한다.

    매개변수:
        require_datago_key (None): 호출자가 제공하는 입력 값이다.
        require_realestate_key (None): 호출자가 제공하는 입력 값이다.
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    _ = require_datago_key
    _ = require_realestate_key
    ds = live_client.dataset("datago.bus_arrival")

    result = ds.call_raw("getBusArrivalListv2", stationId="228000704", numOfRows="5")

    assert isinstance(result, dict)
    assert "response" in result


# test datago hospital info 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_datago_hospital_info(require_datago_key: None, live_client: Client) -> None:
    """
    test datago hospital info 시나리오를 검증한다.

    매개변수:
        require_datago_key (None): 호출자가 제공하는 입력 값이다.
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    _ = require_datago_key
    ds = live_client.dataset("datago.hospital_info")

    result = ds.call_raw("getHospBasisList", numOfRows="5")

    assert isinstance(result, dict)
    assert "response" in result


# test datago apt trade 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_datago_apt_trade(require_datago_key: None, live_client: Client) -> None:
    """
    test datago apt trade 시나리오를 검증한다.

    매개변수:
        require_datago_key (None): 호출자가 제공하는 입력 값이다.
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    _ = require_datago_key
    ds = live_client.dataset("datago.apt_trade")

    result = ds.list(LAWD_CD="11110", DEAL_YMD="202401")

    assert isinstance(result, RecordBatch)
    assert isinstance(result.items, list)


# test datago apt rent 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_datago_apt_rent(
    require_datago_key: None,
    require_realestate_key: None,
    live_client: Client,
) -> None:
    """
    test datago apt rent 시나리오를 검증한다.

    매개변수:
        require_datago_key (None): 호출자가 제공하는 입력 값이다.
        require_realestate_key (None): 호출자가 제공하는 입력 값이다.
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    _ = require_datago_key
    _ = require_realestate_key
    ds = live_client.dataset("datago.apt_rent")

    result = ds.list(LAWD_CD="11110", DEAL_YMD="202401")

    assert isinstance(result, RecordBatch)
    assert isinstance(result.items, list)


# test datago offi trade 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_datago_offi_trade(
    require_datago_key: None,
    require_realestate_key: None,
    live_client: Client,
) -> None:
    """
    test datago offi trade 시나리오를 검증한다.

    매개변수:
        require_datago_key (None): 호출자가 제공하는 입력 값이다.
        require_realestate_key (None): 호출자가 제공하는 입력 값이다.
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    _ = require_datago_key
    _ = require_realestate_key
    ds = live_client.dataset("datago.offi_trade")

    result = ds.list(LAWD_CD="11110", DEAL_YMD="202401")

    assert isinstance(result, RecordBatch)
    assert isinstance(result.items, list)


# test datago offi rent 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_datago_offi_rent(
    require_datago_key: None,
    require_realestate_key: None,
    live_client: Client,
) -> None:
    """
    test datago offi rent 시나리오를 검증한다.

    매개변수:
        require_datago_key (None): 호출자가 제공하는 입력 값이다.
        require_realestate_key (None): 호출자가 제공하는 입력 값이다.
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    _ = require_datago_key
    _ = require_realestate_key
    ds = live_client.dataset("datago.offi_rent")

    result = ds.list(LAWD_CD="11110", DEAL_YMD="202401")

    assert isinstance(result, RecordBatch)
    assert isinstance(result.items, list)


# test datago rh trade 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_datago_rh_trade(
    require_datago_key: None,
    require_realestate_key: None,
    live_client: Client,
) -> None:
    """
    test datago rh trade 시나리오를 검증한다.

    매개변수:
        require_datago_key (None): 호출자가 제공하는 입력 값이다.
        require_realestate_key (None): 호출자가 제공하는 입력 값이다.
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    _ = require_datago_key
    _ = require_realestate_key
    ds = live_client.dataset("datago.rh_trade")

    result = ds.list(LAWD_CD="11110", DEAL_YMD="202401")

    assert isinstance(result, RecordBatch)
    assert isinstance(result.items, list)


# test datago rh rent 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_datago_rh_rent(
    require_datago_key: None,
    require_realestate_key: None,
    live_client: Client,
) -> None:
    """
    test datago rh rent 시나리오를 검증한다.

    매개변수:
        require_datago_key (None): 호출자가 제공하는 입력 값이다.
        require_realestate_key (None): 호출자가 제공하는 입력 값이다.
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    _ = require_datago_key
    _ = require_realestate_key
    ds = live_client.dataset("datago.rh_rent")

    result = ds.list(LAWD_CD="11110", DEAL_YMD="202401")

    assert isinstance(result, RecordBatch)
    assert isinstance(result.items, list)


# test datago sh trade 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_datago_sh_trade(
    require_datago_key: None,
    require_realestate_key: None,
    live_client: Client,
) -> None:
    """
    test datago sh trade 시나리오를 검증한다.

    매개변수:
        require_datago_key (None): 호출자가 제공하는 입력 값이다.
        require_realestate_key (None): 호출자가 제공하는 입력 값이다.
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    _ = require_datago_key
    _ = require_realestate_key
    ds = live_client.dataset("datago.sh_trade")

    result = ds.list(LAWD_CD="11110", DEAL_YMD="202401")

    assert isinstance(result, RecordBatch)
    assert isinstance(result.items, list)


# test datago sh rent 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_datago_sh_rent(
    require_datago_key: None,
    require_realestate_key: None,
    live_client: Client,
) -> None:
    """
    test datago sh rent 시나리오를 검증한다.

    매개변수:
        require_datago_key (None): 호출자가 제공하는 입력 값이다.
        require_realestate_key (None): 호출자가 제공하는 입력 값이다.
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    _ = require_datago_key
    _ = require_realestate_key
    ds = live_client.dataset("datago.sh_rent")

    result = ds.list(LAWD_CD="11110", DEAL_YMD="202401")

    assert isinstance(result, RecordBatch)
    assert isinstance(result.items, list)


# test datago tour kor area 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_datago_tour_kor_area(require_datago_key: None, live_client: Client) -> None:
    """
    test datago tour kor area 시나리오를 검증한다.

    매개변수:
        require_datago_key (None): 호출자가 제공하는 입력 값이다.
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
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


# test datago tour kor location 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_datago_tour_kor_location(require_datago_key: None, live_client: Client) -> None:
    """
    test datago tour kor location 시나리오를 검증한다.

    매개변수:
        require_datago_key (None): 호출자가 제공하는 입력 값이다.
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
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


# test datago tour kor keyword 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_datago_tour_kor_keyword(require_datago_key: None, live_client: Client) -> None:
    """
    test datago tour kor keyword 시나리오를 검증한다.

    매개변수:
        require_datago_key (None): 호출자가 제공하는 입력 값이다.
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
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


# test datago tour kor festival 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_datago_tour_kor_festival(require_datago_key: None, live_client: Client) -> None:
    """
    test datago tour kor festival 시나리오를 검증한다.

    매개변수:
        require_datago_key (None): 호출자가 제공하는 입력 값이다.
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
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


# test datago metro fare 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
@pytest.mark.skip(
    reason="External infra issue: see https://github.com/yeongseon/kpubdata/issues/139"
)
def test_datago_metro_fare(require_datago_key: None, live_client: Client) -> None:
    """
    test datago metro fare 시나리오를 검증한다.

    매개변수:
        require_datago_key (None): 호출자가 제공하는 입력 값이다.
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
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


# test datago metro path 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
@pytest.mark.skip(
    reason="Blocked by metro_fare upstream SSL issue (#139); params confirmed per #140"
)
def test_datago_metro_path(require_datago_key: None, live_client: Client) -> None:
    """
    test datago metro path 시나리오를 검증한다.

    매개변수:
        require_datago_key (None): 호출자가 제공하는 입력 값이다.
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
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


# test datago road traffic 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
@pytest.mark.skip(
    reason="ITS Open API requires a separate apiKey from openapi.its.go.kr "
    "(not data.go.kr serviceKey)"
)
def test_datago_road_traffic(require_datago_key: None, live_client: Client) -> None:
    """
    test datago road traffic 시나리오를 검증한다.

    매개변수:
        require_datago_key (None): 호출자가 제공하는 입력 값이다.
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    _ = require_datago_key
    ds = live_client.dataset("datago.road_traffic")

    result = ds.call_raw("trafficInfo", type="all", drcType="all")

    assert isinstance(result, dict)
    assert "resultCode" in result


# test datago g2b contract 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_datago_g2b_contract(require_datago_key: None, live_client: Client) -> None:
    """
    test datago g2b contract 시나리오를 검증한다.

    매개변수:
        require_datago_key (None): 호출자가 제공하는 입력 값이다.
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    _ = require_datago_key
    ds = live_client.dataset("datago.g2b_contract")

    result = ds.list(page_size=5)

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0
    assert isinstance(result.items[0], dict)


# test datago social enterprise 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_datago_social_enterprise(require_datago_key: None, live_client: Client) -> None:
    """
    test datago social enterprise 시나리오를 검증한다.

    매개변수:
        require_datago_key (None): 호출자가 제공하는 입력 값이다.
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    _ = require_datago_key
    ds = live_client.dataset("datago.social_enterprise")

    result = ds.list(page_size=5)

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0
    assert isinstance(result.items[0], dict)


# test datago g2b catalog 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_datago_g2b_catalog(require_datago_key: None, live_client: Client) -> None:
    """
    test datago g2b catalog 시나리오를 검증한다.

    매개변수:
        require_datago_key (None): 호출자가 제공하는 입력 값이다.
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    _ = require_datago_key
    ds = live_client.dataset("datago.g2b_catalog")

    result = ds.list(page_size=5)

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0
    assert isinstance(result.items[0], dict)
