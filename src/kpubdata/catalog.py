"""Catalog — dataset discovery, search, and resolution."""

from __future__ import annotations

import builtins
import logging
import unicodedata
from difflib import SequenceMatcher
from typing import cast

from kpubdata.core.models import DatasetRef
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.exceptions import DatasetNotFoundError, ProviderNotRegisteredError
from kpubdata.registry import ProviderRegistry

logger = logging.getLogger("kpubdata.catalog")

# Minimum relevance score (0.0–1.0) for a dataset to appear in search results.
_DEFAULT_SCORE_THRESHOLD = 0.5


def _normalize(text: str) -> str:
    """NFC-normalize, strip, and casefold a string for search comparison."""
    return unicodedata.normalize("NFC", text).strip().casefold()


def _score_dataset(needle: str, dataset: DatasetRef) -> float:
    """Score a dataset against a search term.

    Returns a relevance score between 0.0 and 1.0.  An exact substring
    match in any searchable field yields 1.0.  Otherwise the best
    ``SequenceMatcher`` ratio across fields is returned.

    Searchable fields: name, description, tags, id.
    """
    needle_lower = _normalize(needle)
    if not needle_lower:
        return 1.0

    fields: builtins.list[str] = []
    fields.append(_normalize(dataset.name))
    if dataset.description:
        fields.append(_normalize(dataset.description))
    for tag in dataset.tags:
        fields.append(_normalize(tag))
    fields.append(_normalize(dataset.id))

    # Fast path: exact substring match → score 1.0
    for text in fields:
        if needle_lower in text:
            return 1.0

    # Slow path: fuzzy matching via SequenceMatcher
    best: float = 0.0
    for text in fields:
        ratio = SequenceMatcher(None, needle_lower, text).ratio()
        if ratio > best:
            best = ratio

    return best


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
        """Search datasets with fuzzy matching across name, description, tags, and id.

        Results are scored by relevance and returned in descending order.
        Only datasets whose score meets *threshold* (0.0–1.0) are included.

        Raises:
            ProviderNotRegisteredError: If ``provider`` is given but unknown.
        """

        logger.debug(
            "Catalog search",
            extra={"text": text, "provider_filter": provider, "threshold": threshold},
        )
        candidates = self.list(provider=provider)

        scored: builtins.list[tuple[float, DatasetRef]] = []
        for dataset in candidates:
            score = _score_dataset(text, dataset)
            if score >= threshold:
                scored.append((score, dataset))

        # Sort by score descending, then by id for stable ordering
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
