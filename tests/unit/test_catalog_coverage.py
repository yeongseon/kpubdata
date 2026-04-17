from __future__ import annotations

import pytest

from kpubdata.catalog import Catalog
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.exceptions import DatasetNotFoundError
from kpubdata.registry import ProviderRegistry


class _ExplodingAdapter:
    @property
    def name(self) -> str:
        return "alpha"

    def list_datasets(self) -> list[DatasetRef]:
        return []

    def search_datasets(self, text: str) -> list[DatasetRef]:
        return []

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        raise RuntimeError("unexpected adapter failure")

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        return RecordBatch(items=[], dataset=dataset)

    def get_schema(self, dataset: DatasetRef) -> SchemaDescriptor | None:
        return None

    def call_raw(self, dataset: DatasetRef, operation: str, params: dict[str, object]) -> object:
        return None


def test_resolve_wraps_unexpected_adapter_errors_as_dataset_not_found() -> None:
    registry = ProviderRegistry()
    registry.register(_ExplodingAdapter())
    catalog = Catalog(registry)

    with pytest.raises(DatasetNotFoundError) as exc_info:
        _ = catalog.resolve("alpha.some_dataset")

    error = exc_info.value
    assert error.provider == "alpha"
    assert error.dataset_id == "alpha.some_dataset"
    assert "Dataset not found" in str(error)
