from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pytest

from kpubdata import Client
from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.providers.krx.adapter import KrxAdapter
from kpubdata.providers.manifest import BUILTIN_PROVIDERS
from tests.contract.provider_adapter import ProviderAdapterContract


def _index_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "시가": [2650.0],
            "고가": [2675.0],
            "저가": [2641.0],
            "종가": [2669.0],
            "거래량": [410000000],
            "거래대금": [8100000000000],
            "상장시가총액": [2100000000000],
        },
        index=pd.DatetimeIndex(["2024-01-02"], name="날짜"),
    )


def _build_adapter() -> KrxAdapter:
    adapter = KrxAdapter(config=KPubDataConfig())
    adapter._pykrx = SimpleNamespace(
        stock=SimpleNamespace(
            get_index_ohlcv=lambda *_args: _index_frame(),
            get_market_trading_value_by_date=lambda *_args, **_kwargs: pd.DataFrame(
                {
                    "개인": [100],
                    "기관합계": [50],
                    "외국인합계": [30],
                    "기타법인": [20],
                    "전체": [0],
                },
                index=pd.DatetimeIndex(["2024-01-02"], name="날짜"),
            ),
            get_market_fundamental=lambda *_args, **_kwargs: pd.DataFrame(
                {
                    "PER": [150.0],
                    "PBR": [1.5],
                    "DIV": [3.0],
                    "EPS": [1500.0],
                    "BPS": [6000.0],
                },
                index=pd.DatetimeIndex(["2024-01-02"], name="날짜"),
            ),
        )
    )
    return adapter


class TestKrxAdapterContract(ProviderAdapterContract):
    @pytest.fixture()
    def adapter(self) -> ProviderAdapter:
        return _build_adapter()

    @pytest.fixture()
    def valid_dataset_key(self) -> str:
        return "kospi_index"

    @pytest.fixture()
    def invalid_dataset_key(self) -> str:
        return "nonexistent_dataset_key_xyz"

    @pytest.fixture()
    def sample_dataset(self, adapter: ProviderAdapter) -> DatasetRef:
        return adapter.get_dataset("kospi_index")

    @pytest.fixture()
    def sample_query(self) -> Query:
        return Query(start_date="20240102", end_date="20240102")

    @pytest.fixture()
    def raw_operation(self) -> tuple[str, dict[str, object]]:
        return ("list", {"start_date": "20240102", "end_date": "20240102"})


def test_krx_provider_is_registered_in_builtin_manifest() -> None:
    assert ("krx", "kpubdata.providers.krx", "KrxAdapter") in BUILTIN_PROVIDERS


def test_client_from_env_lists_three_krx_datasets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KPUBDATA_KRX_API_KEY", raising=False)
    client = Client.from_env()

    datasets = client.datasets.list(provider="krx")

    assert [dataset.id for dataset in datasets] == [
        "krx.kospi_index",
        "krx.investor_flow",
        "krx.market_valuation",
    ]


def test_client_search_finds_krx_datasets_by_description() -> None:
    client = Client()

    matches = client.datasets.search("investor", provider="krx")

    assert any(dataset.id == "krx.investor_flow" for dataset in matches)


def test_client_can_resolve_krx_schema() -> None:
    client = Client()
    schema = client.dataset("krx.market_valuation").schema()

    assert schema is not None
    assert [field.name for field in schema.fields] == [
        "date",
        "market",
        "per",
        "pbr",
        "dividend_yield",
        "eps",
        "bps",
    ]


def test_krx_adapter_declares_authless_provider() -> None:
    assert KrxAdapter(config=KPubDataConfig()).requires_api_key is False


def test_client_iter_authenticated_providers_excludes_krx_and_includes_bok() -> None:
    client = Client()

    provider_names = {adapter.name for adapter in client.iter_authenticated_providers()}

    assert "krx" not in provider_names
    assert "bok" in provider_names
