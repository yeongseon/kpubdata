"""Client — the top-level entry point for KPubData."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import cast

from typing_extensions import override

from kpubdata.catalog import Catalog
from kpubdata.config import KPubDataConfig
from kpubdata.core.dataset import Dataset
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.registry import ProviderRegistry
from kpubdata.transport.http import HttpTransport, TransportConfig, TransportRequirements

logger = logging.getLogger("kpubdata.client")

_BUILTIN_PROVIDERS: tuple[tuple[str, str, str], ...] = (
    ("datago", "kpubdata.providers.datago", "DataGoAdapter"),
    ("bok", "kpubdata.providers.bok", "BokAdapter"),
    ("kosis", "kpubdata.providers.kosis", "KosisAdapter"),
    ("lofin", "kpubdata.providers.lofin", "LofinAdapter"),
    ("localdata", "kpubdata.providers.localdata.adapter", "LocaldataAdapter"),
)


class Client:
    """Top-level entry point for dataset discovery and bound operations."""

    def __init__(
        self,
        *,
        provider_keys: dict[str, str] | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
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
        self._transport_config: TransportConfig = TransportConfig(
            timeout=self._config.timeout,
            max_retries=self._config.max_retries,
        )
        self._transport: HttpTransport = HttpTransport(self._transport_config)
        self._provider_transports: list[HttpTransport] = []
        self._register_builtin_providers()
        self._catalog: Catalog = Catalog(self._registry)
        logger.debug(
            "Client initialized",
            extra={
                "providers": sorted(self._registry),
                "timeout": self._config.timeout,
                "max_retries": self._config.max_retries,
                "explicit_provider_keys": sorted(self._config.provider_keys.keys()),
            },
        )

    @classmethod
    def from_env(cls, **overrides: object) -> Client:
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


def _get_transport_requirements(adapter: ProviderAdapter) -> TransportRequirements | None:
    requirements = getattr(adapter, "transport_requirements", None)
    if requirements is None:
        return None
    return cast(TransportRequirements | None, requirements)
