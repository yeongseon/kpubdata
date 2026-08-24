"""Client 조립(bootstrap) 계층 (#230).

\`Client\`에서 Provider/전송 **조립** 관심사를 분리한 팩토리 레이어다 —
Client 본체는 런타임 동작(탐색/질의/생명주기)만 담당하고, 어떤 내장
Provider를 어떻게 등록할지는 이 모듈이 결정한다. 공개 API는 그대로다.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import cast

from kpubdata.config import KPubDataConfig
from kpubdata.core.protocol import ProviderAdapter
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
        requirements = _get_transport_requirements(adapter)
        # 전송 요구사항이 없으면 공용 HttpTransport를 그대로 재사용한다.
        if requirements is None:
            return adapter

        # Provider별 SSL/헤더 요구사항이 있으면 별도 HttpTransport를 만들어 붙인다.
        custom_transport = HttpTransport.with_requirements(
            base_transport_config,
            requirements,
        )
        owned_transports.append(custom_transport)
        return adapter_cls(config=cfg, transport=custom_transport)

    return _factory


def _get_transport_requirements(adapter: ProviderAdapter) -> TransportRequirements | None:
    """어댑터가 선언한 전송 요구사항을 읽어 반환한다."""
    requirements = getattr(adapter, "transport_requirements", None)
    if requirements is None:
        return None
    return cast(TransportRequirements | None, requirements)


__all__ = ["register_builtin_providers"]
