"""Provider adapter registry with registration-time validation.

Validates that registered adapters conform to the ProviderAdapter protocol
at registration time, not at call time.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from threading import RLock
from typing import Any

from kpubdata.exceptions import ProviderNotRegisteredError

logger = logging.getLogger("kpubdata.registry")

_REQUIRED_METHODS = (
    "list_datasets",
    "search_datasets",
    "get_dataset",
    "query_records",
    "get_schema",
    "call_raw",
)


class ProviderRegistry:
    """Thread-safe registry for provider adapters."""

    def __init__(self) -> None:
        """Initialize empty eager/lazy adapter registries."""
        self._adapters: dict[str, Any] = {}
        self._lazy: dict[str, Any] = {}
        self._lock = RLock()

    def __repr__(self) -> str:
        """Return concise debug representation."""
        with self._lock:
            eager_names = sorted(self._adapters.keys())
            lazy_names = sorted(self._lazy.keys())
        return f"ProviderRegistry(eager={eager_names}, lazy={lazy_names})"

    def register(self, adapter: Any) -> None:
        """Register an adapter instance. Validates protocol conformance."""
        self._validate_adapter(adapter)
        provider_name = str(adapter.name).strip().lower()

        with self._lock:
            if provider_name in self._adapters or provider_name in self._lazy:
                raise ValueError(f"Provider '{provider_name}' is already registered")
            self._adapters[provider_name] = adapter
        logger.debug(
            "Registered eager provider adapter",
            extra={"provider": provider_name, "adapter_type": type(adapter).__name__},
        )

    def register_lazy(self, name: str, factory: Any, *, skip_if_exists: bool = False) -> None:
        """Register a lazy-loaded adapter via callable factory.

        When ``skip_if_exists`` is True, silently skip registration if the
        provider name is already registered (eager or lazy).  This is used
        by ``Client`` to register built-in providers without conflicting
        with user-registered adapters.
        """
        normalized_name = name.strip().lower()
        if not normalized_name:
            msg = "Provider name cannot be empty"
            raise ValueError(msg)
        if not callable(factory):
            msg = "Lazy adapter factory must be callable"
            raise TypeError(msg)

        with self._lock:
            if normalized_name in self._adapters or normalized_name in self._lazy:
                if skip_if_exists:
                    logger.debug(
                        "Skipped lazy registration; provider already present",
                        extra={"provider": normalized_name},
                    )
                    return
                raise ValueError(f"Provider '{normalized_name}' is already registered")
            self._lazy[normalized_name] = factory
        logger.debug(
            "Registered lazy provider adapter",
            extra={"provider": normalized_name},
        )

    def get(self, name: str) -> Any:
        """Retrieve adapter by provider name."""
        normalized_name = name.strip().lower()
        with self._lock:
            adapter = self._adapters.get(normalized_name)
            if adapter is not None:
                return adapter

            factory = self._lazy.pop(normalized_name, None)

        if factory is None:
            logger.debug("Provider lookup failed", extra={"provider": normalized_name})
            raise ProviderNotRegisteredError(f"Provider '{name}' is not registered")

        logger.debug(
            "Materializing lazy provider adapter",
            extra={"provider": normalized_name},
        )
        lazy_adapter = factory()
        self._validate_adapter(lazy_adapter)
        adapter_name = str(lazy_adapter.name).strip().lower()
        if adapter_name != normalized_name:
            raise TypeError(
                f"Lazy adapter name mismatch: expected '{normalized_name}', got '{adapter_name}'"
            )

        with self._lock:
            self._adapters[normalized_name] = lazy_adapter
        logger.debug(
            "Materialized lazy provider adapter",
            extra={
                "provider": normalized_name,
                "adapter_type": type(lazy_adapter).__name__,
            },
        )
        return lazy_adapter

    def __contains__(self, name: str) -> bool:
        """Return True if adapter is registered eagerly or lazily."""
        normalized_name = name.strip().lower()
        with self._lock:
            return normalized_name in self._adapters or normalized_name in self._lazy

    def __iter__(self) -> Iterator[str]:
        """Iterate provider names currently known to the registry."""
        with self._lock:
            names = set(self._adapters.keys()) | set(self._lazy.keys())
        return iter(sorted(names))

    @staticmethod
    def _validate_adapter(adapter: Any) -> None:
        """Check that adapter has required protocol methods."""
        name = getattr(adapter, "name", None)
        if not isinstance(name, str) or not name.strip():
            msg = "Adapter must define a non-empty string attribute 'name'"
            raise TypeError(msg)

        missing = [
            method_name for method_name in _REQUIRED_METHODS if not hasattr(adapter, method_name)
        ]
        if missing:
            raise TypeError(f"Adapter '{name}' is missing required methods: {missing}")

        non_callable = [
            method_name
            for method_name in _REQUIRED_METHODS
            if not callable(getattr(adapter, method_name, None))
        ]
        if non_callable:
            raise TypeError(f"Adapter '{name}' has non-callable required methods: {non_callable}")


__all__ = ["ProviderRegistry"]
