from __future__ import annotations

import logging

import pytest

from kpubdata.catalog import Catalog
from kpubdata.config import KPubDataConfig
from kpubdata.core.dataset import Dataset
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.core.representation import Representation
from kpubdata.exceptions import ConfigError, DatasetNotFoundError, UnsupportedCapabilityError
from kpubdata.registry import ProviderRegistry


class _FakeAdapter:
    name = "fake"

    def list_datasets(self) -> list[DatasetRef]:
        return []

    def search_datasets(self, text: str) -> list[DatasetRef]:
        _ = text
        return []

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        raise DatasetNotFoundError(
            f"Dataset not found: fake.{dataset_key}",
            provider="fake",
            dataset_id=f"fake.{dataset_key}",
        )

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        _ = dataset, query
        raise AssertionError("query_records should not be called")

    def get_schema(self, dataset: DatasetRef) -> SchemaDescriptor | None:
        _ = dataset
        return None

    def call_raw(self, dataset: DatasetRef, operation: str, params: dict[str, object]) -> object:
        _ = dataset, operation, params
        return None


def test_catalog_resolve_failure_logs_debug(caplog: pytest.LogCaptureFixture) -> None:
    registry = ProviderRegistry()
    registry.register(_FakeAdapter())
    catalog = Catalog(registry)

    caplog.set_level(logging.DEBUG, logger="kpubdata.catalog")
    with pytest.raises(DatasetNotFoundError):
        _ = catalog.resolve("fake.nope")

    record = next(
        record
        for record in caplog.records
        if record.getMessage() == "Catalog resolve failed: dataset not found"
    )
    assert record.__dict__["dataset_id"] == "fake.nope"
    assert record.__dict__["provider"] == "fake"


def test_dataset_list_unsupported_logs_debug(caplog: pytest.LogCaptureFixture) -> None:
    dataset = Dataset(
        ref=DatasetRef(
            id="fake.raw_only",
            provider="fake",
            dataset_key="raw_only",
            name="Raw Only",
            operations=frozenset(),
            representation=Representation.API_JSON,
        ),
        adapter=_FakeAdapter(),
    )

    caplog.set_level(logging.DEBUG, logger="kpubdata.dataset")
    with pytest.raises(UnsupportedCapabilityError):
        _ = dataset.list()

    record = next(
        record
        for record in caplog.records
        if record.getMessage() == "Dataset does not support LIST"
    )
    assert record.__dict__["dataset_id"] == "fake.raw_only"
    assert record.__dict__["provider"] == "fake"
    assert record.__dict__["operation"] == "list"


def test_missing_provider_key_logs_debug(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("KPUBDATA_DATAGO_API_KEY", raising=False)
    monkeypatch.delenv("DATAGO_API_KEY", raising=False)
    cfg = KPubDataConfig()

    caplog.set_level(logging.DEBUG, logger="kpubdata.config")
    with pytest.raises(ConfigError):
        cfg.require_provider_key("datago")

    record = next(
        record for record in caplog.records if record.getMessage() == "Missing provider API key"
    )
    assert record.__dict__["provider"] == "datago"
