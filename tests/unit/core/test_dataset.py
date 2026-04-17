"""Tests for Dataset binding and capability checks."""

from __future__ import annotations

import pytest

from kpubdata.core.capability import Operation
from kpubdata.core.dataset import Dataset
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.core.representation import Representation
from kpubdata.exceptions import UnsupportedCapabilityError


class MockAdapter:
    """Adapter that records calls for assertion."""

    def __init__(self) -> None:
        self.last_query: Query | None = None
        self.last_raw_op: str | None = None
        self.batches: list[RecordBatch] = []

    @property
    def name(self) -> str:
        return "mock"

    def list_datasets(self) -> list[DatasetRef]:
        return []

    def search_datasets(self, text: str) -> list[DatasetRef]:
        _ = text
        return []

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        _ = dataset_key
        return _ref()

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        self.last_query = query
        if self.batches:
            return self.batches.pop(0)
        return RecordBatch(items=[{"k": "v"}], dataset=dataset)

    def get_record(self, dataset: DatasetRef, key: dict[str, object]) -> dict[str, object] | None:
        _ = dataset, key
        return {"id": "1"}

    def get_schema(self, dataset: DatasetRef) -> SchemaDescriptor | None:
        _ = dataset
        return None

    def call_raw(self, dataset: DatasetRef, operation: str, params: dict[str, object]) -> object:
        _ = dataset, params
        self.last_raw_op = operation
        return {"raw": True}


def _ref(ops: frozenset[Operation] | None = None) -> DatasetRef:
    return DatasetRef(
        id="mock.test",
        provider="mock",
        dataset_key="test",
        name="Test",
        representation=Representation.API_JSON,
        operations=ops or frozenset({Operation.LIST, Operation.GET, Operation.RAW}),
    )


class TestDataset:
    def test_list(self) -> None:
        adapter = MockAdapter()
        ds = Dataset(ref=_ref(), adapter=adapter)
        result = ds.list(code="11680")
        assert len(result) == 1
        assert adapter.last_query is not None
        assert adapter.last_query.filters["code"] == "11680"

    def test_list_unsupported(self) -> None:
        adapter = MockAdapter()
        ds = Dataset(ref=_ref(frozenset({Operation.RAW})), adapter=adapter)
        with pytest.raises(UnsupportedCapabilityError, match="list"):
            _ = ds.list()

    def test_get(self) -> None:
        adapter = MockAdapter()
        ds = Dataset(ref=_ref(), adapter=adapter)
        record = ds.get(id="1")
        assert record == {"id": "1"}

    def test_get_unsupported(self) -> None:
        adapter = MockAdapter()
        ds = Dataset(ref=_ref(frozenset({Operation.LIST})), adapter=adapter)
        with pytest.raises(UnsupportedCapabilityError, match="get"):
            _ = ds.get(id="1")

    def test_call_raw(self) -> None:
        adapter = MockAdapter()
        ds = Dataset(ref=_ref(), adapter=adapter)
        result = ds.call_raw("list", param="value")
        assert result == {"raw": True}
        assert adapter.last_raw_op == "list"

    def test_repr(self) -> None:
        adapter = MockAdapter()
        ds = Dataset(ref=_ref(), adapter=adapter)
        assert "mock.test" in repr(ds)

    def test_list_separates_canonical_query_fields(self) -> None:
        adapter = MockAdapter()
        ds = Dataset(ref=_ref(), adapter=adapter)

        _ = ds.list(
            start_date="202401",
            end_date="202412",
            page=2,
            page_size=50,
            region="서울",
        )

        assert adapter.last_query is not None
        assert adapter.last_query.start_date == "202401"
        assert adapter.last_query.end_date == "202412"
        assert adapter.last_query.page == 2
        assert adapter.last_query.page_size == 50
        assert adapter.last_query.filters == {"region": "서울"}

    def test_list_canonical_fields_not_in_filters(self) -> None:
        adapter = MockAdapter()
        ds = Dataset(ref=_ref(), adapter=adapter)

        _ = ds.list(cursor="abc", fields=["name", "age"], sort=["name"])

        assert adapter.last_query is not None
        assert adapter.last_query.cursor == "abc"
        assert adapter.last_query.fields == ["name", "age"]
        assert adapter.last_query.sort == ["name"]
        assert adapter.last_query.filters == {}

    def test_list_only_filters_no_canonical(self) -> None:
        adapter = MockAdapter()
        ds = Dataset(ref=_ref(), adapter=adapter)

        _ = ds.list(lawd_code="11680", deal_ym="202503")

        assert adapter.last_query is not None
        assert adapter.last_query.page is None
        assert adapter.last_query.start_date is None
        assert adapter.last_query.filters == {"lawd_code": "11680", "deal_ym": "202503"}

    def test_list_all_yields_multiple_batches(self) -> None:
        adapter = MockAdapter()
        dataset_ref = _ref()
        adapter.batches = [
            RecordBatch(items=[{"page": 1}], dataset=dataset_ref, next_page=2),
            RecordBatch(items=[{"page": 2}], dataset=dataset_ref, next_page=3),
            RecordBatch(items=[{"page": 3}], dataset=dataset_ref, next_page=None),
        ]
        ds = Dataset(ref=dataset_ref, adapter=adapter)

        batches = list(ds.list_all(region="서울"))

        assert [batch.items[0]["page"] for batch in batches] == [1, 2, 3]

    def test_list_all_stops_when_next_page_is_none(self) -> None:
        adapter = MockAdapter()
        dataset_ref = _ref()
        adapter.batches = [
            RecordBatch(items=[{"page": 1}], dataset=dataset_ref, next_page=2),
            RecordBatch(items=[{"page": 2}], dataset=dataset_ref, next_page=None),
        ]
        ds = Dataset(ref=dataset_ref, adapter=adapter)

        batches = list(ds.list_all(code="11680"))

        assert len(batches) == 2
        assert adapter.last_query is not None
        assert adapter.last_query.page == 2
        assert adapter.last_query.filters == {"code": "11680"}

    def test_list_all_single_page(self) -> None:
        adapter = MockAdapter()
        dataset_ref = _ref()
        adapter.batches = [RecordBatch(items=[{"page": 1}], dataset=dataset_ref, next_page=None)]
        ds = Dataset(ref=dataset_ref, adapter=adapter)

        batches = list(ds.list_all())

        assert len(batches) == 1
        assert batches[0].items == [{"page": 1}]
