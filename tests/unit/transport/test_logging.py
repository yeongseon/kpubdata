from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, cast
from unittest.mock import patch

import httpx
import pytest

import kpubdata.transport.http as http_module
from kpubdata.transport.http import HttpTransport, TransportConfig


def _response_with_content(content: bytes, content_type: str) -> httpx.Response:
    request = httpx.Request("GET", "https://example.test/resource")
    return httpx.Response(
        status_code=200,
        headers={"content-type": content_type},
        content=content,
        request=request,
    )


def test_request_params_log_redacts_service_key(caplog: pytest.LogCaptureFixture) -> None:
    transport = HttpTransport(TransportConfig(max_retries=0))
    response = _response_with_content(b'{"ok": true}', "application/json")
    caplog.set_level(logging.DEBUG, logger="kpubdata.transport")

    with patch("kpubdata.transport.http.httpx.Client.request", return_value=response):
        _ = transport.request(
            "GET",
            "https://example.test/resource",
            params={"serviceKey": "super-secret", "query": "station"},
        )

    param_records = [record for record in caplog.records if record.message == "HTTP request params"]
    assert len(param_records) == 1
    params = cast(dict[str, str], cast(Any, param_records[0]).params)
    assert params == {"serviceKey": "[REDACTED]", "query": "station"}


def test_response_preview_logged_and_truncated(caplog: pytest.LogCaptureFixture) -> None:
    transport = HttpTransport(TransportConfig(max_retries=0))
    long_text = "a" * 900
    response = _response_with_content(long_text.encode("utf-8"), "text/plain; charset=utf-8")
    caplog.set_level(logging.DEBUG, logger="kpubdata.transport")

    with patch("kpubdata.transport.http.httpx.Client.request", return_value=response):
        _ = transport.request("GET", "https://example.test/resource")

    preview_records = [
        record for record in caplog.records if record.message == "HTTP response preview"
    ]
    assert len(preview_records) == 1
    content_length = cast(int, cast(Any, preview_records[0]).content_length)
    preview = cast(str, cast(Any, preview_records[0]).preview)
    assert content_length == 900
    assert preview == long_text[:500]
    assert len(preview) == 500


def test_sanitize_params_redacts_sensitive_keys() -> None:
    sanitize_params = cast(
        Callable[[dict[str, object] | None], dict[str, str]],
        http_module._sanitize_params,
    )
    sanitized = sanitize_params(
        {
            "serviceKey": "a",
            "SERVICE_KEY": "b",
            "api_key": "c",
            "apikey": "d",
            "token": "e",
            "Authorization": "f",
            "secret": "g",
            "password": "h",
            "KEY": "i",
            "query": "station",
        }
    )

    assert sanitized == {
        "serviceKey": "[REDACTED]",
        "SERVICE_KEY": "[REDACTED]",
        "api_key": "[REDACTED]",
        "apikey": "[REDACTED]",
        "token": "[REDACTED]",
        "Authorization": "[REDACTED]",
        "secret": "[REDACTED]",
        "password": "[REDACTED]",
        "KEY": "[REDACTED]",
        "query": "station",
    }


def test_response_preview_handles_text_and_binary_content() -> None:
    response_preview = cast(Callable[[httpx.Response], str], http_module._response_preview)
    text_response = _response_with_content(b'{"count": 1}', "application/json")
    binary_response = _response_with_content(b"\x00\x01\x02\x03", "application/octet-stream")

    assert response_preview(text_response) == '{"count": 1}'
    assert response_preview(binary_response) == "[binary content, 4 bytes]"


def test_debug_gating_skips_sanitization_and_preview_helpers() -> None:
    transport = HttpTransport(TransportConfig(max_retries=0))
    response = _response_with_content(b"ok", "text/plain")

    with (
        patch("kpubdata.transport.http.logger.isEnabledFor", return_value=False),
        patch(
            "kpubdata.transport.http._sanitize_params",
            side_effect=AssertionError("_sanitize_params should not be called"),
        ),
        patch(
            "kpubdata.transport.http._response_preview",
            side_effect=AssertionError("_response_preview should not be called"),
        ),
        patch("kpubdata.transport.http.httpx.Client.request", return_value=response),
    ):
        _ = transport.request("GET", "https://example.test/resource", params={"serviceKey": "x"})


def test_request_logs_include_dataset_context(caplog: pytest.LogCaptureFixture) -> None:
    transport = HttpTransport(TransportConfig(max_retries=0))
    response = _response_with_content(b'{"ok": true}', "application/json")
    caplog.set_level(logging.DEBUG, logger="kpubdata.transport")

    with patch("kpubdata.transport.http.httpx.Client.request", return_value=response):
        _ = transport.request(
            "GET",
            "https://example.test/resource",
            dataset_id="datago.village_fcst",
            provider="datago",
        )

    for message in {
        "HTTP request start",
        "HTTP request success",
        "HTTP response preview",
    }:
        record = next(record for record in caplog.records if record.getMessage() == message)
        assert record.__dict__["dataset_id"] == "datago.village_fcst"
        assert record.__dict__["provider"] == "datago"
