"""Client — KPubData의 최상위 진입점."""

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
    """데이터셋 탐색과 바인딩된 작업을 위한 최상위 진입점."""

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
        """명시적인 Provider/전송 설정으로 클라이언트를 초기화한다.

        ``provider_keys``로 인증 정보를 직접 전달하고,
        ``timeout`` 및 ``max_retries``로 전송 동작을 설정한다.
        내장 Provider(datago, bok, kosis, lofin)는 기본적으로 지연 등록된다.
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
        """환경 변수와 명시적 override 값으로 클라이언트를 생성한다."""

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
        """컨텍스트 매니저에 진입하고 전송 클라이언트를 초기화한다."""

        _ = self._transport.__enter__()
        return self

    def __exit__(self, *exc: object) -> None:
        """컨텍스트 매니저를 종료하고 전송 리소스를 닫는다."""

        self.close()

    def close(self) -> None:
        """이 클라이언트가 사용하는 하위 전송 리소스를 닫는다."""

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
        """탐색, 검색, 해석을 위한 카탈로그 인터페이스를 반환한다."""

        return self._catalog

    def dataset(self, dataset_id: str) -> Dataset:
        """정규 식별자로 데이터셋 객체를 바인딩해 반환한다.

        예외:
            DatasetNotFoundError: 데이터셋 ID가 잘못되었거나 알 수 없을 때.
            ProviderNotRegisteredError: Provider가 등록되지 않았을 때.
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
        """이 클라이언트의 레지스트리에 Provider 어댑터를 등록한다.

        예외:
            TypeError: 어댑터가 필요한 프로토콜을 만족하지 않을 때.
            ValueError: Provider가 이미 등록되어 있을 때.
        """

        logger.debug(
            "Registering external provider adapter",
            extra={"adapter_type": type(adapter).__name__},
        )
        self._registry.register(adapter)

    def iter_authenticated_providers(self) -> tuple[ProviderAdapter, ...]:
        """
        iter authenticated providers 동작을 수행한다.

        반환값:
            tuple[ProviderAdapter, ...]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        providers: list[ProviderAdapter] = []
        for provider_name in self._registry:
            adapter = cast(ProviderAdapter, self._registry.get(provider_name))
            if _requires_api_key(adapter):
                providers.append(adapter)
        return tuple(providers)

    def _register_builtin_providers(self) -> None:
        """
        내부 헬퍼로서 register builtin providers 처리를 담당한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
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
                """
                내부 헬퍼로서 make factory 처리를 담당한다.

                매개변수:
                    mod (str): 호출자가 제공하는 입력 값이다.
                    cfg (KPubDataConfig): 호출자가 제공하는 입력 값이다.
                    tpt (HttpTransport): 호출자가 제공하는 입력 값이다.
                    base_transport_config (TransportConfig): 호출자가 제공하는 입력 값이다.
                    owned_transports (list[HttpTransport]): 호출자가 제공하는 입력 값이다.

                반환값:
                    Callable[[], ProviderAdapter]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

                예외:
                    구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
                """
                def _factory() -> ProviderAdapter:
                    """
                    내부 헬퍼로서 factory 처리를 담당한다.

                    반환값:
                        ProviderAdapter: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

                    예외:
                        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
                    """
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
        """알려진 Provider를 포함한 간결한 표현을 반환한다."""

        return f"Client(providers=[{', '.join(self._registry)}])"


__all__ = ["Client"]


_UNSET = object()


def _get_transport_requirements(adapter: ProviderAdapter) -> TransportRequirements | None:
    """
    내부 헬퍼로서 get transport requirements 처리를 담당한다.

    매개변수:
        adapter (ProviderAdapter): 호출자가 제공하는 입력 값이다.

    반환값:
        TransportRequirements | None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    requirements = getattr(adapter, "transport_requirements", None)
    if requirements is None:
        return None
    return cast(TransportRequirements | None, requirements)


def _requires_api_key(adapter: ProviderAdapter) -> bool:
    """
    내부 헬퍼로서 requires api key 처리를 담당한다.

    매개변수:
        adapter (ProviderAdapter): 호출자가 제공하는 입력 값이다.

    반환값:
        bool: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    return cast(bool, getattr(adapter, "requires_api_key", True))


def _resolve_cache(cache: bool | ResponseCache) -> ResponseCache | None:
    """
    내부 헬퍼로서 resolve cache 처리를 담당한다.

    매개변수:
        cache (bool | ResponseCache): 호출자가 제공하는 입력 값이다.

    반환값:
        ResponseCache | None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    if cache is False:
        return None
    if cache is True:
        return ResponseCache()
    return cache


def _resolve_cache_from_env(cache_override: object) -> bool | ResponseCache:
    """
    내부 헬퍼로서 resolve cache from env 처리를 담당한다.

    매개변수:
        cache_override (object): 호출자가 제공하는 입력 값이다.

    반환값:
        bool | ResponseCache: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    if cache_override is not _UNSET:
        return cast(bool | ResponseCache, cache_override)
    if os.environ.get("KPUBDATA_CACHE") != "1":
        return False
    cache_dir = os.environ.get("KPUBDATA_CACHE_DIR")
    if cache_dir:
        return ResponseCache(base_dir=cache_dir)
    return True


def _resolve_cache_ttl(ttl_override: object) -> int:
    """
    내부 헬퍼로서 resolve cache ttl 처리를 담당한다.

    매개변수:
        ttl_override (object): 호출자가 제공하는 입력 값이다.

    반환값:
        int: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    if ttl_override is not _UNSET:
        return cast(int, ttl_override)
    raw_ttl = os.environ.get("KPUBDATA_CACHE_TTL")
    if raw_ttl is None or raw_ttl == "":
        return 86400
    return int(raw_ttl)
