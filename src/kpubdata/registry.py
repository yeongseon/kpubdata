"""등록 시점 검증을 포함한 Provider 어댑터 레지스트리.

등록된 어댑터가 ProviderAdapter 프로토콜을 만족하는지
호출 시점이 아니라 등록 시점에 검증한다.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from threading import RLock
from typing import Any

from kpubdata.core.models import DatasetRef
from kpubdata.exceptions import CapabilityContractError, ProviderNotRegisteredError

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
    """Provider 어댑터를 위한 스레드 안전 레지스트리."""

    def __init__(self) -> None:
        """비어 있는 eager/lazy 어댑터 레지스트리를 초기화한다."""
        self._adapters: dict[str, Any] = {}
        self._lazy: dict[str, Any] = {}
        self._lock = RLock()

    def __repr__(self) -> str:
        """간결한 디버그 표현을 반환한다."""
        with self._lock:
            eager_names = sorted(self._adapters.keys())
            lazy_names = sorted(self._lazy.keys())
        return f"ProviderRegistry(eager={eager_names}, lazy={lazy_names})"

    def register(self, adapter: Any, *, validate_capabilities: bool = True) -> None:
        """어댑터 인스턴스를 등록한다. 프로토콜 준수 여부를 검증한다.

        ``validate_capabilities=True``(기본값)이면 등록 시점에 ``list_datasets()``를
        한 번 호출해 어댑터의 catalogue가 실제로 로드되는지, 각 dataset이 비어 있지
        않은 ``operations`` 집합을 가지는지(즉 catalogue가 "지원" 거짓 표시를
        하지 않는지)를 fail-fast로 확인한다. 위반 시 ``CapabilityContractError``.

        이름 충돌 검사는 capability 검증보다 먼저 수행한다 — capability 검증은
        ``list_datasets()``를 호출해 catalogue 로드 비용(파일 I/O 등)이 들 수
        있으므로, 어차피 거부될 등록에 그 비용을 지불하지 않는다.
        """
        self._validate_adapter(adapter)
        provider_name = str(adapter.name).strip().lower()

        with self._lock:
            if provider_name in self._adapters or provider_name in self._lazy:
                raise ValueError(f"Provider '{provider_name}' is already registered")

        if validate_capabilities:
            self._validate_capability_contract(adapter)

        with self._lock:
            # capability 검증 동안 다른 스레드가 같은 이름을 등록했을 가능성에 대비해 재확인.
            if provider_name in self._adapters or provider_name in self._lazy:
                raise ValueError(f"Provider '{provider_name}' is already registered")
            self._adapters[provider_name] = adapter
        logger.debug(
            "Registered eager provider adapter",
            extra={"provider": provider_name, "adapter_type": type(adapter).__name__},
        )

    def register_lazy(self, name: str, factory: Any, *, skip_if_exists: bool = False) -> None:
        """호출 가능한 팩토리를 통해 지연 로딩 어댑터를 등록한다.

        ``skip_if_exists``가 True이면 Provider 이름이 이미 등록된 경우(eager 또는 lazy)
        등록을 조용히 건너뛴다. 이는 ``Client``가 사용자 등록 어댑터와 충돌하지 않고
        내장 Provider를 등록할 때 사용된다.
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
        """Provider 이름으로 어댑터를 가져온다."""
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
        self._validate_capability_contract(lazy_adapter)
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
        """어댑터가 eager 또는 lazy로 등록되어 있으면 True를 반환한다."""
        normalized_name = name.strip().lower()
        with self._lock:
            return normalized_name in self._adapters or normalized_name in self._lazy

    def __iter__(self) -> Iterator[str]:
        """현재 레지스트리가 알고 있는 Provider 이름을 순회한다."""
        with self._lock:
            names = set(self._adapters.keys()) | set(self._lazy.keys())
        return iter(sorted(names))

    @staticmethod
    def _validate_adapter(adapter: Any) -> None:
        """어댑터가 필요한 프로토콜 메서드를 갖는지 확인한다."""
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

    @staticmethod
    def _validate_capability_contract(adapter: Any) -> None:
        """어댑터의 catalogue가 정직한 capability 선언을 하는지 fail-fast로 검증한다.

        ``list_datasets()`` 호출 자체가 실패하면 catalogue 로딩이 깨진 상태이므로
        등록 자체를 차단한다. 그리고 노출되는 각 ``DatasetRef``가 비어 있지 않은
        ``operations`` 집합을 갖는지 확인한다 — 빈 operations는 "이 dataset은
        아무 일도 못 한다"는 거짓 표시이기 때문이다.
        """
        provider_name = str(getattr(adapter, "name", "<unknown>"))

        try:
            datasets = adapter.list_datasets()
        except Exception as exc:
            raise CapabilityContractError(
                f"Adapter '{provider_name}' failed to enumerate datasets at registration: {exc}",
                provider=provider_name,
            ) from exc

        if not isinstance(datasets, list):
            raise CapabilityContractError(
                f"Adapter '{provider_name}' list_datasets() must return a list, "
                f"got {type(datasets).__name__}",
                provider=provider_name,
            )

        empty_ops: list[str] = []
        non_ref: list[str] = []
        for entry in datasets:
            if not isinstance(entry, DatasetRef):
                non_ref.append(repr(entry))
                continue
            if not entry.operations:
                empty_ops.append(entry.id)

        if non_ref:
            raise CapabilityContractError(
                f"Adapter '{provider_name}' list_datasets() returned non-DatasetRef entries: "
                f"{non_ref[:3]}",
                provider=provider_name,
            )
        if empty_ops:
            raise CapabilityContractError(
                f"Adapter '{provider_name}' has datasets declaring empty operations: "
                f"{empty_ops[:5]}. An empty operations set is a dishonest capability "
                "declaration — the dataset claims to be supported but exposes no callable "
                "operation.",
                provider=provider_name,
            )


__all__ = ["ProviderRegistry"]
