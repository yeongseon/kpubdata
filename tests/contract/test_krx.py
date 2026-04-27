from __future__ import annotations

import pytest

from kpubdata import Client
from kpubdata.providers.manifest import BUILTIN_PROVIDERS


def test_krx_provider_is_registered_in_builtin_manifest() -> None:
    assert ("krx", "kpubdata.providers.krx", "KrxAdapter") in BUILTIN_PROVIDERS


def test_client_from_env_works_without_krx_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KPUBDATA_KRX_API_KEY", raising=False)
    monkeypatch.delenv("KRX_API_KEY", raising=False)

    client = Client.from_env()

    assert client.datasets.list(provider="krx") == []
