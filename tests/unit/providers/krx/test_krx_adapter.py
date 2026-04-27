from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import Query
from kpubdata.exceptions import ConfigError, InvalidRequestError, ProviderResponseError
from kpubdata.providers.krx.adapter import KrxAdapter


class _ExposedKrxAdapter(KrxAdapter):
    def load_pykrx_for_test(self) -> object:
        return self._load_pykrx()


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parents[3] / "fixtures" / "krx" / name


def _load_snapshot(name: str) -> list[dict[str, object]]:
    return json.loads(_fixture_path(name).read_text(encoding="utf-8"))


def _build_adapter() -> KrxAdapter:
    return KrxAdapter(config=KPubDataConfig())


def _set_pykrx(adapter: KrxAdapter, **stock_methods: object) -> None:
    adapter._pykrx = SimpleNamespace(stock=SimpleNamespace(**stock_methods))


def _kospi_index_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "시가": [2650.0, 2661.0, 2644.0, 2632.0, 2629.0],
            "고가": [2675.0, 2678.0, 2662.0, 2644.0, 2665.0],
            "저가": [2641.0, 2649.0, 2620.0, 2614.0, 2622.0],
            "종가": [2669.0, 2651.0, 2634.0, 2620.0, 2660.0],
            "거래량": [410000000, 420000000, 430000000, 440000000, 450000000],
            "거래대금": [8100000000000, 8200000000000, 8300000000000, 8400000000000, 8500000000000],
            "상장시가총액": [
                2100000000000,
                2110000000000,
                2120000000000,
                2130000000000,
                2140000000000,
            ],
        },
        index=pd.DatetimeIndex(
            [
                "2024-01-02",
                "2024-01-03",
                "2024-01-04",
                "2024-01-05",
                "2024-01-08",
            ],
            name="날짜",
        ),
    )


def _investor_frame(multiplier: int) -> pd.DataFrame:
    return (
        pd.DataFrame(
            {
                "개인": [100, 110, 120, 130, 140],
                "기관합계": [50, 55, 60, 65, 70],
                "외국인합계": [30, 35, 40, 45, 50],
                "기타법인": [20, 25, 30, 35, 40],
                "전체": [0, 0, 0, 0, 0],
            },
            index=pd.DatetimeIndex(
                [
                    "2024-01-02",
                    "2024-01-03",
                    "2024-01-04",
                    "2024-01-05",
                    "2024-01-08",
                ],
                name="날짜",
            ),
        )
        * multiplier
    )


def _market_fundamental_frame(day: str) -> pd.DataFrame:
    rows = {
        "20240102": [(100.0, 1.0, 2.0, 1000, 5000), (200.0, 2.0, 4.0, 2000, 7000)],
        "20240103": [(110.0, 1.1, 2.2, 1100, 5100), (210.0, 2.1, 4.2, 2100, 7100)],
        "20240104": [(120.0, 1.2, 2.4, 1200, 5200), (220.0, 2.2, 4.4, 2200, 7200)],
        "20240105": [(130.0, 1.3, 2.6, 1300, 5300), (230.0, 2.3, 4.6, 2300, 7300)],
        "20240108": [(140.0, 1.4, 2.8, 1400, 5400), (240.0, 2.4, 4.8, 2400, 7400)],
    }
    day_rows = rows[day]
    return pd.DataFrame(
        {
            "PER": [row[0] for row in day_rows],
            "PBR": [row[1] for row in day_rows],
            "DIV": [row[2] for row in day_rows],
            "EPS": [row[3] for row in day_rows],
            "BPS": [row[4] for row in day_rows],
            "DPS": [100, 200],
        },
        index=pd.Index(["000001", "000002"], name="티커"),
    )


def test_catalogue_includes_three_krx_datasets() -> None:
    adapter = _build_adapter()

    datasets = adapter.list_datasets()

    assert [dataset.id for dataset in datasets] == [
        "krx.kospi_index",
        "krx.investor_flow",
        "krx.market_valuation",
    ]
    assert all(
        dataset.description is not None and "KRX" in dataset.description for dataset in datasets
    )


def test_query_records_kospi_index_normalizes_snapshot() -> None:
    adapter = _build_adapter()
    dataset = adapter.get_dataset("kospi_index")
    calls: list[tuple[str, str, str]] = []

    def _get_index_ohlcv(start_date: str, end_date: str, ticker: str) -> pd.DataFrame:
        calls.append((start_date, end_date, ticker))
        return _kospi_index_frame()

    _set_pykrx(adapter, get_index_ohlcv=_get_index_ohlcv)

    batch = adapter.query_records(dataset, Query(start_date="20240102", end_date="20240108"))

    assert batch.items == _load_snapshot("kospi_index_5days.json")
    assert batch.total_count == 5
    assert calls == [("20240102", "20240108", "1001")]


