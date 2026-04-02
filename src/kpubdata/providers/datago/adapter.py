"""Data.go.kr adapter with curated dataset catalogue."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from importlib.resources import files
from types import MappingProxyType
from typing import cast

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.core.representation import Representation
from kpubdata.exceptions import DatasetNotFoundError
from kpubdata.transport.http import HttpTransport, TransportConfig


class DataGoAdapter:
    """Adapter for data.go.kr (공공데이터포털).

    Provides a curated catalogue of supported datasets from the
    apis.data.go.kr endpoint family.
    """

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
        """Return canonical provider key."""

        return "datago"

    def list_datasets(self) -> list[DatasetRef]:
        """List datasets available from data.go.kr."""

        return list(self._datasets)

    def search_datasets(self, text: str) -> list[DatasetRef]:
        """Search datasets available from data.go.kr."""

        needle = text.casefold()
        return [
            dataset
            for dataset in self._datasets
            if needle in dataset.id.casefold() or needle in dataset.name.casefold()
        ]

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        """Resolve provider-local dataset key for data.go.kr."""

        dataset = self._datasets_by_key.get(dataset_key)
        if dataset is not None:
            return dataset

        raise DatasetNotFoundError(
            f"Dataset not found: datago.{dataset_key}",
            provider="datago",
            dataset_id=f"datago.{dataset_key}",
        )

    def query_records(self, _dataset: DatasetRef, _query: Query) -> RecordBatch:
        """Query records from a data.go.kr dataset."""

        raise NotImplementedError("TODO: implement datago query_records")

    def get_record(self, _dataset: DatasetRef, _key: dict[str, object]) -> dict[str, object] | None:
        """Get a single record from a data.go.kr dataset."""

        raise NotImplementedError("TODO: implement datago get_record")

    def get_schema(self, _dataset: DatasetRef) -> SchemaDescriptor | None:
        """Get schema metadata for a data.go.kr dataset."""

        raise NotImplementedError("TODO: implement datago get_schema")

    def call_raw(self, _dataset: DatasetRef, _operation: str, _params: dict[str, object]) -> object:
        """Call provider-native data.go.kr API operation."""

        raise NotImplementedError("TODO: implement datago call_raw")

    def _require_api_key(self) -> str:
        return self._config.require_provider_key("datago")

    @staticmethod
    def _load_default_catalogue() -> tuple[DatasetRef, ...]:
        package_files = files("kpubdata.providers.datago")
        catalogue_text = package_files.joinpath("catalogue.json").read_text(encoding="utf-8")
        parsed_catalogue = cast(object, json.loads(catalogue_text))
        if not isinstance(parsed_catalogue, list):
            msg = "datago catalogue.json must contain a top-level JSON array"
            raise ValueError(msg)

        catalogue_entries = cast(list[object], parsed_catalogue)
        datasets: list[DatasetRef] = []
        for entry_object in catalogue_entries:
            if not isinstance(entry_object, dict):
                msg = "datago catalogue entries must be JSON objects"
                raise ValueError(msg)
            typed_entry_object = cast(dict[object, object], entry_object)
            entry: dict[str, object] = {}
            for key, value in typed_entry_object.items():
                if not isinstance(key, str):
                    msg = "datago catalogue entry keys must be strings"
                    raise ValueError(msg)
                entry[key] = value
            datasets.append(DataGoAdapter._build_dataset_ref(entry))
        return tuple(datasets)

    @staticmethod
    def _build_dataset_ref(entry: dict[str, object]) -> DatasetRef:
        dataset_key = DataGoAdapter._require_string_field(entry, "dataset_key")
        name = DataGoAdapter._require_string_field(entry, "name")
        representation_value = DataGoAdapter._require_string_field(entry, "representation")
        representation = Representation(representation_value)
        raw_metadata = MappingProxyType(
            {
                key: value
                for key, value in entry.items()
                if key not in ("dataset_key", "name", "representation")
            }
        )

        return DatasetRef(
            id=f"datago.{dataset_key}",
            provider="datago",
            dataset_key=dataset_key,
            name=name,
            representation=representation,
            operations=frozenset(),
            raw_metadata=raw_metadata,
        )

    @staticmethod
    def _require_string_field(entry: Mapping[str, object], field_name: str) -> str:
        value = entry.get(field_name)
        if isinstance(value, str) and value:
            return value
        raise ValueError(f"datago catalogue entry missing non-empty string field: {field_name}")


__all__ = ["DataGoAdapter"]
