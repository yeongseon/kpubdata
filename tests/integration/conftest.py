"""테스트 모듈.

이 파일은 ``tests/integration/conftest.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest

from kpubdata.client import Client


@pytest.fixture(scope="session")
def require_datago_key() -> str:
    """
    require datago key 동작을 수행한다.

    반환값:
        str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    key = os.getenv("KPUBDATA_DATAGO_API_KEY", "")
    if not key:
        pytest.skip("KPUBDATA_DATAGO_API_KEY not set")
    return key


@pytest.fixture
def require_realestate_key() -> Generator[None, None, None]:
    """
    require realestate key 동작을 수행한다.

    반환값:
        Generator[None, None, None]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    if os.environ.get("KPUBDATA_DATAGO_REALESTATE_ENABLED") != "1":
        pytest.skip(
            "Set KPUBDATA_DATAGO_REALESTATE_ENABLED=1 once "
            + "국토부 RTMS APIs have been 활용신청 approved on this key"
        )
    yield


@pytest.fixture(scope="session")
def require_bok_key() -> str:
    """
    require bok key 동작을 수행한다.

    반환값:
        str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    key = os.getenv("KPUBDATA_BOK_API_KEY", "")
    if not key:
        pytest.skip("KPUBDATA_BOK_API_KEY not set")
    return key


@pytest.fixture(scope="session")
def require_kosis_key() -> str:
    """
    require kosis key 동작을 수행한다.

    반환값:
        str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    key = os.getenv("KPUBDATA_KOSIS_API_KEY", "")
    if not key:
        pytest.skip("KPUBDATA_KOSIS_API_KEY not set")
    return key


@pytest.fixture(scope="session")
def require_lofin_key() -> str:
    """
    require lofin key 동작을 수행한다.

    반환값:
        str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    key = os.getenv("KPUBDATA_LOFIN_API_KEY", "")
    if not key:
        pytest.skip("KPUBDATA_LOFIN_API_KEY not set")
    return key


@pytest.fixture(scope="session")
def require_localdata_key() -> str:
    """
    require localdata key 동작을 수행한다.

    반환값:
        str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    key = os.getenv("KPUBDATA_LOCALDATA_API_KEY", "")
    if not key:
        pytest.skip("KPUBDATA_LOCALDATA_API_KEY not set")
    return key


@pytest.fixture(scope="session")
def require_seoul_key() -> str:
    """
    require seoul key 동작을 수행한다.

    반환값:
        str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    key = os.getenv("KPUBDATA_SEOUL_API_KEY", "")
    if not key:
        pytest.skip("KPUBDATA_SEOUL_API_KEY not set")
    return key


@pytest.fixture(scope="session")
def require_semas_key() -> str:
    """
    require semas key 동작을 수행한다.

    반환값:
        str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    key = os.getenv("KPUBDATA_SEMAS_API_KEY", "")
    if not key:
        pytest.skip("KPUBDATA_SEMAS_API_KEY not set")
    return key


@pytest.fixture(scope="session")
def require_sgis_key() -> str:
    """
    require sgis key 동작을 수행한다.

    반환값:
        str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    key = os.getenv("KPUBDATA_SGIS_API_KEY", "")
    if not key:
        pytest.skip("KPUBDATA_SGIS_API_KEY not set")
    return key


@pytest.fixture(scope="session")
def live_client() -> Client:
    """
    live client 동작을 수행한다.

    반환값:
        Client: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    if not any(
        os.getenv(name, "")
        for name in (
            "KPUBDATA_DATAGO_API_KEY",
            "KPUBDATA_BOK_API_KEY",
            "KPUBDATA_KOSIS_API_KEY",
            "KPUBDATA_LOFIN_API_KEY",
            "KPUBDATA_LOCALDATA_API_KEY",
            "KPUBDATA_SEOUL_API_KEY",
            "KPUBDATA_SEMAS_API_KEY",
            "KPUBDATA_SGIS_API_KEY",
        )
    ):
        pytest.skip("No API keys set")
    return Client.from_env()