def test_query_records_kospi_index_supports_custom_ticker_filter() -> None:
    adapter = _build_adapter()
    dataset = adapter.get_dataset("kospi_index")
    tickers: list[str] = []

    def _get_index_ohlcv(start_date: str, end_date: str, ticker: str) -> pd.DataFrame:
        _ = start_date, end_date
        tickers.append(ticker)
        return _kospi_index_frame()

    _set_pykrx(adapter, get_index_ohlcv=_get_index_ohlcv)

    _ = adapter.query_records(
        dataset,
        Query(start_date="20240102", end_date="20240108", filters={"ticker": "2001"}),
    )

    assert tickers == ["2001"]


def test_call_raw_kospi_index_returns_raw_dataframe_records() -> None:
    adapter = _build_adapter()
    dataset = adapter.get_dataset("kospi_index")
    _set_pykrx(adapter, get_index_ohlcv=lambda *_args: _kospi_index_frame())

    payload = adapter.call_raw(
        dataset,
        "list",
        {"start_date": "20240102", "end_date": "20240108"},
    )

    assert payload == [
        {
            "날짜": "2024-01-02",
            "시가": 2650.0,
            "고가": 2675.0,
            "저가": 2641.0,
            "종가": 2669.0,
            "거래량": 410000000,
            "거래대금": 8100000000000,
            "상장시가총액": 2100000000000,
        },
        {
            "날짜": "2024-01-03",
            "시가": 2661.0,
            "고가": 2678.0,
            "저가": 2649.0,
            "종가": 2651.0,
            "거래량": 420000000,
            "거래대금": 8200000000000,
            "상장시가총액": 2110000000000,
        },
        {
            "날짜": "2024-01-04",
            "시가": 2644.0,
            "고가": 2662.0,
            "저가": 2620.0,
            "종가": 2634.0,
            "거래량": 430000000,
            "거래대금": 8300000000000,
            "상장시가총액": 2120000000000,
        },
        {
            "날짜": "2024-01-05",
            "시가": 2632.0,
            "고가": 2644.0,
            "저가": 2614.0,
            "종가": 2620.0,
            "거래량": 440000000,
            "거래대금": 8400000000000,
            "상장시가총액": 2130000000000,
        },
        {
            "날짜": "2024-01-08",
            "시가": 2629.0,
            "고가": 2665.0,
            "저가": 2622.0,
            "종가": 2660.0,
            "거래량": 450000000,
            "거래대금": 8500000000000,
            "상장시가총액": 2140000000000,
        },
    ]


def test_query_records_investor_flow_normalizes_snapshot() -> None:
    adapter = _build_adapter()
    dataset = adapter.get_dataset("investor_flow")
    calls: list[tuple[str, str, str, str]] = []

    def _get_market_trading_value_by_date(
        start_date: str,
        end_date: str,
        market: str,
        *,
        on: str = "순매수",
        **_kwargs: object,
    ) -> pd.DataFrame:
        calls.append((start_date, end_date, market, on))
        frames = {
            "매수": _investor_frame(10),
            "매도": _investor_frame(6),
            "순매수": _investor_frame(4),
        }
        return frames[on]

    _set_pykrx(adapter, get_market_trading_value_by_date=_get_market_trading_value_by_date)

    batch = adapter.query_records(dataset, Query(start_date="20240102", end_date="20240108"))

    assert batch.items == _load_snapshot("investor_flow_5days.json")
    assert batch.total_count == 20
    assert calls == [
        ("20240102", "20240108", "KOSPI", "매수"),
        ("20240102", "20240108", "KOSPI", "매도"),
        ("20240102", "20240108", "KOSPI", "순매수"),
    ]


def test_query_records_investor_flow_supports_custom_market_filter() -> None:
    adapter = _build_adapter()
    dataset = adapter.get_dataset("investor_flow")
    markets: list[str] = []

    def _get_market_trading_value_by_date(
        start_date: str,
        end_date: str,
        market: str,
        *,
        on: str = "순매수",
        **_kwargs: object,
    ) -> pd.DataFrame:
        _ = start_date, end_date, on
        markets.append(market)
        return _investor_frame(1)

    _set_pykrx(adapter, get_market_trading_value_by_date=_get_market_trading_value_by_date)

    _ = adapter.query_records(
        dataset,
        Query(start_date="20240102", end_date="20240108", filters={"market": "KOSDAQ"}),
    )

    assert markets == ["KOSDAQ", "KOSDAQ", "KOSDAQ"]


