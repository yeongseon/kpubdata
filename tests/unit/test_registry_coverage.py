from __future__ import annotations

from typing import Any

import pytest

from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.registry import ProviderRegistry


class _ValidAdapter:
    def __init__(self, provider_name: str) -> None:
        self._name: str = provider_name

    @property
    def name(self) -> str:
        return self._name

    def list_datasets(self) -> list[DatasetRef]:
        return []

    def search_datasets(self, text: str) -> list[DatasetRef]:
        return []

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        raise LookupError(dataset_key)

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        return RecordBatch(items=[], dataset=dataset)

    def get_schema(self, dataset: DatasetRef) -> SchemaDescriptor | None:
        return None

    def call_raw(self, dataset: DatasetRef, operation: str, params: dict[str, object]) -> object:
        return None


class _NameOnlyAdapter:
    name: str = "broken"


def _build_non_callable_adapter() -> Any:
    return type(
        "BrokenAdapter",
        (),
        {
            "name": "ok",
            "list_datasets": None,
            "search_datasets": lambda self, text: [],
            "get_dataset": lambda self, dataset_key: None,
            "query_records": lambda self, dataset, query: None,
            "get_schema": lambda self, dataset: None,
            "call_raw": lambda self, dataset, operation, params: None,
        },
    )()


def test_repr_lists_eager_and_lazy_names() -> None:
    registry = ProviderRegistry()
    registry.register(_ValidAdapter("eager"))
    registry.register_lazy("lazy", lambda: _ValidAdapter("lazy"))

    rendered = repr(registry)

    assert rendered == "ProviderRegistry(eager=['eager'], lazy=['lazy'])"


def test_register_lazy_rejects_empty_name() -> None:
    registry = ProviderRegistry()

    with pytest.raises(ValueError, match="cannot be empty"):
        registry.register_lazy("   ", lambda: _ValidAdapter("x"))


def test_register_lazy_rejects_non_callable_factory() -> None:
    registry = ProviderRegistry()

    with pytest.raises(TypeError, match="must be callable"):
        registry.register_lazy("x", object())


def test_register_lazy_rejects_duplicate_name() -> None:
    registry = ProviderRegistry()
    registry.register_lazy("dup", lambda: _ValidAdapter("dup"))

    with pytest.raises(ValueError, match="already registered"):
        registry.register_lazy("dup", lambda: _ValidAdapter("dup"))


def test_get_rejects_lazy_adapter_name_mismatch() -> None:
    registry = ProviderRegistry()
    registry.register_lazy("expected", lambda: _ValidAdapter("actual"))

    with pytest.raises(TypeError, match="name mismatch"):
        registry.get("expected")


def test_validate_adapter_rejects_missing_methods() -> None:
    with pytest.raises(TypeError, match="missing required methods"):
        ProviderRegistry._validate_adapter(_NameOnlyAdapter())


def test_validate_adapter_rejects_non_callable_methods() -> None:
    with pytest.raises(TypeError, match="non-callable required methods"):
        ProviderRegistry._validate_adapter(_build_non_callable_adapter())
