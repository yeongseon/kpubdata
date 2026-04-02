from __future__ import annotations

import pytest

from kpubdata.client import Client
from kpubdata.core.capability import Operation
from kpubdata.core.dataset import Dataset
from kpubdata.core.models import DatasetRef, Query, RecordBatch
from kpubdata.core.representation import Representation
from kpubdata.exceptions import (
    DatasetNotFoundError,
    ProviderNotRegisteredError,
    UnsupportedCapabilityError,
)


class FakeAdapter:
    def __init__(self) -> None:
        self._datasets: dict[str, DatasetRef] = {
            "weather": DatasetRef(
                id="fake.weather",
                provider="fake",
                dataset_key="weather",
                name="Weather Data",
                representation=Representation.API_JSON,
                operations=frozenset({Operation.LIST, Operation.RAW}),
            ),
            "stations": DatasetRef(
                id="fake.stations",
                provider="fake",
                dataset_key="stations",
                name="Station List",
                representation=Representation.API_JSON,
                operations=frozenset({Operation.LIST, Operation.GET, Operation.RAW}),
            ),
        }
        self.last_query: tuple[DatasetRef, Query] | None = None
        self.last_raw_call: tuple[DatasetRef, str, dict[str, object]] | None = None

    @property
    def name(self) -> str:
        return "fake"

    def list_datasets(self) -> list[DatasetRef]:
        return [self._datasets["weather"], self._datasets["stations"]]

    def search_datasets(self, text: str) -> list[DatasetRef]:
        needle = text.casefold()
        return [
            dataset_ref
            for dataset_ref in self._datasets.values()
            if needle in dataset_ref.name.casefold()
        ]

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        try:
            return self._datasets[dataset_key]
        except KeyError as exc:
            raise DatasetNotFoundError(f"Dataset not found: {dataset_key}") from exc

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        self.last_query = (dataset, query)
        return RecordBatch(
            items=[
                {"id": "w-001", "value": "sunny"},
                {"id": "w-002", "value": "rain"},
            ],
            dataset=dataset,
            total_count=2,
        )

    def get_record(self, dataset: DatasetRef, key: dict[str, object]) -> dict[str, object] | None:
        return {"dataset": dataset.dataset_key, "record": key, "id": "station-record"}

    def get_schema(self, _dataset: DatasetRef) -> None:
        return None

    def call_raw(self, dataset: DatasetRef, operation: str, params: dict[str, object]) -> object:
        self.last_raw_call = (dataset, operation, params)
        return {"ok": True, "dataset": dataset.id, "operation": operation, "params": params}


def _build_client() -> tuple[Client, FakeAdapter]:
    client = Client(provider_keys={"fake": "test-key"})
    fake = FakeAdapter()
    client.register_provider(fake)
    return client, fake


def test_register_and_list_datasets() -> None:
    client, _fake = _build_client()

    refs = client.datasets.list()

    assert len(refs) == 2
    assert {ref.id for ref in refs} == {"fake.weather", "fake.stations"}


def test_register_and_search_datasets() -> None:
    client, _fake = _build_client()

    refs = client.datasets.search("weather")

    assert len(refs) == 1
    assert refs[0].id == "fake.weather"


def test_dataset_resolves_to_bound_dataset() -> None:
    client, _fake = _build_client()

    dataset = client.dataset("fake.weather")

    assert isinstance(dataset, Dataset)
    assert dataset.id == "fake.weather"
    assert dataset.name == "Weather Data"
    assert dataset.provider == "fake"
    assert dataset.operations == frozenset({Operation.LIST, Operation.RAW})


def test_dataset_list_delegates_to_query_records() -> None:
    client, fake = _build_client()

    result = client.dataset("fake.weather").list(stationName="종로구")

    assert isinstance(result, RecordBatch)
    assert len(result.items) == 2
    assert fake.last_query is not None
    queried_dataset, query = fake.last_query
    assert queried_dataset.id == "fake.weather"
    assert query.filters == {"stationName": "종로구"}


def test_dataset_call_raw_delegates_to_adapter() -> None:
    client, fake = _build_client()

    result = client.dataset("fake.weather").call_raw("getWeather", param1="value1")

    assert result == {
        "ok": True,
        "dataset": "fake.weather",
        "operation": "getWeather",
        "params": {"param1": "value1"},
    }
    assert fake.last_raw_call is not None
    raw_dataset, raw_operation, raw_params = fake.last_raw_call
    assert raw_dataset.id == "fake.weather"
    assert raw_operation == "getWeather"
    assert raw_params == {"param1": "value1"}


def test_dataset_get_delegates_to_adapter() -> None:
    client, _fake = _build_client()

    result = client.dataset("fake.stations").get(station_id="ST001")

    assert isinstance(result, dict)
    assert result["dataset"] == "stations"
    assert result["record"] == {"station_id": "ST001"}


def test_dataset_schema_returns_none() -> None:
    client, _fake = _build_client()

    result = client.dataset("fake.weather").schema()

    assert result is None


def test_unknown_provider_raises() -> None:
    client = Client(provider_keys={"fake": "test-key"})

    with pytest.raises(ProviderNotRegisteredError):
        _ = client.dataset("unknown.ds")


def test_unknown_dataset_raises() -> None:
    client, _fake = _build_client()

    with pytest.raises(DatasetNotFoundError):
        _ = client.dataset("fake.nonexistent")


def test_unsupported_get_raises() -> None:
    client, _fake = _build_client()

    with pytest.raises(UnsupportedCapabilityError):
        _ = client.dataset("fake.weather").get(key="val")


def test_from_env_creates_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KPUBDATA_TIMEOUT", "15")
    client = Client.from_env()
    fake = FakeAdapter()

    client.register_provider(fake)

    assert client.dataset("fake.weather").id == "fake.weather"
