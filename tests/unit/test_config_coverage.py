from __future__ import annotations

import os
from unittest.mock import patch

from kpubdata.config import KPubDataConfig


def test_from_env_skips_empty_values() -> None:
    env = {
        "KPUBDATA_DATAGO_API_KEY": "datago-key",
        "KPUBDATA_EMPTY_API_KEY": "",
    }
    with patch.dict(os.environ, env, clear=False):
        config = KPubDataConfig.from_env()

    assert config.provider_keys["datago"] == "datago-key"
    assert "empty" not in config.provider_keys


def test_from_env_provider_overrides_require_string_pairs_and_non_empty_values() -> None:
    env = {"KPUBDATA_DATAGO_API_KEY": "scanned-key"}
    overrides: dict[object, object] = {
        "Data-Go": "override-key",
        "blank": "",
        "nonstr": 123,
        999: "value",
    }
    with patch.dict(os.environ, env, clear=False):
        config = KPubDataConfig.from_env(provider_keys=overrides)

    assert config.provider_keys["data-go"] == "override-key"
    assert "blank" not in config.provider_keys
    assert "nonstr" not in config.provider_keys
    assert "999" not in config.provider_keys


def test_get_provider_key_uses_case_insensitive_explicit_fallback() -> None:
    config = KPubDataConfig(provider_keys={"DaTaGo": "explicit-key"})

    assert config.get_provider_key("datago") == "explicit-key"
