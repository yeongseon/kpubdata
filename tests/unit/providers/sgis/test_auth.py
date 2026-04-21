from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.exceptions import AuthError, ConfigError
from kpubdata.providers.sgis.auth import SgisAuthClient
from kpubdata.transport.http import HttpTransport


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parents[3] / "fixtures" / "sgis" / name


def _load_fixture(name: str) -> dict[str, object]:
    payload = cast(object, json.loads(_fixture_path(name).read_text(encoding="utf-8")))
    if isinstance(payload, dict):
        return cast(dict[str, object], payload)
    raise ValueError(f"Fixture must be object: {name}")


class _FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.headers: dict[str, str] = {"content-type": "application/json"}
        self.text: str = json.dumps(payload, ensure_ascii=False)
        self.content: bytes = self.text.encode("utf-8")


class _FakeTransport:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self._responses: list[_FakeResponse] = list(responses)
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> _FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        if not self._responses:
            raise AssertionError("No fixture responses remaining")
        return self._responses.pop(0)


def _build_auth_client(
    responses: list[_FakeResponse],
    *,
    provider_key: str,
) -> tuple[SgisAuthClient, _FakeTransport]:
    transport = _FakeTransport(responses)
    config = KPubDataConfig(provider_keys={"sgis": provider_key})
    return (
        SgisAuthClient(
            config=config,
            transport=cast(HttpTransport, cast(object, transport)),
        ),
        transport,
    )


def test_get_access_token_uses_consumer_secret_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KPUBDATA_SGIS_CONSUMER_SECRET", "env-secret")
    auth_client, transport = _build_auth_client(
        [_FakeResponse(_load_fixture("auth_success.json"))],
        provider_key="consumer-key-only",
    )

    token = auth_client.get_access_token()

    assert token == "test-access-token-1"
    request_params = cast(dict[str, str], transport.calls[0]["params"])
    assert request_params["consumer_key"] == "consumer-key-only"
    assert request_params["consumer_secret"] == "env-secret"


def test_get_access_token_uses_key_and_secret_from_provider_key() -> None:
    auth_client, transport = _build_auth_client(
        [_FakeResponse(_load_fixture("auth_success.json"))],
        provider_key="consumer-key:consumer-secret",
    )

    token = auth_client.get_access_token()

    assert token == "test-access-token-1"
    request_params = cast(dict[str, str], transport.calls[0]["params"])
    assert request_params["consumer_key"] == "consumer-key"
    assert request_params["consumer_secret"] == "consumer-secret"


def test_get_access_token_raises_on_auth_error() -> None:
    auth_client, _ = _build_auth_client(
        [_FakeResponse(_load_fixture("error_invalid_token.json"))],
        provider_key="consumer-key:consumer-secret",
    )

    with pytest.raises(AuthError):
        _ = auth_client.get_access_token()


def test_get_access_token_caches_until_invalidate() -> None:
    auth_client, transport = _build_auth_client(
        [_FakeResponse(_load_fixture("auth_success.json"))],
        provider_key="consumer-key:consumer-secret",
    )

    first = auth_client.get_access_token()
    second = auth_client.get_access_token()

    assert first == second
    assert len(transport.calls) == 1


def test_get_access_token_refreshes_after_invalidate() -> None:
    auth_success = _load_fixture("auth_success.json")
    auth_success_2 = dict(auth_success)
    auth_success_2["result"] = {
        "accessToken": "test-access-token-2",
        "accessTimeout": "4102444800",
    }

    auth_client, transport = _build_auth_client(
        [_FakeResponse(auth_success), _FakeResponse(auth_success_2)],
        provider_key="consumer-key:consumer-secret",
    )

    first = auth_client.get_access_token()
    auth_client.invalidate()
    second = auth_client.get_access_token()

    assert first == "test-access-token-1"
    assert second == "test-access-token-2"
    assert len(transport.calls) == 2


def test_get_access_token_requires_secret_when_env_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KPUBDATA_SGIS_CONSUMER_SECRET", raising=False)
    auth_client, _ = _build_auth_client(
        [_FakeResponse(_load_fixture("auth_success.json"))],
        provider_key="consumer-key-only",
    )

    with pytest.raises(ConfigError):
        _ = auth_client.get_access_token()
