"""Configuration management — explicit construction and environment-based loading.

Key lookup order for provider keys:
1. Explicit `provider_keys` dict passed to constructor
2. Environment variable: KPUBDATA_{PROVIDER}_API_KEY (uppercased)
3. Environment variable: {PROVIDER}_API_KEY (uppercased, fallback)
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
    """Framework configuration."""

    provider_keys: dict[str, str] = field(default_factory=dict)
    timeout: float = 30.0
    max_retries: int = 3
    extra: dict[str, object] = field(default_factory=dict)

    def __repr__(self) -> str:
        """Return concise debug representation without exposing secrets."""
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
        """Look up API key for a provider following documented precedence."""
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
        """Like get_provider_key but raises ConfigError if missing."""
        key = self.get_provider_key(provider)
        if key is not None:
            return key
        logger.debug("Missing provider API key", extra={"provider": provider})
        raise ConfigError(f"Missing provider API key for '{provider}'")

    @classmethod
    def from_env(cls, **overrides: Any) -> KPubDataConfig:
        """Build config from environment variables.

        Scans for KPUBDATA_*_API_KEY patterns.
        Overrides can be passed as kwargs.
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
    return provider.strip().lower()


def _provider_env_token(provider: str) -> str:
    token = re.sub(r"[^A-Za-z0-9]", "_", provider)
    return token.upper()


def _get_explicit_key(provider_keys: dict[str, str], provider: str) -> str | None:
    if provider in provider_keys and provider_keys[provider]:
        return provider_keys[provider]

    for name, value in provider_keys.items():
        if name.lower() == provider and value:
            return value
    return None


__all__ = ["KPubDataConfig"]
