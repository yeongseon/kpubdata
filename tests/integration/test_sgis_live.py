"""테스트 모듈.

이 파일은 ``tests/integration/test_sgis_live.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

import pytest

from kpubdata.client import Client
from kpubdata.core.models import RecordBatch


# test boundary sido returns record batch 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
@pytest.mark.usefixtures("require_sgis_key")
def test_boundary_sido_returns_record_batch(live_client: Client) -> None:
    """
    test boundary sido returns record batch 시나리오를 검증한다.

    매개변수:
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    ds = live_client.dataset("sgis.boundary.sido")

    result = ds.list()

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0


# test boundary sido has geometry 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
@pytest.mark.usefixtures("require_sgis_key")
def test_boundary_sido_has_geometry(live_client: Client) -> None:
    """
    test boundary sido has geometry 시나리오를 검증한다.

    매개변수:
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    ds = live_client.dataset("sgis.boundary.sido")
    result = ds.list()

    item = result.items[0]
    assert "geometry" in item or "adm_cd" in item


# test boundary sido raw returns geojson 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
@pytest.mark.usefixtures("require_sgis_key")
def test_boundary_sido_raw_returns_geojson(live_client: Client) -> None:
    """
    test boundary sido raw returns geojson 시나리오를 검증한다.

    매개변수:
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    ds = live_client.dataset("sgis.boundary.sido")

    raw = ds.call_raw("list")

    assert isinstance(raw, dict)
    assert "features" in raw


# test boundary sigungu returns record batch 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
@pytest.mark.usefixtures("require_sgis_key")
def test_boundary_sigungu_returns_record_batch(live_client: Client) -> None:
    """
    test boundary sigungu returns record batch 시나리오를 검증한다.

    매개변수:
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    ds = live_client.dataset("sgis.boundary.sigungu")

    result = ds.list()

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0


# test boundary sido count is reasonable 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
@pytest.mark.usefixtures("require_sgis_key")
def test_boundary_sido_count_is_reasonable(live_client: Client) -> None:
    """
    test boundary sido count is reasonable 시나리오를 검증한다.

    매개변수:
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    ds = live_client.dataset("sgis.boundary.sido")
    result = ds.list()

    assert 15 <= len(result.items) <= 20
