from __future__ import annotations

import os

import pytest

from kpubdata.client import Client


@pytest.fixture(scope="session")
def require_datago_key() -> str:
    key = os.getenv("KPUBDATA_DATAGO_API_KEY", "")
    if not key:
        pytest.skip("KPUBDATA_DATAGO_API_KEY not set")
    return key


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
def live_client() -> Client:
    if not any(
        os.getenv(name, "")
        for name in (
            "KPUBDATA_DATAGO_API_KEY",
            "KPUBDATA_BOK_API_KEY",
            "KPUBDATA_KOSIS_API_KEY",
            "KPUBDATA_LOFIN_API_KEY",
            "KPUBDATA_LOCALDATA_API_KEY",
        )
    ):
        pytest.skip("No API keys set")
    return Client.from_env()
