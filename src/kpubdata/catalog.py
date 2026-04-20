"""Catalog — dataset discovery, search, and resolution."""

from __future__ import annotations

import builtins
import logging
from typing import cast

from kpubdata.core.models import DatasetRef
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.exceptions import DatasetNotFoundError, ProviderNotRegisteredError
from kpubdata.registry import ProviderRegistry

logger = logging.getLogger("kpubdata.catalog")


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

    def search(self, text: str, *, provider: str | None = None) -> builtins.list[DatasetRef]:
        """Search datasets by delegating to each adapter's search logic.

        Each adapter implements its own ``search_datasets(text)`` method,
        allowing provider-specific search semantics.

        Raises:
            ProviderNotRegisteredError: If ``provider`` is given but unknown.
        """

        logger.debug(
            "Catalog search",
            extra={"text": text, "provider_filter": provider},
        )
        if provider is not None:
            adapter = self._get_adapter(provider)
            provider_results = adapter.search_datasets(text)
            logger.debug(
                "Catalog search result",
                extra={"provider": provider, "text": text, "count": len(provider_results)},
            )
            return provider_results

        results: builtins.list[DatasetRef] = []
        for provider_name in self._registry:
            adapter = self._get_adapter(provider_name)
            results.extend(adapter.search_datasets(text))
        logger.debug(
            "Catalog search result",
            extra={"provider": None, "text": text, "count": len(results)},
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