def test_query_records_market_valuation_normalizes_snapshot() -> None:
    adapter = _build_adapter()
    dataset = adapter.get_dataset("market_valuation")
    days_called: list[str] = []

    def _unsupported_market_fundamental(*_args: object, **_kwargs: object) -> pd.DataFrame:
        raise TypeError("range market fundamental is unavailable")

    def _get_market_fundamental_by_ticker(date: str, market: str = "KOSPI") -> pd.DataFrame:
        _ = market
        days_called.append(date)
        if date in {"20240106", "20240107"}:
            return pd.DataFrame(columns=["PER", "PBR", "DIV", "EPS", "BPS", "DPS"])
        return _market_fundamental_frame(date)

    _set_pykrx(
        adapter,
        get_market_fundamental=_unsupported_market_fundamental,
        get_market_fundamental_by_ticker=_get_market_fundamental_by_ticker,
    )

    batch = adapter.query_records(dataset, Query(start_date="20240102", end_date="20240108"))

    assert batch.items == _load_snapshot("market_valuation_5days.json")
    assert batch.total_count == 5
    assert days_called == [
        "20240102",
        "20240103",
        "20240104",
        "20240105",
        "20240106",
        "20240107",
        "20240108",
    ]


@pytest.mark.parametrize(
    ("dataset_key", "methods"),
    [
        (
            "kospi_index",
            {"get_index_ohlcv": lambda *_args: pd.DataFrame()},
        ),
        (
            "investor_flow",
            {"get_market_trading_value_by_date": lambda *_args, **_kwargs: pd.DataFrame()},
        ),
        (
            "market_valuation",
            {"get_market_fundamental": lambda *_args, **_kwargs: pd.DataFrame()},
        ),
    ],
)
def test_empty_dataframe_returns_empty_record_batch(
    dataset_key: str,
    methods: dict[str, object],
) -> None:
    adapter = _build_adapter()
    dataset = adapter.get_dataset(dataset_key)
    _set_pykrx(adapter, **methods)

    batch = adapter.query_records(dataset, Query(start_date="20240102", end_date="20240108"))

    assert batch.items == []
    assert batch.total_count == 0
    assert batch.next_page is None


@pytest.mark.parametrize(
    ("dataset_key", "methods"),
    [
        (
            "kospi_index",
            {"get_index_ohlcv": lambda *_args: (_ for _ in ()).throw(RuntimeError("boom"))},
        ),
        (
            "investor_flow",
            {
                "get_market_trading_value_by_date": lambda *_args, **_kwargs: (_ for _ in ()).throw(
                    RuntimeError("boom")
                )
            },
        ),
        (
            "market_valuation",
            {
                "get_market_fundamental": lambda *_args, **_kwargs: (_ for _ in ()).throw(
                    RuntimeError("boom")
                )
            },
        ),
    ],
)
def test_pykrx_exception_is_wrapped_with_cause(
    dataset_key: str,
    methods: dict[str, object],
) -> None:
    adapter = _build_adapter()
    dataset = adapter.get_dataset(dataset_key)
    _set_pykrx(adapter, **methods)

    with pytest.raises(ProviderResponseError, match="KRX backend error: boom") as excinfo:
        _ = adapter.query_records(dataset, Query(start_date="20240102", end_date="20240108"))

    assert excinfo.value.provider == "krx"
    assert excinfo.value.dataset_id == dataset.id
    assert isinstance(excinfo.value.__cause__, RuntimeError)


def test_get_schema_builds_from_catalogue_metadata() -> None:
    adapter = _build_adapter()
    dataset = adapter.get_dataset("market_valuation")

    schema = adapter.get_schema(dataset)

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


def test_query_records_requires_start_and_end_dates() -> None:
    adapter = _build_adapter()
    dataset = adapter.get_dataset("kospi_index")

    with pytest.raises(InvalidRequestError, match="start_date and end_date"):
        _ = adapter.query_records(dataset, Query())


def test_load_pykrx_raises_install_hint_when_dependency_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = _ExposedKrxAdapter(config=KPubDataConfig())

    def _raise_import_error() -> SimpleNamespace:
        raise ImportError("pykrx is unavailable")

    monkeypatch.setattr(adapter, "_import_pykrx", _raise_import_error)

    with pytest.raises(ConfigError, match=r"Install kpubdata\[krx\] to enable KRX provider"):
        _ = adapter.load_pykrx_for_test()


def test_load_pykrx_returns_imported_module(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = _ExposedKrxAdapter(config=KPubDataConfig())
    pykrx_module = SimpleNamespace(stock=SimpleNamespace())

    def _import_module(name: str) -> SimpleNamespace:
        assert name == "pykrx"
        return pykrx_module

    monkeypatch.setattr(importlib, "import_module", _import_module)

    assert adapter.load_pykrx_for_test() is pykrx_module


def test_adapter_is_constructible_without_krx_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KPUBDATA_KRX_API_KEY", raising=False)

    adapter = KrxAdapter(config=KPubDataConfig.from_env())

    assert adapter.name == "krx"
    assert adapter.requires_api_key is False


def test_adapter_construction_does_not_import_pykrx(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delitem(sys.modules, "pykrx", raising=False)

    _ = KrxAdapter(config=KPubDataConfig())

    assert "pykrx" not in sys.modules
