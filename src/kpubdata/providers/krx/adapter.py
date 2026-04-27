from __future__ import annotations

import importlib
import logging
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime
from typing import Protocol, cast

import pandas as pd

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.exceptions import (
    ConfigError,
    DatasetNotFoundError,
    InvalidRequestError,
    ProviderResponseError,
)
from kpubdata.providers._common import build_schema_from_metadata, load_catalogue
from kpubdata.transport.http import HttpTransport, TransportConfig

logger = logging.getLogger("kpubdata.provider.krx")

_INVESTOR_LABELS: tuple[tuple[str, str], ...] = (
    ("개인", "개인"),
    ("기관합계", "기관"),
    ("외국인합계", "외국인"),
    ("기타법인", "기타"),
)


class _StockNamespace(Protocol):
    def get_index_ohlcv(self, start_date: str, end_date: str, ticker: str) -> pd.DataFrame: ...

    def get_index_ohlcv_by_date(
        self,
        start_date: str,
        end_date: str,
        ticker: str,
        *,
        name_display: bool = True,
    ) -> pd.DataFrame: ...

    def get_market_trading_value_by_date(
        self,
        start_date: str,
        end_date: str,
        ticker: str,
        *,
        on: str = "순매수",
        etf: bool = False,
        etn: bool = False,
        elw: bool = False,
        detail: bool = False,
        freq: str = "d",
    ) -> pd.DataFrame: ...

    def get_market_fundamental(
        self,
        start_date: str,
        end_date: str,
        *,
        market: str,
    ) -> pd.DataFrame: ...

    def get_market_fundamental_by_ticker(
        self,
        date: str,
        market: str = "KOSPI",
    ) -> pd.DataFrame: ...


class _PykrxNamespace(Protocol):
    stock: _StockNamespace


