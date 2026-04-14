"""Tests for Dataset binding and capability checks."""

from __future__ import annotations

import pytest

from kpubdata.core.capability import Operation
from kpubdata.core.dataset import Dataset
from kpubdata.core.models import DatasetRef, Query, RecordBatch
from kpubdata.core.representation import Representation
from kpubdata.exceptions import UnsupportedCapabilityError


class MockAdapter:
    """Adapter that records calls for assertion."""

    def __init__(self) -> None:
        self.last_query: Query | None = None
        self.last_raw_op: str | None = None

    @property
    def name(self) -> str:
        return "mock"

    def list_datasets(self) -> list:
        return []

    def search_datasets(self, text: str) -> list:
        return []

    def get_dataset(self, dataset_key: str) -> object:
        return None

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        self.last_query = query
        return RecordBatch(items=[{"k": "v"}], dataset=dataset)

    def get_record(self, dataset: DatasetRef, key: dict) -> dict | None:
        return {"id": "1"}

    def get_schema(self, dataset: DatasetRef) -> object:
        return None

    def call_raw(self, dataset: DatasetRef, operation: str, params: dict) -> object:
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
        ds = Dataset(ref=_ref(), adapter=adapter)  # type: ignore[arg-type]
        result = ds.list(code="11680")
        assert len(result) == 1
        assert adapter.last_query is not None
        assert adapter.last_query.filters["code"] == "11680"

    def test_list_unsupported(self) -> None:
        adapter = MockAdapter()
        ds = Dataset(ref=_ref(frozenset({Operation.RAW})), adapter=adapter)  # type: ignore[arg-type]
        with pytest.raises(UnsupportedCapabilityError, match="list"):
            ds.list()

    def test_get(self) -> None:
        adapter = MockAdapter()
        ds = Dataset(ref=_ref(), adapter=adapter)  # type: ignore[arg-type]
        record = ds.get(id="1")
        assert record == {"id": "1"}

    def test_get_unsupported(self) -> None:
        adapter = MockAdapter()
        ds = Dataset(ref=_ref(frozenset({Operation.LIST})), adapter=adapter)  # type: ignore[arg-type]
        with pytest.raises(UnsupportedCapabilityError, match="get"):
            ds.get(id="1")

    def test_call_raw(self) -> None:
        adapter = MockAdapter()
        ds = Dataset(ref=_ref(), adapter=adapter)  # type: ignore[arg-type]
        result = ds.call_raw("list", param="value")
        assert result == {"raw": True}
        assert adapter.last_raw_op == "list"

    def test_repr(self) -> None:
        adapter = MockAdapter()
        ds = Dataset(ref=_ref(), adapter=adapter)  # type: ignore[arg-type]
        assert "mock.test" in repr(ds)
