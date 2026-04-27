"""Client — the top-level entry point for KPubData."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from typing import cast

from typing_extensions import override

from kpubdata.catalog import Catalog
from kpubdata.config import KPubDataConfig
from kpubdata.core.dataset import Dataset
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.providers.manifest import BUILTIN_PROVIDERS
from kpubdata.registry import ProviderRegistry
from kpubdata.transport.cache import ResponseCache
from kpubdata.transport.http import HttpTransport, TransportConfig, TransportRequirements

logger = logging.getLogger("kpubdata.client")

_BUILTIN_PROVIDERS = BUILTIN_PROVIDERS


class Client:
    """Top-level entry point for dataset discovery and bound operations."""

    def __init__(
        self,
        *,
        provider_keys: dict[str, str] | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        cache: bool | ResponseCache = False,
        cache_ttl_seconds: int = 86400,
        **extra: object,
    ) -> None:
        """Initialize a client with explicit provider and transport configuration.

        Use ``provider_keys`` to supply credentials directly, and configure
        transport behavior with ``timeout`` and ``max_retries``.
        Built-in providers (datago, bok, kosis, lofin) are lazily registered by default.
        """

        self._config: KPubDataConfig = KPubDataConfig(
            provider_keys=provider_keys or {},
            timeout=timeout,
            max_retries=max_retries,
            extra=dict(extra),
        )
        self._registry: ProviderRegistry = ProviderRegistry()
        resolved_cache = _resolve_cache(cache)
        self._transport_config: TransportConfig = TransportConfig(
            timeout=self._config.timeout,
            max_retries=self._config.max_retries,
            cache=resolved_cache,
            cache_ttl_seconds=cache_ttl_seconds,
        )
        self._transport: HttpTransport = HttpTransport(
            self._transport_config,
            cache=resolved_cache,
            cache_ttl_seconds=cache_ttl_seconds,
        )
        self._provider_transports: list[HttpTransport] = []
        self._register_builtin_providers()
        self._catalog: Catalog = Catalog(self._registry)
        logger.debug(
            "Client initialized",
            extra={
                "providers": sorted(self._registry),
                "timeout": self._config.timeout,
                "max_retries": self._config.max_retries,
                "cache_enabled": resolved_cache is not None,
                "cache_ttl_seconds": cache_ttl_seconds,
                "explicit_provider_keys": sorted(self._config.provider_keys.keys()),
            },
        )

    @classmethod
    def from_env(cls, **overrides: object) -> Client:
        """Create a client from environment variables and explicit overrides."""

        cache_override = overrides.pop("cache", _UNSET)
        ttl_override = overrides.pop("cache_ttl_seconds", _UNSET)
        config = KPubDataConfig.from_env(**overrides)
        cache_ttl_seconds = _resolve_cache_ttl(ttl_override)
        return cls(
            provider_keys=config.provider_keys,
            timeout=config.timeout,
            max_retries=config.max_retries,
            cache=_resolve_cache_from_env(cache_override),
            cache_ttl_seconds=cache_ttl_seconds,
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

        logger.debug(
            "Client closing",
            extra={"owned_provider_transports": len(self._provider_transports)},
        )
        self._transport.close()
        for provider_transport in self._provider_transports:
            provider_transport.close()
        self._provider_transports.clear()

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

        logger.debug("Binding dataset", extra={"dataset_id": dataset_id})
        adapter, ref = self._catalog.resolve(dataset_id)
        logger.debug(
            "Dataset bound",
            extra={
                "dataset_id": ref.id,
                "provider": ref.provider,
                "operations": sorted(op.value for op in ref.operations),
            },
        )
        return Dataset(ref=ref, adapter=adapter)

    def register_provider(self, adapter: object) -> None:
        """Register a provider adapter in this client's registry.

        Raises:
            TypeError: If the adapter does not satisfy the required protocol.
            ValueError: If the provider is already registered.
        """

        logger.debug(
            "Registering external provider adapter",
            extra={"adapter_type": type(adapter).__name__},
        )
        self._registry.register(adapter)

    def iter_authenticated_providers(self) -> tuple[ProviderAdapter, ...]:
        providers: list[ProviderAdapter] = []
        for provider_name in self._registry:
            adapter = cast(ProviderAdapter, self._registry.get(provider_name))
            if _requires_api_key(adapter):
                providers.append(adapter)
        return tuple(providers)

    def _register_builtin_providers(self) -> None:
        config = self._config
        transport = self._transport
        transport_config = self._transport_config
        provider_transports = self._provider_transports

        for provider_name, module_path, class_name in _BUILTIN_PROVIDERS:

            def _make_factory(
                mod: str,
                cls: str,
                cfg: KPubDataConfig,
                tpt: HttpTransport,
                base_transport_config: TransportConfig,
                owned_transports: list[HttpTransport],
            ) -> Callable[[], ProviderAdapter]:
                def _factory() -> ProviderAdapter:
                    import importlib

                    module = importlib.import_module(mod)
                    adapter_cls = cast(Callable[..., ProviderAdapter], getattr(module, cls))
                    adapter = adapter_cls(config=cfg, transport=tpt)
                    requirements = _get_transport_requirements(adapter)
                    if requirements is None:
                        return adapter

                    custom_transport = HttpTransport.with_requirements(
                        base_transport_config,
                        requirements,
                    )
                    owned_transports.append(custom_transport)
                    return adapter_cls(config=cfg, transport=custom_transport)

                return _factory

            self._registry.register_lazy(
                provider_name,
                _make_factory(
                    module_path,
                    class_name,
                    config,
                    transport,
                    transport_config,
                    provider_transports,
                ),
                skip_if_exists=True,
            )

    @override
    def __repr__(self) -> str:
        """Return concise representation with known providers."""

        return f"Client(providers=[{', '.join(self._registry)}])"


__all__ = ["Client"]


_UNSET = object()


def _get_transport_requirements(adapter: ProviderAdapter) -> TransportRequirements | None:
    requirements = getattr(adapter, "transport_requirements", None)
    if requirements is None:
        return None
    return cast(TransportRequirements | None, requirements)


def _requires_api_key(adapter: ProviderAdapter) -> bool:
    return cast(bool, getattr(adapter, "requires_api_key", True))


def _resolve_cache(cache: bool | ResponseCache) -> ResponseCache | None:
    if cache is False:
        return None
    if cache is True:
        return ResponseCache()
    return cache


def _resolve_cache_from_env(cache_override: object) -> bool | ResponseCache:
    if cache_override is not _UNSET:
        return cast(bool | ResponseCache, cache_override)
    if os.environ.get("KPUBDATA_CACHE") != "1":
        return False
    cache_dir = os.environ.get("KPUBDATA_CACHE_DIR")
    if cache_dir:
        return ResponseCache(base_dir=cache_dir)
    return True


def _resolve_cache_ttl(ttl_override: object) -> int:
    if ttl_override is not _UNSET:
        return cast(int, ttl_override)
    raw_ttl = os.environ.get("KPUBDATA_CACHE_TTL")
    if raw_ttl is None or raw_ttl == "":
        return 86400
    return int(raw_ttl)
