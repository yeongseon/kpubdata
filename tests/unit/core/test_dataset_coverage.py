from __future__ import annotations

from kpubdata.core.capability import Operation
from kpubdata.core.dataset import Dataset
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.core.representation import Representation
from kpubdata.transport.http import HttpTransport


class _Adapter:
    @property
    def name(self) -> str:
        return "mock"

    def list_datasets(self) -> list[DatasetRef]:
        return []

    def search_datasets(self, text: str) -> list[DatasetRef]:
        return []

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        raise LookupError(dataset_key)

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        return RecordBatch(items=[], dataset=dataset)

    def get_record(self, dataset: DatasetRef, key: dict[str, object]) -> dict[str, object] | None:
        return None

    def get_schema(self, dataset: DatasetRef) -> SchemaDescriptor | None:
        return None

    def call_raw(self, dataset: DatasetRef, operation: str, params: dict[str, object]) -> object:
        return None


def test_ref_property_returns_bound_reference() -> None:
    ref = DatasetRef(
        id="mock.sample",
        provider="mock",
        dataset_key="sample",
        name="Sample",
        representation=Representation.API_JSON,
        operations=frozenset({Operation.LIST}),
    )
    dataset = Dataset(ref=ref, adapter=_Adapter(), transport=HttpTransport())

    assert dataset.ref is ref
