from __future__ import annotations

from kpubdata.client import Client
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor


class _AdapterWithoutFlag:
    @property
    def name(self) -> str:
        return "beta"

    def list_datasets(self) -> list[DatasetRef]:
        return []

    def search_datasets(self, text: str) -> list[DatasetRef]:
        _ = text
        return []

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        raise LookupError(dataset_key)

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        _ = query
        return RecordBatch(items=[], dataset=dataset)

    def get_schema(self, dataset: DatasetRef) -> SchemaDescriptor | None:
        _ = dataset
        return None

    def call_raw(self, dataset: DatasetRef, operation: str, params: dict[str, object]) -> object:
        _ = dataset
        _ = operation
        _ = params
        return None


def test_iter_authenticated_providers_defaults_missing_flag_to_true() -> None:
    client = Client()
    client.register_provider(_AdapterWithoutFlag())

    provider_names = {adapter.name for adapter in client.iter_authenticated_providers()}

    assert "beta" in provider_names
    assert "krx" not in provider_names
