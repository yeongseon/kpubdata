from __future__ import annotations

from unittest.mock import MagicMock

from kpubdata.client import Client
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor


class _Adapter:
    @property
    def name(self) -> str:
        return "alpha"

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


def test_enter_delegates_to_transport_and_returns_self() -> None:
    client = Client()
    transport = MagicMock()
    client._transport = transport

    entered = client.__enter__()

    transport.__enter__.assert_called_once_with()
    assert entered is client


def test_close_delegates_to_transport_close() -> None:
    client = Client()
    transport = MagicMock()
    client._transport = transport

    client.close()

    transport.close.assert_called_once_with()


def test_exit_calls_close() -> None:
    client = Client()
    client.close = MagicMock()

    client.__exit__(None, None, None)

    client.close.assert_called_once_with()


def test_repr_includes_registered_provider_names() -> None:
    client = Client()
    client.register_provider(_Adapter())

    rendered = repr(client)

    assert rendered == "Client(providers=[alpha])"
