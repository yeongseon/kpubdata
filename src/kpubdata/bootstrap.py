"""Client 조립(bootstrap) 계층 (#230).

\`Client\`에서 Provider/전송 **조립** 관심사를 분리한 팩토리 레이어다 —
Client 본체는 런타임 동작(탐색/질의/생명주기)만 담당하고, 어떤 내장
Provider를 어떻게 등록할지는 이 모듈이 결정한다. 공개 API는 그대로다.
"""

from __future__ import annotations

import importlib
import logging
from collections.abc import Callable
from typing import cast

from kpubdata.config import KPubDataConfig
from kpubdata.core.bridge import CompositeProviderAdapter
from kpubdata.core.executor import SpecDatasetAdapter, SpecExecutor
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.core.spec import SpecDefinition, discover_specs
from kpubdata.providers.manifest import BUILTIN_PROVIDERS
from kpubdata.registry import ProviderRegistry
from kpubdata.transport.http import (
    HttpTransport,
    TransportConfig,
    TransportRequirements,
)


def register_builtin_providers(
    registry: ProviderRegistry,
    *,
    config: KPubDataConfig,
    transport: HttpTransport,
    transport_config: TransportConfig,
    owned_transports: list[HttpTransport],
) -> None:
    """내장 Provider 목록을 지연 로딩 팩토리로 레지스트리에 등록한다.

    매개변수:
        registry: 등록 대상 레지스트리.
        config: Provider 생성에 쓸 프레임워크 설정.
        transport: 요구사항 없는 Provider가 공유할 기본 전송 계층.
        transport_config: Provider별 전용 전송을 만들 때의 기본 설정.
        owned_transports: Provider별 전용 전송이 추가되는 목록 —
            호출자(Client)가 종료 시 함께 닫는다.
    """
    for provider_name, module_path, class_name in BUILTIN_PROVIDERS:
        registry.register_lazy(
            provider_name,
            _make_builtin_factory(
                provider_name,
                module_path,
                class_name,
                config,
                transport,
                transport_config,
                owned_transports,
            ),
            skip_if_exists=True,
        )


def _make_builtin_factory(
    provider_name: str,
    mod: str,
    cls: str,
    cfg: KPubDataConfig,
    tpt: HttpTransport,
    base_transport_config: TransportConfig,
    owned_transports: list[HttpTransport],
) -> Callable[[], ProviderAdapter]:
    """Provider 모듈을 늦게 import하는 어댑터 생성 함수를 만든다."""

    def _factory() -> ProviderAdapter:
        module = importlib.import_module(mod)
        adapter_cls = cast(Callable[..., ProviderAdapter], getattr(module, cls))
        adapter = adapter_cls(config=cfg, transport=tpt)
        final_transport = tpt
        requirements = _get_transport_requirements(adapter)
        # Provider별 SSL/헤더 요구사항이 있으면 별도 HttpTransport를 만들어 붙인다.
        if requirements is not None:
            final_transport = HttpTransport.with_requirements(
                base_transport_config,
                requirements,
            )
            owned_transports.append(final_transport)
            adapter = adapter_cls(config=cfg, transport=final_transport)
        # spec이 있는 Provider는 카탈로그 어댑터와 병합해 spec 우선으로 노출한다(#378).
        return _wrap_with_specs(provider_name, adapter, final_transport, cfg)

    return _factory


def _wrap_with_specs(
    provider_name: str,
    adapter: ProviderAdapter,
    transport: HttpTransport,
    config: KPubDataConfig,
) -> ProviderAdapter:
    """Provider용 spec이 있으면 composite 브릿지로 감싸고, 없으면 원본을 반환한다."""
    specs = _specs_for_provider(provider_name)
    if not specs:
        return adapter
    executor = SpecExecutor(transport, config)
    spec_adapter = SpecDatasetAdapter(provider_name, list(specs), executor)
    logger.info(
        "Wrapping builtin adapter with dataset specs",
        extra={"provider": provider_name, "spec_count": len(specs)},
    )
    return CompositeProviderAdapter(adapter, spec_adapter)


def _specs_for_provider(provider_name: str) -> tuple[SpecDefinition, ...]:
    """번들 spec 중 해당 Provider 것만 모은다."""
    return tuple(spec for spec in discover_specs() if spec.provider == provider_name)


def _get_transport_requirements(adapter: ProviderAdapter) -> TransportRequirements | None:
    """어댑터가 선언한 전송 요구사항을 읽어 반환한다."""
    requirements = getattr(adapter, "transport_requirements", None)
    if requirements is None:
        return None
    return cast(TransportRequirements | None, requirements)


logger = logging.getLogger("kpubdata.bootstrap")

__all__ = ["register_builtin_providers"]
