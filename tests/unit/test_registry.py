"""Tests for provider registry."""

from __future__ import annotations

import pytest

from kpubdata.exceptions import ProviderNotRegisteredError
from kpubdata.registry import ProviderRegistry


class FakeAdapter:
    """Minimal adapter satisfying the protocol for testing."""

    def __init__(self, provider_name: str = "fake") -> None:
        self._name: str = provider_name

    @property
    def name(self) -> str:
        return self._name

    def list_datasets(self) -> list[object]:
        return []

    def search_datasets(self, text: str) -> list[object]:
        _ = text
        return []

    def get_dataset(self, dataset_key: str) -> object:
        return None

    def query_records(self, dataset: object, query: object) -> object:
        return None

    def get_schema(self, dataset: object) -> object:
        return None

    def call_raw(self, dataset: object, operation: str, params: dict[str, object]) -> object:
        _ = dataset, operation, params
        return None


class TestProviderRegistry:
    def test_register_and_get(self) -> None:
        reg = ProviderRegistry()
        adapter = FakeAdapter("test")
        reg.register(adapter)
        assert reg.get("test") is adapter

    def test_contains(self) -> None:
        reg = ProviderRegistry()
        reg.register(FakeAdapter("test"))
        assert "test" in reg
        assert "other" not in reg

    def test_iter(self) -> None:
        reg = ProviderRegistry()
        reg.register(FakeAdapter("b"))
        reg.register(FakeAdapter("a"))
        assert list(reg) == ["a", "b"]

    def test_duplicate_raises(self) -> None:
        reg = ProviderRegistry()
        reg.register(FakeAdapter("dup"))
        with pytest.raises(ValueError, match="already registered"):
            reg.register(FakeAdapter("dup"))

    def test_missing_raises(self) -> None:
        reg = ProviderRegistry()
        with pytest.raises(ProviderNotRegisteredError):
            reg.get("nonexistent")

    def test_lazy_register(self) -> None:
        reg = ProviderRegistry()
        reg.register_lazy("lazy", lambda: FakeAdapter("lazy"))
        assert "lazy" in reg
        adapter = reg.get("lazy")
        assert adapter.name == "lazy"

    def test_validate_rejects_bad_adapter(self) -> None:
        reg = ProviderRegistry()
        with pytest.raises(TypeError):
            reg.register(object())  # type: ignore[arg-type]
