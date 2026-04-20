from __future__ import annotations

import logging
from pathlib import Path
from typing import cast
from unittest.mock import patch

import httpx
import pytest

from kpubdata.client import Client
from kpubdata.exceptions import TransportError
from kpubdata.transport.cache import ResponseCache, make_cache_key
from kpubdata.transport.http import HttpTransport, TransportConfig


def _response(
    status_code: int = 200,
    *,
    method: str = "GET",
    url: str = "https://example.test/resource",
    content: bytes = b'{"ok": true}',
) -> httpx.Response:
    request = httpx.Request(method, url)
    return httpx.Response(status_code=status_code, content=content, request=request)


def test_response_cache_roundtrip(tmp_path: Path) -> None:
    cache = ResponseCache(base_dir=tmp_path)

    cache.set("abc", b"payload", ttl_seconds=60)

    assert cache.get("abc") == b"payload"


def test_response_cache_expiry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = ResponseCache(base_dir=tmp_path)
    now = 1_700_000_000.0

    monkeypatch.setattr("kpubdata.transport.cache.time.time", lambda: now)
    cache.set("abc", b"payload", ttl_seconds=10)

    monkeypatch.setattr("kpubdata.transport.cache.time.time", lambda: now + 11)
    assert cache.get("abc") is None
    assert not (tmp_path / "abc.json").exists()


def test_response_cache_missing_key_returns_none(tmp_path: Path) -> None:
    cache = ResponseCache(base_dir=tmp_path)

    assert cache.get("missing") is None


def test_make_cache_key_redacts_secret_values() -> None:
    key_one = make_cache_key(
        "GET",
        "https://example.test/resource",
        {"serviceKey": "secret-a", "query": "stations"},
        {"Authorization": "Bearer aaa", "Accept": "application/json"},
    )
    key_two = make_cache_key(
        "GET",
        "https://example.test/resource",
        {"query": "stations", "serviceKey": "secret-b"},
        {"Accept": "application/json", "Authorization": "Bearer bbb"},
    )
    key_three = make_cache_key(
        "GET",
        "https://example.test/resource",
        {"query": "other", "serviceKey": "secret-b"},
        {"Accept": "application/json", "Authorization": "Bearer bbb"},
    )

    assert key_one == key_two
    assert key_one != key_three


def test_response_cache_filesystem_errors_are_swallowed(tmp_path: Path) -> None:
    blocked_path = tmp_path / "blocked"
    _ = blocked_path.write_text("not-a-directory", encoding="utf-8")
    cache = ResponseCache(base_dir=blocked_path)

    cache.set("abc", b"payload", ttl_seconds=60)
    assert cache.get("abc") is None
    cache.clear()
    cache.clear_expired()


def test_http_transport_get_cache_hit_logs_and_skips_network(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    cache = ResponseCache(base_dir=tmp_path)
    transport = HttpTransport(TransportConfig(max_retries=0), cache=cache, cache_ttl_seconds=60)
    response = _response(content=b'{"cached": false}')
    caplog.set_level(logging.DEBUG, logger="kpubdata.transport")

    with patch(
        "kpubdata.transport.http.httpx.Client.request", return_value=response
    ) as request_mock:
        first = transport.request(
            "GET",
            "https://example.test/resource",
            params={"serviceKey": "secret", "page": "1"},
            dataset_id="datago.tour_kor_area",
            provider="datago",
        )
        second = transport.request(
            "GET",
            "https://example.test/resource",
            params={"page": "1", "serviceKey": "rotated-secret"},
            dataset_id="datago.tour_kor_area",
            provider="datago",
        )

    assert first.content == second.content == b'{"cached": false}'
    assert request_mock.call_count == 1

    miss_record = next(
        record for record in caplog.records if record.getMessage() == "transport cache miss; stored"
    )
    hit_record = next(
        record for record in caplog.records if record.getMessage() == "transport cache hit"
    )
    assert miss_record.__dict__["dataset_id"] == "datago.tour_kor_area"
    assert hit_record.__dict__["provider"] == "datago"
    assert miss_record.__dict__["cache_key"] == hit_record.__dict__["cache_key"]


def test_http_transport_post_is_never_cached(tmp_path: Path) -> None:
    cache = ResponseCache(base_dir=tmp_path)
    transport = HttpTransport(TransportConfig(max_retries=0), cache=cache, cache_ttl_seconds=60)
    response = _response(method="POST", content=b'{"created": true}')

    with patch(
        "kpubdata.transport.http.httpx.Client.request", return_value=response
    ) as request_mock:
        _ = transport.request("POST", "https://example.test/resource", content=b"{}")
        _ = transport.request("POST", "https://example.test/resource", content=b"{}")

    assert request_mock.call_count == 2
    assert list(tmp_path.glob("*.json")) == []


def test_http_transport_non_2xx_is_never_cached(tmp_path: Path) -> None:
    cache = ResponseCache(base_dir=tmp_path)
    transport = HttpTransport(TransportConfig(max_retries=0), cache=cache, cache_ttl_seconds=60)
    response = _response(status_code=404)

    with (
        patch("kpubdata.transport.http.httpx.Client.request", return_value=response),
        pytest.raises(TransportError),
    ):
        _ = transport.request("GET", "https://example.test/resource")

    assert list(tmp_path.glob("*.json")) == []


def test_client_from_env_enables_cache_and_honors_overrides(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("KPUBDATA_CACHE", "1")
    monkeypatch.setenv("KPUBDATA_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("KPUBDATA_CACHE_TTL", "12")

    client = Client.from_env()
    transport_config = cast(TransportConfig, client.__dict__["_transport_config"])

    assert transport_config.cache_ttl_seconds == 12
    assert isinstance(transport_config.cache, ResponseCache)
    assert transport_config.cache is not None
    assert transport_config.cache.base_dir == tmp_path


def test_client_from_env_explicit_cache_false_disables_env_cache(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("KPUBDATA_CACHE", "1")
    monkeypatch.setenv("KPUBDATA_CACHE_DIR", str(tmp_path))

    client = Client.from_env(cache=False)
    transport_config = cast(TransportConfig, client.__dict__["_transport_config"])

    assert transport_config.cache is None
