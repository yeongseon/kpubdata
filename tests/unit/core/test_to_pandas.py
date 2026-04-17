"""Tests for RecordBatch.to_pandas() optional pandas integration."""

from __future__ import annotations

from types import ModuleType
from unittest.mock import patch

import pytest

from kpubdata.core.models import DatasetRef, RecordBatch
from kpubdata.core.representation import Representation


def _dataset_ref() -> DatasetRef:
    return DatasetRef(
        id="mock.test",
        provider="mock",
        dataset_key="test",
        name="Test",
        representation=Representation.API_JSON,
    )


class _FakeDataFrame:
    _data: list[dict[str, object]]
    columns: list[str]

    def __init__(self, data: list[dict[str, object]]) -> None:
        self._data = list(data)
        self.columns = list(self._data[0].keys()) if self._data else []

    def __len__(self) -> int:
        return len(self._data)


class _FakePandasModule(ModuleType):
    DataFrame: type[_FakeDataFrame]


def _fake_pandas_module() -> _FakePandasModule:
    module = _FakePandasModule("pandas")
    module.DataFrame = _FakeDataFrame
    return module


def test_to_pandas_returns_dataframe() -> None:
    batch = RecordBatch(
        items=[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 31}],
        dataset=_dataset_ref(),
    )

    fake_pandas = _fake_pandas_module()

    with patch.dict("sys.modules", {"pandas": fake_pandas}):
        df = batch.to_pandas()

    assert isinstance(df, fake_pandas.DataFrame)
    assert list(df.columns) == ["name", "age"]
    assert len(df) == 2


def test_to_pandas_empty_items() -> None:
    batch = RecordBatch(items=[], dataset=_dataset_ref())

    fake_pandas = _fake_pandas_module()

    with patch.dict("sys.modules", {"pandas": fake_pandas}):
        df = batch.to_pandas()

    assert isinstance(df, fake_pandas.DataFrame)
    assert list(df.columns) == []
    assert len(df) == 0


def test_to_pandas_import_error() -> None:
    batch = RecordBatch(items=[{"name": "Alice"}], dataset=_dataset_ref())

    with (
        patch.dict("sys.modules", {"pandas": None}),
        pytest.raises(ImportError, match=r"pandas is required for to_pandas\(\)"),
    ):
        _ = batch.to_pandas()
