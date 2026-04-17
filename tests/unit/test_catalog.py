"""Tests for catalog discovery."""

from __future__ import annotations

import pytest

from kpubdata.catalog import Catalog
from kpubdata.core.capability import Operation
from kpubdata.core.models import DatasetRef
from kpubdata.core.representation import Representation
from kpubdata.exceptions import DatasetNotFoundError
from kpubdata.registry import ProviderRegistry


class StubAdapter:
    """Adapter returning predetermined datasets for testing."""

    def __init__(self, provider_name: str, datasets: list[DatasetRef]) -> None:
        self._name = provider_name
        self._datasets = datasets

    @property
    def name(self) -> str:
        return self._name

    def list_datasets(self) -> list[DatasetRef]:
        return list(self._datasets)

    def search_datasets(self, text: str) -> list[DatasetRef]:
        needle = text.casefold()
        return [d for d in self._datasets if needle in d.name.casefold()]

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        for d in self._datasets:
            if d.dataset_key == dataset_key:
                return d
        raise DatasetNotFoundError(f"Not found: {dataset_key}")

    def query_records(self, dataset: object, query: object) -> object:
        return None

    def get_schema(self, dataset: object) -> object:
        return None

    def call_raw(self, dataset: object, operation: str, params: dict[str, object]) -> object:
        _ = dataset, operation, params
        return None


def _make_ref(provider: str, key: str, name: str) -> DatasetRef:
    return DatasetRef(
        id=f"{provider}.{key}",
        provider=provider,
        dataset_key=key,
        name=name,
        representation=Representation.API_JSON,
        operations=frozenset({Operation.LIST, Operation.RAW}),
    )


class TestCatalog:
    def _build(self) -> Catalog:
        reg = ProviderRegistry()
        reg.register(
            StubAdapter(
                "alpha",
                [
                    _make_ref("alpha", "ds1", "Alpha Dataset One"),
                    _make_ref("alpha", "ds2", "Alpha Dataset Two"),
                ],
            )
        )
        reg.register(
            StubAdapter(
                "beta",
                [
                    _make_ref("beta", "subway", "Beta Subway Data"),
                ],
            )
        )
        return Catalog(reg)

    def test_list_all(self) -> None:
        catalog = self._build()
        result = catalog.list()
        assert len(result) == 3

    def test_list_filtered(self) -> None:
        catalog = self._build()
        result = catalog.list(provider="alpha")
        assert len(result) == 2

    def test_search(self) -> None:
        catalog = self._build()
        result = catalog.search("subway")
        assert len(result) == 1
        assert result[0].name == "Beta Subway Data"

    def test_search_case_insensitive(self) -> None:
        catalog = self._build()
        result = catalog.search("ALPHA")
        assert len(result) == 2

    def test_search_with_provider_filter(self) -> None:
        catalog = self._build()
        result = catalog.search("dataset", provider="alpha")
        assert len(result) == 2
        assert all(r.provider == "alpha" for r in result)

    def test_search_delegates_to_adapter(self) -> None:
        catalog = self._build()
        result = catalog.search("subway")
        assert len(result) == 1
        assert result[0].name == "Beta Subway Data"

    def test_search_no_match_returns_empty(self) -> None:
        catalog = self._build()
        result = catalog.search("nonexistent_xyz")
        assert result == []

    def test_resolve(self) -> None:
        catalog = self._build()
        adapter, ref = catalog.resolve("beta.subway")
        assert ref.dataset_key == "subway"
        assert adapter.name == "beta"

    def test_resolve_invalid_format(self) -> None:
        catalog = self._build()
        with pytest.raises(DatasetNotFoundError, match="Invalid dataset id"):
            _ = catalog.resolve("nodot")

    def test_resolve_not_found(self) -> None:
        catalog = self._build()
        with pytest.raises(DatasetNotFoundError):
            _ = catalog.resolve("alpha.nonexistent")
