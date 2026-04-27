from __future__ import annotations

import pytest
from typing_extensions import override

from kpubdata import Client
from kpubdata.config import KPubDataConfig
from kpubdata.providers.krx.adapter import KrxAdapter
from kpubdata.providers.manifest import BUILTIN_PROVIDERS


def test_krx_provider_is_registered_in_builtin_manifest() -> None:
    assert ("krx", "kpubdata.providers.krx", "KrxAdapter") in BUILTIN_PROVIDERS


def test_client_from_env_works_without_krx_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KPUBDATA_KRX_API_KEY", raising=False)
    monkeypatch.delenv("KRX_API_KEY", raising=False)

    client = Client.from_env()

    assert client.datasets.list(provider="krx") == []


def test_krx_adapter_declares_authless_provider() -> None:
    assert KrxAdapter(config=KPubDataConfig()).requires_api_key is False


def test_client_iter_authenticated_providers_excludes_krx_and_includes_bok() -> None:
    client = Client()

    provider_names = {adapter.name for adapter in client.iter_authenticated_providers()}

    assert "krx" not in provider_names
    assert "bok" in provider_names


def test_iter_authenticated_providers_changes_when_krx_requires_key() -> None:
    class StrictKrxAdapter(KrxAdapter):
        requires_api_key: bool = True

        @property
        @override
        def name(self) -> str:
            return "krx_strict"

    client = Client()
    client.register_provider(StrictKrxAdapter(config=KPubDataConfig()))

    provider_names = {adapter.name for adapter in client.iter_authenticated_providers()}

    assert "krx" not in provider_names
    assert "krx_strict" in provider_names
