"""Tests for config management."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.exceptions import ConfigError


class TestKPubDataConfig:
    def test_explicit_key(self) -> None:
        cfg = KPubDataConfig(provider_keys={"datago": "mykey"})
        assert cfg.get_provider_key("datago") == "mykey"

    def test_missing_key_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("KPUBDATA_DATAGO_API_KEY", raising=False)
        monkeypatch.delenv("DATAGO_API_KEY", raising=False)
        cfg = KPubDataConfig()
        assert cfg.get_provider_key("datago") is None

    def test_require_key_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("KPUBDATA_DATAGO_API_KEY", raising=False)
        monkeypatch.delenv("DATAGO_API_KEY", raising=False)
        cfg = KPubDataConfig()
        with pytest.raises(ConfigError, match="Missing provider API key"):
            cfg.require_provider_key("datago")

    def test_env_kpubdata_prefix(self) -> None:
        cfg = KPubDataConfig()
        with patch.dict(os.environ, {"KPUBDATA_SEOUL_API_KEY": "envkey"}):
            assert cfg.get_provider_key("seoul") == "envkey"

    def test_env_fallback_prefix(self) -> None:
        cfg = KPubDataConfig()
        with patch.dict(os.environ, {"SEOUL_API_KEY": "fallback"}, clear=False):
            # Only if KPUBDATA_ not set
            result = cfg.get_provider_key("seoul")
            assert result is not None

    def test_explicit_takes_precedence(self) -> None:
        cfg = KPubDataConfig(provider_keys={"seoul": "explicit"})
        with patch.dict(os.environ, {"KPUBDATA_SEOUL_API_KEY": "envkey"}):
            assert cfg.get_provider_key("seoul") == "explicit"

    def test_from_env(self) -> None:
        env = {"KPUBDATA_DATAGO_API_KEY": "k1", "KPUBDATA_SEOUL_API_KEY": "k2"}
        with patch.dict(os.environ, env, clear=False):
            cfg = KPubDataConfig.from_env()
            assert "datago" in cfg.provider_keys
            assert "seoul" in cfg.provider_keys

    def test_repr_no_secrets(self) -> None:
        cfg = KPubDataConfig(provider_keys={"datago": "secret123"})
        r = repr(cfg)
        assert "secret123" not in r
        assert "datago" in r
