"""Catalog — dataset discovery, search, and resolution."""

from __future__ import annotations

import builtins
import logging
import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import cast

from kpubdata.core.models import DatasetRef
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.exceptions import DatasetNotFoundError, ProviderNotRegisteredError
from kpubdata.registry import ProviderRegistry

logger = logging.getLogger("kpubdata.catalog")

# 검색 결과에 포함되기 위한 데이터셋의 최소 관련도 점수(0.0–1.0).
_DEFAULT_SCORE_THRESHOLD = 0.5

# 토큰 중첩 점수 구간 — 항상 부분 문자열 1.0 점수보다 엄격히 낮게 유지하여
# 정확한 부분 문자열 일치가 순위 우선권을 유지하도록 한다.
_TOKEN_OVERLAP_FLOOR = 0.7
_TOKEN_OVERLAP_CEIL = 0.95

# 유니코드 단어 토큰(문자, 숫자, 밑줄)이다. ``village_fcst`` 같은 식별자형 토큰은
# 하나의 토큰으로 유지되며, 이는 Provider 카탈로그에서 dataset_key 문자열이
# 작성되는 방식과 일치한다.
_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _normalize(text: str) -> str:
    """NFC-normalize, strip, and casefold a string for search comparison."""
    return unicodedata.normalize("NFC", text).strip().casefold()


def _tokenize(text: str) -> frozenset[str]:
    """Split *text* into a deterministic set of normalized word tokens."""
    if not text:
        return frozenset()
    return frozenset(_TOKEN_RE.findall(_normalize(text)))


@dataclass(slots=True, frozen=True)
class _IndexedItem:
    """Pre-computed search payload for a single dataset.

    Bundles a :class:`DatasetRef` with its normalized field strings and a
    deterministic token set, so that :class:`Catalog.search` can score each
    item without recomputing per-call normalization work.
    """

    dataset: DatasetRef
    fields: tuple[str, ...]
    tokens: frozenset[str]


def _build_index(datasets: builtins.list[DatasetRef]) -> builtins.list[_IndexedItem]:
    """Materialize an in-memory search index over *datasets*.

    Each item exposes normalized field strings (name, description, tags, id,
    dataset_key, provider) and the union of word tokens extracted from those
    fields. Building the index is O(n) over the candidate set and runs once
    per search call.
    """
    index: builtins.list[_IndexedItem] = []
    for dataset in datasets:
        field_sources: builtins.list[str] = [
            dataset.name,
            dataset.id,
            dataset.dataset_key,
            dataset.provider,
        ]
        if dataset.description:
            field_sources.append(dataset.description)
        field_sources.extend(dataset.tags)

        normalized_fields: builtins.list[str] = []
        tokens: set[str] = set()
        for source in field_sources:
            normalized = _normalize(source)
            normalized_fields.append(normalized)
            tokens.update(_TOKEN_RE.findall(normalized))

        index.append(
            _IndexedItem(
                dataset=dataset,
                fields=tuple(normalized_fields),
                tokens=frozenset(tokens),
            )
        )
    return index


def _score_indexed(
    needle: str,
    needle_tokens: frozenset[str],
    item: _IndexedItem,
) -> float:
    """Score *item* against a pre-normalized query and its token set.

    Scoring layers, in priority order:

    1. **Exact substring** in any indexed field → ``1.0``.
    2. **Token overlap** = matched query tokens / total query tokens, mapped
       into ``[_TOKEN_OVERLAP_FLOOR, _TOKEN_OVERLAP_CEIL]`` so that token
       evidence never outranks a substring match.
    3. **Fuzzy fallback** via ``SequenceMatcher`` ratio across fields.

    The final score is ``max(layer 2, layer 3)`` when layer 1 misses, which
    preserves prior recall (fuzzy results are never dropped) while letting
    token evidence promote near-threshold matches.
    """
    if not needle:
        return 1.0

    for text in item.fields:
        if needle in text:
            return 1.0

    overlap_score = 0.0
    if needle_tokens:
        matched = len(needle_tokens & item.tokens)
        if matched:
            ratio = matched / len(needle_tokens)
            overlap_score = (
                _TOKEN_OVERLAP_FLOOR + (_TOKEN_OVERLAP_CEIL - _TOKEN_OVERLAP_FLOOR) * ratio
            )

    fuzzy_score = 0.0
    for text in item.fields:
        candidate = SequenceMatcher(None, needle, text).ratio()
        if candidate > fuzzy_score:
            fuzzy_score = candidate

    return max(overlap_score, fuzzy_score)


