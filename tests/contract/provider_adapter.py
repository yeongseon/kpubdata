from __future__ import annotations

import pytest

from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.exceptions import DatasetNotFoundError


class ProviderAdapterContract:
    def test_isinstance_provider_adapter(self, adapter: ProviderAdapter) -> None:
        assert isinstance(adapter, ProviderAdapter)

    def test_name_is_nonempty_string(self, adapter: ProviderAdapter) -> None:
        name = adapter.name
        assert isinstance(name, str)
        assert len(name) > 0

    def test_list_datasets_returns_list_of_dataset_ref(self, adapter: ProviderAdapter) -> None:
        datasets = adapter.list_datasets()
        assert isinstance(datasets, list)
        assert all(isinstance(ds, DatasetRef) for ds in datasets)

    def test_list_datasets_nonempty(self, adapter: ProviderAdapter) -> None:
        datasets = adapter.list_datasets()
        assert len(datasets) > 0

    def test_search_datasets_returns_list_of_dataset_ref(self, adapter: ProviderAdapter) -> None:
        result = adapter.search_datasets("test")
        assert isinstance(result, list)
        assert all(isinstance(ds, DatasetRef) for ds in result)

    def test_get_dataset_valid_key(self, adapter: ProviderAdapter, valid_dataset_key: str) -> None:
        dataset = adapter.get_dataset(valid_dataset_key)
        assert isinstance(dataset, DatasetRef)
        assert dataset.dataset_key == valid_dataset_key

    def test_get_dataset_invalid_key_raises(
        self, adapter: ProviderAdapter, invalid_dataset_key: str
    ) -> None:
        with pytest.raises(DatasetNotFoundError):
            _ = adapter.get_dataset(invalid_dataset_key)

    def test_query_records_returns_record_batch(
        self, adapter: ProviderAdapter, sample_dataset: DatasetRef, sample_query: Query
    ) -> None:
        batch = adapter.query_records(sample_dataset, sample_query)
        assert isinstance(batch, RecordBatch)
        assert isinstance(batch.items, list)
        assert batch.dataset is sample_dataset

    def test_query_records_items_are_dicts(
        self, adapter: ProviderAdapter, sample_dataset: DatasetRef, sample_query: Query
    ) -> None:
        batch = adapter.query_records(sample_dataset, sample_query)
        for item in batch.items:
            assert isinstance(item, dict)

    def test_get_schema_returns_descriptor_or_none(
        self, adapter: ProviderAdapter, sample_dataset: DatasetRef
    ) -> None:
        schema = adapter.get_schema(sample_dataset)
        assert schema is None or isinstance(schema, SchemaDescriptor)

    def test_call_raw_returns_object(
        self,
        adapter: ProviderAdapter,
        sample_dataset: DatasetRef,
        raw_operation: tuple[str, dict[str, object]],
    ) -> None:
        operation, params = raw_operation
        result = adapter.call_raw(sample_dataset, operation, params)
        assert result is not None

    def test_all_datasets_have_provider_set(self, adapter: ProviderAdapter) -> None:
        for dataset in adapter.list_datasets():
            assert dataset.provider == adapter.name

    def test_all_dataset_ids_prefixed_with_provider(self, adapter: ProviderAdapter) -> None:
        for dataset in adapter.list_datasets():
            assert dataset.id.startswith(f"{adapter.name}.")
