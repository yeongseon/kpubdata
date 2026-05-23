"""설정 관리 — 명시적 구성과 환경 변수 기반 로딩.

Provider 키 조회 순서:
1. 생성자에 전달한 명시적 `provider_keys` dict
2. 환경 변수: KPUBDATA_{PROVIDER}_API_KEY (대문자)
3. 환경 변수: {PROVIDER}_API_KEY (대문자, fallback)

data.go.kr 계열 Provider(localdata, lofin, semas)는 모두 "datago" 키를 사용한다.
모든 data.go.kr 기반 Provider에 대해 KPUBDATA_DATAGO_API_KEY를 한 번만 설정하면 된다.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any

from kpubdata.exceptions import ConfigError

_ENV_KEY_PATTERN = re.compile(r"^KPUBDATA_([A-Z0-9_]+)_API_KEY$")
logger = logging.getLogger("kpubdata.config")


@dataclass
class KPubDataConfig:
    """프레임워크 설정."""

    provider_keys: dict[str, str] = field(default_factory=dict)
    timeout: float = 30.0
    max_retries: int = 3
    extra: dict[str, object] = field(default_factory=dict)

    def __repr__(self) -> str:
        """민감 정보를 노출하지 않는 간결한 디버그 표현을 반환한다."""
        providers = sorted(self.provider_keys.keys())
        return (
            "KPubDataConfig("
            f"providers={providers}, "
            f"timeout={self.timeout}, "
            f"max_retries={self.max_retries}, "
            f"extra_keys={sorted(self.extra.keys())}"
            ")"
        )

    def get_provider_key(self, provider: str) -> str | None:
        """문서화된 우선순위에 따라 Provider의 API 키를 조회한다."""
        normalized_provider = _normalize_provider_name(provider)

        explicit = _get_explicit_key(self.provider_keys, normalized_provider)
        if explicit:
            return explicit

        provider_token = _provider_env_token(normalized_provider)
        kpub_var = f"KPUBDATA_{provider_token}_API_KEY"
        value = os.environ.get(kpub_var)
        if value:
            return value

        fallback_var = f"{provider_token}_API_KEY"
        fallback_value = os.environ.get(fallback_var)
        if fallback_value:
            return fallback_value

        return None

    def require_provider_key(self, provider: str) -> str:
        """get_provider_key와 같지만 키가 없으면 ConfigError를 발생시킨다."""
        key = self.get_provider_key(provider)
        if key is not None:
            return key
        logger.debug("Missing provider API key", extra={"provider": provider})
        raise ConfigError(f"Missing provider API key for '{provider}'")

    @classmethod
    def from_env(cls, **overrides: Any) -> KPubDataConfig:
        """환경 변수로부터 설정을 구성한다.

        KPUBDATA_*_API_KEY 패턴을 스캔한다.
        override 값은 kwargs로 전달할 수 있다.
        """
        scanned_keys: dict[str, str] = {}
        for env_name, env_value in os.environ.items():
            match = _ENV_KEY_PATTERN.match(env_name)
            if match is None:
                continue
            if not env_value:
                continue
            provider_name = match.group(1).lower()
            scanned_keys[provider_name] = env_value

        provider_overrides_raw = overrides.pop("provider_keys", None)
        provider_overrides: dict[str, str] = {}
        if isinstance(provider_overrides_raw, dict):
            for key, value in provider_overrides_raw.items():
                if isinstance(key, str) and isinstance(value, str) and value:
                    provider_overrides[_normalize_provider_name(key)] = value

        merged_provider_keys = scanned_keys.copy()
        merged_provider_keys.update(provider_overrides)

        return cls(provider_keys=merged_provider_keys, **overrides)


def _normalize_provider_name(provider: str) -> str:
    """
    내부 헬퍼로서 normalize provider name 처리를 담당한다.

    매개변수:
        provider (str): 호출자가 제공하는 입력 값이다.

    반환값:
        str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    return provider.strip().lower()


def _provider_env_token(provider: str) -> str:
    """
    내부 헬퍼로서 provider env token 처리를 담당한다.

    매개변수:
        provider (str): 호출자가 제공하는 입력 값이다.

    반환값:
        str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    token = re.sub(r"[^A-Za-z0-9]", "_", provider)
    return token.upper()


def _get_explicit_key(provider_keys: dict[str, str], provider: str) -> str | None:
    """
    내부 헬퍼로서 get explicit key 처리를 담당한다.

    매개변수:
        provider_keys (dict[str, str]): 호출자가 제공하는 입력 값이다.
        provider (str): 호출자가 제공하는 입력 값이다.

    반환값:
        str | None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    if provider in provider_keys and provider_keys[provider]:
        return provider_keys[provider]

    for name, value in provider_keys.items():
        if name.lower() == provider and value:
            return value
    return None


__all__ = ["KPubDataConfig"]
