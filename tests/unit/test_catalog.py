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


class TestCatalogIndexedScorer:
    """Tests for the indexed scorer introduced in the catalog search refactor."""

    @staticmethod
    def _make_ref(
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

    def _build_catalog(self) -> Catalog:
        reg = ProviderRegistry()
        reg.register(
            StubAdapter(
                "weather",
                [
                    self._make_ref(
                        "weather",
                        "village_fcst",
                        "동네예보",
                        description="기상청 단기예보 조회 서비스",
                        tags=("weather", "forecast", "기상"),
                    ),
                    self._make_ref(
                        "weather",
                        "marine_fcst",
                        "해양예보",
                        description="기상청 해양예보 서비스",
                        tags=("weather", "marine"),
                    ),
                ],
            )
        )
        reg.register(
            StubAdapter(
                "finance",
                [
                    self._make_ref(
                        "finance",
                        "base_rate",
                        "기준금리",
                        description="한국은행 기준금리",
                        tags=("economy", "rate"),
                    ),
                ],
            )
        )
        return Catalog(reg)

    def test_token_overlap_ranks_full_match_above_partial(self) -> None:
        """A dataset matching both query tokens outranks one matching only one."""
        catalog = self._build_catalog()
        # 'marine weather' is not a contiguous substring of any field, so both
        # datasets fall through the substring layer. marine_fcst tags contain
        # both 'marine' and 'weather' (2/2 → ceil score), while village_fcst
        # tags contain only 'weather' (1/2 → mid-band score).
        result = catalog.search("marine weather", threshold=0.6)
        keys = [ref.dataset_key for ref in result]
        assert "marine_fcst" in keys and "village_fcst" in keys
        assert keys.index("marine_fcst") < keys.index("village_fcst")

    def test_provider_name_is_searchable(self) -> None:
        """Searching by provider name returns that provider's datasets."""
        catalog = self._build_catalog()
        result = catalog.search("finance")
        assert len(result) == 1
        assert result[0].provider == "finance"

    def test_dataset_key_is_searchable_as_single_token(self) -> None:
        """Identifier-style dataset_key remains a single token (no underscore split)."""
        catalog = self._build_catalog()
        # threshold=0.9 filters out fuzzy noise from sibling keys that share
        # the '_fcst' suffix; only the exact substring hit on village_fcst
        # (score 1.0) qualifies.
        result = catalog.search("village_fcst", threshold=0.9)
        assert len(result) == 1
        assert result[0].dataset_key == "village_fcst"

    def test_substring_outranks_token_overlap(self) -> None:
        """An exact substring hit (score 1.0) always sorts above token-overlap hits."""
        catalog = self._build_catalog()
        # 'forecast' appears as a substring in the 'forecast' tag on village_fcst
        # (score 1.0) and is also a query token. marine_fcst lacks the
        # 'forecast' tag, so it can only earn a token-overlap or fuzzy score.
        result = catalog.search("forecast", threshold=0.5)
        assert result, "expected at least one result"
        assert result[0].dataset_key == "village_fcst"

    def test_no_result_for_long_meaningless_query(self) -> None:
        """A long random query stays below threshold (no spurious fuzzy hits)."""
        catalog = self._build_catalog()
        result = catalog.search("qzxvbnmqzxvbnmqzxvbnm_no_such_dataset_anywhere")
        assert result == []

    def test_case_insensitive_token_match(self) -> None:
        """Token overlap is computed on casefolded text."""
        catalog = self._build_catalog()
        # 'MARINE' is uppercase but should match 'marine' tag (substring path).
        result = catalog.search("MARINE")
        assert len(result) == 1
        assert result[0].dataset_key == "marine_fcst"

    def test_mixed_korean_and_ascii_tokenization(self) -> None:
        """Korean and ASCII tokens coexist in a single query."""
        catalog = self._build_catalog()
        # '기상청 forecast' — '기상청' substring hits the description of
        # village_fcst; 'forecast' substring hits its tag. Both pass via the
        # substring layer; result is non-empty and stably ordered.
        result = catalog.search("기상청 forecast", threshold=0.5)
        assert any(r.dataset_key == "village_fcst" for r in result)

    def test_provider_filter_applies_before_indexing(self) -> None:
        """Provider filter narrows candidates; cross-provider matches are excluded."""
        catalog = self._build_catalog()
        # '한국은행' appears only in the finance dataset's description; with
        # provider='weather' the candidate pool excludes finance entirely.
        result = catalog.search("한국은행", provider="weather")
        assert result == []

    def test_empty_query_returns_all_candidates(self) -> None:
        """An empty query yields score 1.0 for every dataset (existing contract)."""
        catalog = self._build_catalog()
        result = catalog.search("")
        assert len(result) == 3

    def test_threshold_above_one_returns_empty(self) -> None:
        """Threshold > 1.0 excludes everything (token overlap caps below 1.0)."""
        catalog = self._build_catalog()
        # A query that hits only via token overlap (no substring): pick a query
        # token that appears only as a token (e.g. provider name as a token).
        # With threshold=1.01 nothing can pass.
        result = catalog.search("forecast", threshold=1.01)
        assert result == []


class TestIndexedScorerHelpers:
    """Direct tests for the indexed scorer building blocks."""

    @staticmethod
    def _ref(
        name: str,
        *,
        description: str | None = None,
        tags: tuple[str, ...] = (),
    ) -> DatasetRef:
        return DatasetRef(
            id="prov.key",
            provider="prov",
            dataset_key="key",
            name=name,
            representation=Representation.API_JSON,
            operations=frozenset({Operation.LIST}),
            description=description,
            tags=tags,
        )

    def test_tokenize_splits_on_non_word_chars(self) -> None:
        from kpubdata.catalog import _tokenize

        assert _tokenize("Hello, World!") == frozenset({"hello", "world"})

    def test_tokenize_keeps_underscore_identifier_intact(self) -> None:
        from kpubdata.catalog import _tokenize

        assert _tokenize("village_fcst") == frozenset({"village_fcst"})

    def test_tokenize_korean_word(self) -> None:
        from kpubdata.catalog import _tokenize

        assert _tokenize("기상청 예보") == frozenset({"기상청", "예보"})

    def test_tokenize_empty_returns_empty_set(self) -> None:
        from kpubdata.catalog import _tokenize

        assert _tokenize("") == frozenset()
        assert _tokenize("   ") == frozenset()

    def test_build_index_includes_provider_and_dataset_key(self) -> None:
        from kpubdata.catalog import _build_index

        ref = self._ref("Name", tags=("alpha",), description="desc")
        index = _build_index([ref])
        assert len(index) == 1
        item = index[0]
        assert "prov" in item.tokens
        assert "key" in item.tokens
        assert "name" in item.tokens
        assert "alpha" in item.tokens
        assert "desc" in item.tokens

    def test_score_indexed_substring_returns_one(self) -> None:
        from kpubdata.catalog import _build_index, _score_indexed, _tokenize

        ref = self._ref("Hello World")
        item = _build_index([ref])[0]
        score = _score_indexed("hello", _tokenize("hello"), item)
        assert score == 1.0

    def test_score_indexed_token_overlap_band(self) -> None:
        """Token overlap score stays strictly below 1.0 and within the band."""
        from kpubdata.catalog import (
            _TOKEN_OVERLAP_CEIL,
            _TOKEN_OVERLAP_FLOOR,
            _build_index,
            _score_indexed,
            _tokenize,
        )

        ref = self._ref("Apple Banana", description="fruit basket")
        item = _build_index([ref])[0]
        # Query token 'apple' is a substring of 'apple banana' → returns 1.0.
        # To force the token-overlap branch we need a query whose tokens match
        # item tokens exactly but whose normalized form is NOT a substring of
        # any field. 'banana apple' has both tokens; ' apple banana' contains
        # both as a substring. Use a query that is not contiguous in any field.
        query = "banana zzz"
        score = _score_indexed(query, _tokenize(query), item)
        # 1/2 of query tokens matched ('banana') → expect floor + 0.5 * (ceil-floor)
        expected = _TOKEN_OVERLAP_FLOOR + 0.5 * (_TOKEN_OVERLAP_CEIL - _TOKEN_OVERLAP_FLOOR)
        assert score == pytest.approx(expected)
        assert score < 1.0
        assert _TOKEN_OVERLAP_FLOOR <= score <= _TOKEN_OVERLAP_CEIL

    def test_score_indexed_full_token_overlap_below_substring_score(self) -> None:
        """Even 100% token overlap stays below substring score (1.0)."""
        from kpubdata.catalog import (
            _TOKEN_OVERLAP_CEIL,
            _build_index,
            _score_indexed,
            _tokenize,
        )

        ref = self._ref("Apple Banana")
        item = _build_index([ref])[0]
        # 'banana apple' tokens fully overlap but the literal string is not a
        # contiguous substring of 'apple banana'.
        query = "banana apple"
        score = _score_indexed(query, _tokenize(query), item)
        assert score == pytest.approx(_TOKEN_OVERLAP_CEIL)
        assert score < 1.0
