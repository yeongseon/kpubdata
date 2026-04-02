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
        """Initialize client state from explicit constructor arguments."""

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
        """Create client from environment variables with explicit overrides."""

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
        """Access dataset discovery catalog."""

        return self._catalog

    def dataset(self, dataset_id: str) -> Dataset:
        """Bind dataset by canonical id like ``provider.dataset_key``."""

        adapter, ref = self._catalog.resolve(dataset_id)
        return Dataset(ref=ref, adapter=adapter, transport=self._transport)

    def register_provider(self, adapter: Any) -> None:
        """Register a provider adapter in the registry."""

        self._registry.register(adapter)

    def __repr__(self) -> str:
        """Return concise representation with known providers."""

        return f"Client(providers=[{', '.join(self._registry)}])"


__all__ = ["Client"]
