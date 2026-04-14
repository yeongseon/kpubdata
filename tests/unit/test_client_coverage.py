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

    assert "alpha" in rendered
    assert "datago" in rendered
    assert "bok" in rendered
    assert "kosis" in rendered


def test_builtin_providers_registered_by_default() -> None:
    client = Client()

    assert "datago" in client._registry
    assert "bok" in client._registry
    assert "kosis" in client._registry


def test_builtin_providers_datasets_discoverable() -> None:
    client = Client()

    datasets = client.datasets.list()

    assert len(datasets) > 0
    provider_names = {ds.provider for ds in datasets}
    assert "datago" in provider_names
    assert "bok" in provider_names
    assert "kosis" in provider_names


def test_builtin_dataset_binding_works() -> None:
    client = Client()

    ds = client.dataset("datago.village_fcst")

    assert ds.id == "datago.village_fcst"
    assert ds.provider == "datago"


def test_user_adapter_overrides_builtin() -> None:
    custom_adapter = _Adapter()
    custom_adapter._name = "datago"  # type: ignore[attr-defined]

    class _DatagoOverride(_Adapter):
        @property
        def name(self) -> str:
            return "datago"

    client = Client()
    client._registry._lazy.pop("datago", None)
    client.register_provider(_DatagoOverride())

    adapter = client._registry.get("datago")
    assert isinstance(adapter, _DatagoOverride)