class KrxAdapter:
    requires_api_key: bool = False

    def __init__(
        self,
        *,
        config: KPubDataConfig | None = None,
        transport: HttpTransport | None = None,
        catalogue: Sequence[DatasetRef] | None = None,
    ) -> None:
        self._config: KPubDataConfig = config or KPubDataConfig()
        transport_config = TransportConfig(
            timeout=self._config.timeout,
            max_retries=self._config.max_retries,
        )
        self._transport: HttpTransport = transport or HttpTransport(transport_config)
        self._pykrx: _PykrxNamespace | None = None

        datasets = tuple(catalogue) if catalogue is not None else self._load_default_catalogue()
        self._datasets: tuple[DatasetRef, ...] = datasets
        self._datasets_by_key: dict[str, DatasetRef] = {
            dataset.dataset_key: dataset for dataset in self._datasets
        }

    @property
    def name(self) -> str:
        return "krx"

    def list_datasets(self) -> list[DatasetRef]:
        return list(self._datasets)

    def search_datasets(self, text: str) -> list[DatasetRef]:
        needle = text.casefold()
        return [
            dataset
            for dataset in self._datasets
            if needle in dataset.id.casefold()
            or needle in dataset.name.casefold()
            or (dataset.description is not None and needle in dataset.description.casefold())
            or any(needle in tag.casefold() for tag in dataset.tags)
        ]

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        dataset = self._datasets_by_key.get(dataset_key)
        if dataset is not None:
            return dataset

        logger.debug(
            "KRX dataset not found",
            extra={"dataset_id": f"krx.{dataset_key}", "provider": "krx"},
        )
        raise DatasetNotFoundError(
            f"Dataset not found: krx.{dataset_key}",
            provider="krx",
            dataset_id=f"krx.{dataset_key}",
        )

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        resolved_dataset = self.get_dataset(dataset.dataset_key)
        frame = self._dispatch_dataframe(
            resolved_dataset,
            query,
            self._dataset_handlers(),
        )
        if frame.empty:
            return RecordBatch(items=[], dataset=resolved_dataset, total_count=0, next_page=None)

        normalize = self._dataset_normalizers()[resolved_dataset.dataset_key]
        items = normalize(frame, resolved_dataset, query)
        return RecordBatch(
            items=items,
            dataset=resolved_dataset,
            total_count=len(items),
            next_page=None,
            raw=self._frame_to_records(frame),
        )

    def get_schema(self, dataset: DatasetRef) -> SchemaDescriptor | None:
        return build_schema_from_metadata(dataset)

    def call_raw(self, dataset: DatasetRef, operation: str, params: dict[str, object]) -> object:
        _ = operation
        resolved_dataset = self.get_dataset(dataset.dataset_key)
        frame = self._dispatch_dataframe(
            resolved_dataset,
            self._query_from_params(params),
            self._dataset_raw_handlers(),
        )
        if frame.empty:
            return []
        return self._frame_to_records(frame)

    def _dataset_handlers(self) -> Mapping[str, Callable[[DatasetRef, Query], pd.DataFrame]]:
        return {
            "kospi_index": self._fetch_kospi_index,
            "investor_flow": self._fetch_investor_flow,
            "market_valuation": self._fetch_market_valuation,
        }

    def _dataset_raw_handlers(self) -> Mapping[str, Callable[[DatasetRef, Query], pd.DataFrame]]:
        return {
            "kospi_index": self._fetch_kospi_index,
            "investor_flow": self._fetch_investor_flow_raw,
            "market_valuation": self._fetch_market_valuation,
        }

    def _dataset_normalizers(
        self,
    ) -> Mapping[str, Callable[[pd.DataFrame, DatasetRef, Query], list[dict[str, object]]]]:
        return {
            "kospi_index": self._normalize_kospi_index,
            "investor_flow": self._normalize_investor_flow,
            "market_valuation": self._normalize_market_valuation,
        }

    def _dispatch_dataframe(
        self,
        dataset: DatasetRef,
        query: Query,
        handlers: Mapping[str, Callable[[DatasetRef, Query], pd.DataFrame]],
    ) -> pd.DataFrame:
        handler = handlers.get(dataset.dataset_key)
        if handler is None:
            raise DatasetNotFoundError(
                f"Dataset not found: {dataset.id}",
                provider="krx",
                dataset_id=dataset.id,
            )

        try:
            return handler(dataset, query)
        except (InvalidRequestError, ProviderResponseError):
            raise
        except Exception as exc:
            raise ProviderResponseError(
                f"KRX backend error: {exc}",
                provider="krx",
                dataset_id=dataset.id,
            ) from exc

    def _fetch_kospi_index(self, dataset: DatasetRef, query: Query) -> pd.DataFrame:
        stock = self._stock_api()
        start_date, end_date = self._require_date_range(dataset, query)
        ticker = self._resolve_string_param(query, "ticker") or self._metadata_default(
            dataset, "ticker"
        )
        try:
            return stock.get_index_ohlcv(start_date, end_date, ticker)
        except Exception:
            fallback = getattr(stock, "get_index_ohlcv_by_date", None)
            if callable(fallback):
                typed_fallback = cast(Callable[..., pd.DataFrame], fallback)
                return typed_fallback(start_date, end_date, ticker, name_display=False)
            raise

    def _fetch_investor_flow(self, dataset: DatasetRef, query: Query) -> pd.DataFrame:
        stock = self._stock_api()
        start_date, end_date = self._require_date_range(dataset, query)
        market = self._resolve_string_param(query, "market") or self._metadata_default(
            dataset, "market"
        )
        buy_frame = stock.get_market_trading_value_by_date(start_date, end_date, market, on="매수")
        sell_frame = stock.get_market_trading_value_by_date(start_date, end_date, market, on="매도")
        net_frame = stock.get_market_trading_value_by_date(
            start_date, end_date, market, on="순매수"
        )

        if buy_frame.empty or sell_frame.empty or net_frame.empty:
            return pd.DataFrame()

        return self._combine_investor_frames(buy_frame, sell_frame, net_frame)

    def _fetch_investor_flow_raw(self, dataset: DatasetRef, query: Query) -> pd.DataFrame:
        stock = self._stock_api()
        start_date, end_date = self._require_date_range(dataset, query)
        market = self._resolve_string_param(query, "market") or self._metadata_default(
            dataset, "market"
        )
        on = self._resolve_string_param(query, "on") or "순매수"
        return stock.get_market_trading_value_by_date(start_date, end_date, market, on=on)

    def _fetch_market_valuation(self, dataset: DatasetRef, query: Query) -> pd.DataFrame:
        stock = self._stock_api()
        start_date, end_date = self._require_date_range(dataset, query)
        market = self._resolve_string_param(query, "market") or self._metadata_default(
            dataset, "market"
        )

        try:
            frame = stock.get_market_fundamental(start_date, end_date, market=market)
        except TypeError:
            frame = self._fetch_market_valuation_by_day(stock, start_date, end_date, market)

        if frame.empty:
            return pd.DataFrame()

        if self._has_columns(frame, "PER", "PBR", "DIV", "EPS", "BPS"):
            return self._aggregate_market_valuation_frame(frame)

        return frame

    def _fetch_market_valuation_by_day(
        self,
        stock: _StockNamespace,
        start_date: str,
        end_date: str,
        market: str,
    ) -> pd.DataFrame:
        rows: list[dict[str, object]] = []
        for day in pd.date_range(
            start=pd.Timestamp(start_date), end=pd.Timestamp(end_date), freq="D"
        ):
            day_string = day.strftime("%Y%m%d")
            frame = stock.get_market_fundamental_by_ticker(day_string, market=market)
            if frame.empty or not self._has_columns(frame, "PER", "PBR", "DIV", "EPS", "BPS"):
                continue
            numeric = frame.loc[:, ["PER", "PBR", "DIV", "EPS", "BPS"]]
            if numeric.eq(0).all(axis=None):
                continue
            rows.append(
                {
                    "date": day,
                    "PER": float(numeric["PER"].mean()),
                    "PBR": float(numeric["PBR"].mean()),
                    "DIV": float(numeric["DIV"].mean()),
                    "EPS": float(numeric["EPS"].mean()),
                    "BPS": float(numeric["BPS"].mean()),
                }
            )
        if not rows:
            return pd.DataFrame()
        frame = pd.DataFrame(rows)
        return frame.set_index("date")

    def _combine_investor_frames(
        self,
        buy_frame: pd.DataFrame,
        sell_frame: pd.DataFrame,
        net_frame: pd.DataFrame,
    ) -> pd.DataFrame:
        rows: list[dict[str, object]] = []
        for day in buy_frame.index:
            for raw_label, normalized_label in _INVESTOR_LABELS:
                if (
                    raw_label not in buy_frame.columns
                    or raw_label not in sell_frame.columns
                    or raw_label not in net_frame.columns
                ):
                    continue
                rows.append(
                    {
                        "date": day,
                        "investor_type": normalized_label,
                        "buy_value": buy_frame.at[day, raw_label],
                        "sell_value": sell_frame.at[day, raw_label],
                        "net_value": net_frame.at[day, raw_label],
                    }
                )
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows)

    def _aggregate_market_valuation_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        if isinstance(frame.index, pd.DatetimeIndex):
            return frame
        if "date" in frame.columns:
            return frame.set_index("date")
        return frame

    def _normalize_kospi_index(
        self,
        frame: pd.DataFrame,
        dataset: DatasetRef,
        query: Query,
    ) -> list[dict[str, object]]:
        _ = dataset, query
        records = self._frame_to_records(frame)
        return [
            {
                "date": self._format_date(record.get("날짜")),
                "open": record.get("시가"),
                "high": record.get("고가"),
                "low": record.get("저가"),
                "close": record.get("종가"),
                "volume": record.get("거래량"),
                "trading_value": record.get("거래대금"),
                "market_cap": record.get("상장시가총액"),
            }
            for record in records
        ]

    def _normalize_investor_flow(
        self,
        frame: pd.DataFrame,
        dataset: DatasetRef,
        query: Query,
    ) -> list[dict[str, object]]:
        market = self._resolve_string_param(query, "market") or self._metadata_default(
            dataset, "market"
        )
        records = self._frame_to_records(frame)
        return [
            {
                "date": self._format_date(record.get("date")),
                "market": market,
                "investor_type": record.get("investor_type"),
                "buy_value": record.get("buy_value"),
                "sell_value": record.get("sell_value"),
                "net_value": record.get("net_value"),
            }
            for record in records
        ]

    def _normalize_market_valuation(
        self,
        frame: pd.DataFrame,
        dataset: DatasetRef,
        query: Query,
    ) -> list[dict[str, object]]:
        market = self._resolve_string_param(query, "market") or self._metadata_default(
            dataset, "market"
        )
        records = self._frame_to_records(frame)
        return [
            {
                "date": self._format_date(record.get("date") or record.get("날짜")),
                "market": market,
                "per": record.get("PER"),
                "pbr": record.get("PBR"),
                "dividend_yield": record.get("DIV"),
                "eps": record.get("EPS"),
                "bps": record.get("BPS"),
            }
            for record in records
        ]

    def _load_default_catalogue(self) -> tuple[DatasetRef, ...]:
        return load_catalogue("kpubdata.providers.krx", "krx")

    def _import_pykrx(self) -> object:
        return importlib.import_module("pykrx")

    def _load_pykrx(self) -> _PykrxNamespace:
        if self._pykrx is not None:
            return self._pykrx
        try:
            module = self._import_pykrx()
        except ImportError as exc:
            raise ConfigError("Install kpubdata[krx] to enable KRX provider") from exc
        self._pykrx = cast(_PykrxNamespace, module)
        return self._pykrx

    def _stock_api(self) -> _StockNamespace:
        return self._load_pykrx().stock

    def _require_date_range(self, dataset: DatasetRef, query: Query) -> tuple[str, str]:
        start_date = query.start_date or self._resolve_string_param(query, "start_date")
        end_date = query.end_date or self._resolve_string_param(query, "end_date")
        if start_date is None or end_date is None:
            raise InvalidRequestError(
                "KRX queries require start_date and end_date",
                provider="krx",
                dataset_id=dataset.id,
            )
        return start_date, end_date

    @staticmethod
    def _query_from_params(params: Mapping[str, object]) -> Query:
        query = Query()
        for key, value in params.items():
            if key == "start_date" and isinstance(value, str):
                query.start_date = value
            elif key == "end_date" and isinstance(value, str):
                query.end_date = value
            else:
                query.filters[key] = value
        return query

    @staticmethod
    def _resolve_string_param(query: Query, key: str) -> str | None:
        if key in query.filters:
            filter_value = query.filters[key]
            if isinstance(filter_value, str) and filter_value:
                return filter_value
        if key in query.extra:
            extra_value = query.extra[key]
            if isinstance(extra_value, str) and extra_value:
                return extra_value
        return None

    @staticmethod
    def _metadata_default(dataset: DatasetRef, key: str) -> str:
        raw_value = dataset.raw_metadata.get("default_query_params")
        if isinstance(raw_value, Mapping):
            value = raw_value.get(key)
            if isinstance(value, str) and value:
                return value
        raise ProviderResponseError(
            f"Dataset metadata missing default_query_params.{key}",
            provider="krx",
            dataset_id=dataset.id,
        )

    @staticmethod
    def _has_columns(frame: pd.DataFrame, *columns: str) -> bool:
        return all(column in frame.columns for column in columns)

    def _frame_to_records(self, frame: pd.DataFrame) -> list[dict[str, object]]:
        reset_frame = frame.reset_index()
        records = cast(list[dict[str, object]], reset_frame.to_dict(orient="records"))
        return [
            {key: self._to_python_value(value) for key, value in record.items()}
            for record in records
        ]

    def _to_python_value(self, value: object) -> object:
        if isinstance(value, pd.Timestamp):
            return value.strftime("%Y-%m-%d")
        return value

    @staticmethod
    def _format_date(value: object) -> str:
        if isinstance(value, str):
            if len(value) == 8 and value.isdigit():
                return datetime.strptime(value, "%Y%m%d").strftime("%Y-%m-%d")
            return value
        if isinstance(value, pd.Timestamp):
            return value.strftime("%Y-%m-%d")
        raise ProviderResponseError(f"Invalid KRX date value: {value!r}", provider="krx")


__all__ = ["KrxAdapter"]
