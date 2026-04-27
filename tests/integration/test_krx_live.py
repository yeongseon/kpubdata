from __future__ import annotations

import os

import pytest

from kpubdata.client import Client
from kpubdata.core.models import RecordBatch


@pytest.fixture(scope="module")
def require_krx_integration() -> None:
    if os.environ.get("KPUBDATA_KRX_INTEGRATION") != "1":
        pytest.skip("Set KPUBDATA_KRX_INTEGRATION=1 to run live KRX integration tests")


@pytest.fixture(scope="module")
def krx_client(require_krx_integration: None) -> Client:
    return Client()


@pytest.mark.integration
def test_kospi_index_live_returns_rows(krx_client: Client) -> None:
    dataset = krx_client.dataset("krx.kospi_index")

    result = dataset.list(start_date="20240102", end_date="20240108")

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0


@pytest.mark.integration
def test_investor_flow_live_returns_rows(krx_client: Client) -> None:
    dataset = krx_client.dataset("krx.investor_flow")

    result = dataset.list(start_date="20240102", end_date="20240108")

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0


@pytest.mark.integration
def test_market_valuation_live_returns_rows(krx_client: Client) -> None:
    dataset = krx_client.dataset("krx.market_valuation")

    result = dataset.list(start_date="20240102", end_date="20240108")

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0
