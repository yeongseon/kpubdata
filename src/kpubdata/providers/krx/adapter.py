"""KRX adapter scaffold.

This provider is intentionally authless: KRX dataset implementations use the
optional ``pykrx`` backend rather than a per-user API key, so the adapter opts
out of the default provider-key convention via ``requires_api_key = False``.
The backend import must remain lazy because issue #199 only scaffolds the
provider contract; concrete dataset methods land in issue #200.
"""

from __future__ import annotations

import importlib
import logging
from collections.abc import Sequence

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.exceptions import ConfigError, DatasetNotFoundError
from kpubdata.providers._common import build_schema_from_metadata, load_catalogue
from kpubdata.transport.http import HttpTransport, TransportConfig

logger = logging.getLogger("kpubdata.provider.krx")


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
            if needle in dataset.id.casefold() or needle in dataset.name.casefold()
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
        _ = query
        _ = self.get_dataset(dataset.dataset_key)
        raise DatasetNotFoundError(
            f"Dataset not found: {dataset.id}",
            provider="krx",
            dataset_id=dataset.id,
        )

    def get_schema(self, dataset: DatasetRef) -> SchemaDescriptor | None:
        return build_schema_from_metadata(dataset)

    def call_raw(self, dataset: DatasetRef, operation: str, params: dict[str, object]) -> object:
        _ = operation
        _ = params
        _ = self.get_dataset(dataset.dataset_key)
        raise DatasetNotFoundError(
            f"Dataset not found: {dataset.id}",
            provider="krx",
            dataset_id=dataset.id,
        )

    def _load_default_catalogue(self) -> tuple[DatasetRef, ...]:
        return load_catalogue("kpubdata.providers.krx", "krx")

    def _import_pykrx(self) -> object:
        return importlib.import_module("pykrx")

    def _load_pykrx(self) -> object:
        try:
            return self._import_pykrx()
        except ImportError as exc:
            raise ConfigError("Install kpubdata[krx] to enable KRX provider") from exc
