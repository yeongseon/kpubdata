"""Client — the top-level entry point for KPubData."""

from __future__ import annotations

from typing import Any

from kpubdata.catalog import Catalog
from kpubdata.config import KPubDataConfig
from kpubdata.core.dataset import Dataset
from kpubdata.registry import ProviderRegistry
from kpubdata.transport.http import HttpTransport, TransportConfig


class Client:
    """Top-level entry point for dataset discovery and bound operations."""

    def __init__(
        self,
        *,
        provider_keys: dict[str, str] | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        **extra: Any,
    ) -> None:
        """Initialize a client with explicit provider and transport configuration.

        Use ``provider_keys`` to supply credentials directly, and configure
        transport behavior with ``timeout`` and ``max_retries``.
        """

        self._config = KPubDataConfig(
            provider_keys=provider_keys or {},
            timeout=timeout,
            max_retries=max_retries,
            extra=dict(extra),
        )
        self._registry = ProviderRegistry()
        self._transport = HttpTransport(
            TransportConfig(timeout=self._config.timeout, max_retries=self._config.max_retries),
        )
        self._catalog = Catalog(self._registry)

    @classmethod
    def from_env(cls, **overrides: Any) -> Client:
        """Create a client from environment variables and explicit overrides."""

        config = KPubDataConfig.from_env(**overrides)
        return cls(
            provider_keys=config.provider_keys,
            timeout=config.timeout,
            max_retries=config.max_retries,
            **config.extra,
        )

    def __enter__(self) -> Client:
        """Enter context manager and initialize transport client."""

        _ = self._transport.__enter__()
        return self

    def __exit__(self, *exc: object) -> None:
        """Exit context manager and close transport resources."""

        self.close()

    def close(self) -> None:
        """Close underlying transport resources for this client."""

        self._transport.close()

    @property
    def datasets(self) -> Catalog:
        """Return catalog interface for discovery, search, and resolution."""

        return self._catalog

    def dataset(self, dataset_id: str) -> Dataset:
        """Bind and return a dataset object by canonical identifier.

        Raises:
            DatasetNotFoundError: If the dataset id is invalid or unknown.
            ProviderNotRegisteredError: If the provider is not registered.
        """

        adapter, ref = self._catalog.resolve(dataset_id)
        return Dataset(ref=ref, adapter=adapter)

    def register_provider(self, adapter: Any) -> None:
        """Register a provider adapter in this client's registry.

        Raises:
            TypeError: If the adapter does not satisfy the required protocol.
            ValueError: If the provider is already registered.
        """

        self._registry.register(adapter)

    def __repr__(self) -> str:
        """Return concise representation with known providers."""

        return f"Client(providers=[{', '.join(self._registry)}])"


__all__ = ["Client"]
