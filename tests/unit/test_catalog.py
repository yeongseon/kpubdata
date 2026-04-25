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


class TestCatalogFuzzySearch:
    """Tests for catalog-level fuzzy search across name, description, tags, and id."""

    @staticmethod
    def _make_rich_ref(
        provider: str,
        key: str,
        name: str,
        *,
        description: str | None = None,
        tags: tuple[str, ...] = (),
    ) -> DatasetRef:
        return DatasetRef(
            id=f"{provider}.{key}",
            provider=provider,
            dataset_key=key,
            name=name,
            representation=Representation.API_JSON,
            operations=frozenset({Operation.LIST}),
            description=description,
            tags=tags,
        )

    def _build_rich(self) -> Catalog:
        reg = ProviderRegistry()
        reg.register(
            StubAdapter(
                "weather",
                [
                    self._make_rich_ref(
                        "weather",
                        "village_fcst",
                        "동네예보",
                        description="기상청 단기예보 조회 서비스",
                        tags=("weather", "forecast", "기상"),
                    ),
                    self._make_rich_ref(
                        "weather",
                        "air_quality",
                        "대기오염정보",
                        description="한국환경공단 대기질 정보",
                        tags=("air", "pollution", "환경"),
                    ),
                ],
            )
        )
        reg.register(
            StubAdapter(
                "finance",
                [
                    self._make_rich_ref(
                        "finance",
                        "base_rate",
                        "기준금리",
                        description="한국은행 기준금리 조회",
                        tags=("economy", "interest-rate", "금리"),
                    ),
                ],
            )
        )
        return Catalog(reg)

    def test_search_by_description(self) -> None:
        catalog = self._build_rich()
        result = catalog.search("기상청")
        assert len(result) == 1
        assert result[0].dataset_key == "village_fcst"

    def test_search_by_tag(self) -> None:
        catalog = self._build_rich()
        result = catalog.search("pollution")
        assert len(result) == 1
        assert result[0].dataset_key == "air_quality"

    def test_search_by_korean_tag(self) -> None:
        catalog = self._build_rich()
        result = catalog.search("금리")
        assert len(result) == 1
        assert result[0].dataset_key == "base_rate"

    def test_search_by_id_substring(self) -> None:
        catalog = self._build_rich()
        result = catalog.search("base_rate")
        assert len(result) >= 1
        assert result[0].dataset_key == "base_rate"

    def test_search_partial_name(self) -> None:
        catalog = self._build_rich()
        result = catalog.search("예보")
        assert len(result) == 1
        assert result[0].dataset_key == "village_fcst"

    def test_search_sorted_by_relevance(self) -> None:
        catalog = self._build_rich()
        result = catalog.search("대기")
        assert len(result) >= 1
        assert result[0].dataset_key == "air_quality"

    def test_search_custom_threshold(self) -> None:
        catalog = self._build_rich()
        strict = catalog.search("weathr", threshold=0.9)
        lenient = catalog.search("weathr", threshold=0.1)
        assert len(lenient) >= len(strict)

    def test_search_empty_string(self) -> None:
        catalog = self._build_rich()
        result = catalog.search("")
        assert len(result) == 3

    def test_search_provider_filter_with_fuzzy(self) -> None:
        catalog = self._build_rich()
        result = catalog.search("정보", provider="weather")
        assert all(r.provider == "weather" for r in result)


class TestScoreDataset:
    """Direct unit tests for the _score_dataset helper."""

    @staticmethod
    def _ref(name: str, **kwargs: object) -> DatasetRef:
        return DatasetRef(
            id="test.ds",
            provider="test",
            dataset_key="ds",
            name=name,
            representation=Representation.API_JSON,
            **kwargs,  # type: ignore[arg-type]
        )

    def test_exact_substring_returns_one(self) -> None:
        from kpubdata.catalog import _score_dataset

        ref = self._ref("Hello World")
        assert _score_dataset("hello", ref) == 1.0

    def test_no_match_returns_low(self) -> None:
        from kpubdata.catalog import _score_dataset

        ref = self._ref("Hello World")
        score = _score_dataset("zzzzzzzzz", ref)
        assert score < 0.2

    def test_description_match(self) -> None:
        from kpubdata.catalog import _score_dataset

        ref = self._ref("Short Name", description="A detailed description with keywords")
        assert _score_dataset("keywords", ref) == 1.0

    def test_tag_match(self) -> None:
        from kpubdata.catalog import _score_dataset

        ref = self._ref("Name", tags=("weather", "forecast"))
        assert _score_dataset("forecast", ref) == 1.0

    def test_case_insensitive(self) -> None:
        from kpubdata.catalog import _score_dataset

        ref = self._ref("Base Rate")
        assert _score_dataset("BASE RATE", ref) == 1.0

    def test_whitespace_only_returns_one(self) -> None:
        from kpubdata.catalog import _score_dataset

        ref = self._ref("Anything")
        assert _score_dataset("   ", ref) == 1.0

    def test_search_does_not_call_adapter_search_datasets(self) -> None:
        """Catalog.search uses catalog-level scoring, not adapter delegation."""
        from unittest.mock import MagicMock

        adapter = StubAdapter("mock", [_make_ref("mock", "ds", "Mock Data")])
        adapter.search_datasets = MagicMock(side_effect=AssertionError("should not be called"))  # type: ignore[method-assign]

        reg = ProviderRegistry()
        reg.register(adapter)
        catalog = Catalog(reg)

        result = catalog.search("Mock")
        assert len(result) == 1
        adapter.search_datasets.assert_not_called()