def _score_dataset(needle: str, dataset: DatasetRef) -> float:
    """Score a single dataset against *needle* (public-internal helper).

    Retained for callers that want to score one dataset without materializing
    a full index. Internally builds a one-shot index entry so behavior stays
    aligned with :class:`Catalog.search`.
    """
    needle_normalized = _normalize(needle)
    if not needle_normalized:
        return 1.0
    needle_tokens = frozenset(_TOKEN_RE.findall(needle_normalized))
    index = _build_index([dataset])
    return _score_indexed(needle_normalized, needle_tokens, index[0])


class Catalog:
    """Provides dataset discovery across registered providers."""

    def __init__(self, registry: ProviderRegistry) -> None:
        """Initialize catalog bound to a provider registry."""

        self._registry = registry

    def list(self, *, provider: str | None = None) -> builtins.list[DatasetRef]:
        """Return discoverable datasets, optionally filtered by provider.

        Raises:
            ProviderNotRegisteredError: If ``provider`` is given but unknown.
        """

        logger.debug("Catalog list", extra={"provider_filter": provider})
        if provider is not None:
            adapter = self._get_adapter(provider)
            provider_datasets = adapter.list_datasets()
            logger.debug(
                "Catalog list result",
                extra={"provider": provider, "count": len(provider_datasets)},
            )
            return provider_datasets

        datasets: builtins.list[DatasetRef] = []
        for provider_name in self._registry:
            adapter = self._get_adapter(provider_name)
            datasets.extend(adapter.list_datasets())
        logger.debug(
            "Catalog list result",
            extra={"provider": None, "count": len(datasets)},
        )
        return datasets

    def search(
        self,
        text: str,
        *,
        provider: str | None = None,
        threshold: float = _DEFAULT_SCORE_THRESHOLD,
    ) -> builtins.list[DatasetRef]:
        """이름, 설명, 태그, id를 대상으로 퍼지 매칭하여 데이터셋을 검색한다.

        결과는 관련도 점수에 따라 내림차순으로 반환된다.
        점수가 *threshold*(0.0–1.0)를 충족하는 데이터셋만 포함된다.

        Raises:
            ProviderNotRegisteredError: ``provider``가 주어졌지만 알 수 없는 경우.
        """

        logger.debug(
            "Catalog search",
            extra={"text": text, "provider_filter": provider, "threshold": threshold},
        )
        candidates = self.list(provider=provider)
        index = _build_index(candidates)

        needle_normalized = _normalize(text)
        needle_tokens = frozenset(_TOKEN_RE.findall(needle_normalized))

        scored: builtins.list[tuple[float, DatasetRef]] = []
        for item in index:
            score = _score_indexed(needle_normalized, needle_tokens, item)
            if score >= threshold:
                scored.append((score, item.dataset))

        # 점수 내림차순, 이후 안정적인 순서를 위해 id 기준으로 정렬
        scored.sort(key=lambda pair: (-pair[0], pair[1].id))
        results = [dataset for _, dataset in scored]

        logger.debug(
            "Catalog search result",
            extra={
                "provider": provider,
                "text": text,
                "candidates": len(candidates),
                "count": len(results),
            },
        )
        return results

    def resolve(self, dataset_id: str) -> tuple[ProviderAdapter, DatasetRef]:
        """Resolve ``provider.dataset_key`` into an adapter and dataset ref.

        Raises:
            DatasetNotFoundError: If the dataset id is malformed or not found.
            ProviderNotRegisteredError: If the provider is not registered.
        """

        provider_name, dataset_key = self._split_dataset_id(dataset_id)
        logger.debug(
            "Catalog resolve",
            extra={
                "dataset_id": dataset_id,
                "provider": provider_name,
                "dataset_key": dataset_key,
            },
        )
        adapter = self._get_adapter(provider_name)

        try:
            return adapter, adapter.get_dataset(dataset_key)
        except DatasetNotFoundError:
            logger.debug(
                "Catalog resolve failed: dataset not found",
                extra={"dataset_id": dataset_id, "provider": provider_name},
            )
            raise
        except Exception as exc:
            logger.debug(
                "Catalog resolve failed: adapter raised",
                extra={
                    "dataset_id": dataset_id,
                    "provider": provider_name,
                    "exception_type": type(exc).__name__,
                },
            )
            raise DatasetNotFoundError(
                f"Dataset not found: {dataset_id}",
                provider=provider_name,
                dataset_id=dataset_id,
            ) from exc

    def _get_adapter(self, provider: str) -> ProviderAdapter:
        """Fetch provider adapter from registry or raise canonical error."""

        try:
            return cast(ProviderAdapter, self._registry.get(provider))
        except ProviderNotRegisteredError:
            raise

    @staticmethod
    def _split_dataset_id(dataset_id: str) -> tuple[str, str]:
        """Split canonical dataset id into ``(provider, dataset_key)``."""

        parts = dataset_id.split(".", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise DatasetNotFoundError(
                f"Invalid dataset id format: {dataset_id}", dataset_id=dataset_id
            )
        return parts[0], parts[1]


__all__ = ["Catalog"]
