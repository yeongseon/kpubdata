from __future__ import annotations

import os
from collections.abc import Generator

import pytest

from kpubdata.client import Client


@pytest.fixture(scope="session")
def require_datago_key() -> str:
    key = os.getenv("KPUBDATA_DATAGO_API_KEY", "")
    if not key:
        pytest.skip("KPUBDATA_DATAGO_API_KEY not set")
    return key


@pytest.fixture
def require_realestate_key() -> Generator[None, None, None]:
    if os.environ.get("KPUBDATA_DATAGO_REALESTATE_ENABLED") != "1":
        pytest.skip(
            "Set KPUBDATA_DATAGO_REALESTATE_ENABLED=1 once "
            + "국토부 RTMS APIs have been 활용신청 approved on this key"
        )
    yield


@pytest.fixture(scope="session")
def require_bok_key() -> str:
    key = os.getenv("KPUBDATA_BOK_API_KEY", "")
    if not key:
        pytest.skip("KPUBDATA_BOK_API_KEY not set")
    return key


@pytest.fixture(scope="session")
def require_kosis_key() -> str:
    key = os.getenv("KPUBDATA_KOSIS_API_KEY", "")
    if not key:
        pytest.skip("KPUBDATA_KOSIS_API_KEY not set")
    return key


@pytest.fixture(scope="session")
def require_lofin_key() -> str:
    key = os.getenv("KPUBDATA_LOFIN_API_KEY", "")
    if not key:
        pytest.skip("KPUBDATA_LOFIN_API_KEY not set")
    return key


@pytest.fixture(scope="session")
def require_localdata_key() -> str:
    key = os.getenv("KPUBDATA_LOCALDATA_API_KEY", "")
    if not key:
        pytest.skip("KPUBDATA_LOCALDATA_API_KEY not set")
    return key


@pytest.fixture(scope="session")
def require_seoul_key() -> str:
    key = os.getenv("KPUBDATA_SEOUL_API_KEY", "")
    if not key:
        pytest.skip("KPUBDATA_SEOUL_API_KEY not set")
    return key


@pytest.fixture(scope="session")
def require_semas_key() -> str:
    key = os.getenv("KPUBDATA_SEMAS_API_KEY", "")
    if not key:
        pytest.skip("KPUBDATA_SEMAS_API_KEY not set")
    return key


@pytest.fixture(scope="session")
def require_sgis_key() -> str:
    key = os.getenv("KPUBDATA_SGIS_API_KEY", "")
    if not key:
        pytest.skip("KPUBDATA_SGIS_API_KEY not set")
    return key


@pytest.fixture(scope="session")
def live_client() -> Client:
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
