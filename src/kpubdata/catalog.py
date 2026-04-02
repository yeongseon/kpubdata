"""Catalog — dataset discovery, search, and resolution."""

from __future__ import annotations

import builtins
from typing import cast

from kpubdata.core.models import DatasetRef
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.exceptions import DatasetNotFoundError, ProviderNotRegisteredError
from kpubdata.registry import ProviderRegistry


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

        if provider is not None:
            adapter = self._get_adapter(provider)
            return adapter.list_datasets()

        datasets: builtins.list[DatasetRef] = []
        for provider_name in self._registry:
            adapter = self._get_adapter(provider_name)
            datasets.extend(adapter.list_datasets())
        return datasets

    def search(self, text: str, *, provider: str | None = None) -> builtins.list[DatasetRef]:
        """Search datasets by case-insensitive id or name matching.

        Raises:
            ProviderNotRegisteredError: If ``provider`` is given but unknown.
        """

        needle = text.casefold()
        candidates = self.list(provider=provider)
        return [
            dataset
            for dataset in candidates
            if needle in dataset.id.casefold() or needle in dataset.name.casefold()
        ]

    def resolve(self, dataset_id: str) -> tuple[ProviderAdapter, DatasetRef]:
        """Resolve ``provider.dataset_key`` into an adapter and dataset ref.

        Raises:
            DatasetNotFoundError: If the dataset id is malformed or not found.
            ProviderNotRegisteredError: If the provider is not registered.
        """

        provider_name, dataset_key = self._split_dataset_id(dataset_id)
        adapter = self._get_adapter(provider_name)

        try:
            return adapter, adapter.get_dataset(dataset_key)
        except DatasetNotFoundError:
            raise
        except Exception as exc:
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
