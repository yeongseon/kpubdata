from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from kpubdata.client import Client
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.transport.http import HttpTransport, TransportRequirements


class _AdapterWithoutRequirements:
    instances: list[object] = []

    def __init__(self, *, config: object, transport: HttpTransport) -> None:
        self.config: object = config
        self.transport: HttpTransport = transport
        type(self).instances.append(self)

    @property
    def name(self) -> str:
        return "dummy"

    def list_datasets(self) -> list[DatasetRef]:
        return []

    def search_datasets(self, _text: str) -> list[DatasetRef]:
        return []

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        raise LookupError(dataset_key)

    def query_records(self, dataset: DatasetRef, _query: Query) -> RecordBatch:
        return RecordBatch(items=[], dataset=dataset)

    def get_record(self, _dataset: DatasetRef, _key: dict[str, object]) -> dict[str, object] | None:
        return None

    def get_schema(self, _dataset: DatasetRef) -> SchemaDescriptor | None:
        return None

    def call_raw(self, _dataset: DatasetRef, _operation: str, _params: dict[str, object]) -> object:
        return None


class _AdapterWithRequirements:
    instances: list[object] = []

    def __init__(self, *, config: object, transport: HttpTransport) -> None:
        self.config: object = config
        self.transport: HttpTransport = transport
        type(self).instances.append(self)

    @property
    def name(self) -> str:
        return "dummy"

    @property
    def transport_requirements(self) -> TransportRequirements | None:
        return TransportRequirements(headers={"X-Provider": "dummy"}, verify_ssl=False)

    def list_datasets(self) -> list[DatasetRef]:
        return []

    def search_datasets(self, _text: str) -> list[DatasetRef]:
        return []

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        raise LookupError(dataset_key)

    def query_records(self, dataset: DatasetRef, _query: Query) -> RecordBatch:
        return RecordBatch(items=[], dataset=dataset)

    def get_record(self, _dataset: DatasetRef, _key: dict[str, object]) -> dict[str, object] | None:
        return None

    def get_schema(self, _dataset: DatasetRef) -> SchemaDescriptor | None:
        return None

    def call_raw(self, _dataset: DatasetRef, _operation: str, _params: dict[str, object]) -> object:
        return None


def test_builtin_provider_without_transport_requirements_uses_shared_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _AdapterWithoutRequirements.instances.clear()
    monkeypatch.setattr(
        "kpubdata.client._BUILTIN_PROVIDERS", (("dummy", "dummy.module", "DummyAdapter"),)
    )

    with (
        patch(
            "importlib.import_module",
            return_value=SimpleNamespace(DummyAdapter=_AdapterWithoutRequirements),
        ),
        patch.object(HttpTransport, "with_requirements") as with_requirements,
    ):
        client = Client()
        _ = client.datasets.list()

    with_requirements.assert_not_called()
    assert len(_AdapterWithoutRequirements.instances) == 1


def test_builtin_provider_with_transport_requirements_builds_custom_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _AdapterWithRequirements.instances.clear()
    monkeypatch.setattr(
        "kpubdata.client._BUILTIN_PROVIDERS", (("dummy", "dummy.module", "DummyAdapter"),)
    )

    with patch(
        "importlib.import_module",
        return_value=SimpleNamespace(DummyAdapter=_AdapterWithRequirements),
    ):
        client = Client(timeout=12.0, max_retries=7)
        _ = client.datasets.list()

    adapter = _AdapterWithRequirements.instances[-1]
    assert isinstance(adapter, _AdapterWithRequirements)
    assert len(_AdapterWithRequirements.instances) == 2

    with patch("kpubdata.transport.http.httpx.Client") as client_cls:
        _ = adapter.transport.client

    client_cls.assert_called_once_with(
        timeout=12.0,
        headers={"X-Provider": "dummy"},
        follow_redirects=True,
        verify=False,
    )
