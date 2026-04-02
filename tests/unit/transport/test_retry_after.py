from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from unittest.mock import patch

import httpx
import pytest

from kpubdata.exceptions import TransportError
from kpubdata.transport.http import HttpTransport, TransportConfig


def _response(status_code: int, *, retry_after: str | None = None) -> httpx.Response:
    request = httpx.Request("GET", "https://example.test/resource")
    headers = {"Retry-After": retry_after} if retry_after is not None else None
    return httpx.Response(status_code=status_code, headers=headers, request=request)


def test_429_with_retry_after_seconds_uses_header_delay() -> None:
    transport = HttpTransport(TransportConfig(max_retries=1, retry_backoff_factor=0.5))

    with (
        patch("kpubdata.transport.http.httpx.Client.request") as request_mock,
        patch("kpubdata.transport.http.time.sleep") as sleep_mock,
    ):
        request_mock.side_effect = [_response(429, retry_after="2"), _response(200)]

        response = transport.request("GET", "https://example.test/resource")

    assert response.status_code == 200
    assert request_mock.call_count == 2
    sleep_mock.assert_called_once_with(2.0)


def test_429_with_retry_after_http_date_uses_computed_delay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import kpubdata.transport.http as http_module

    fixed_now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    retry_at = fixed_now + timedelta(seconds=4)
    retry_after_header = format_datetime(retry_at, usegmt=True)

    class _FixedDatetime:
        @staticmethod
        def now(_tz: timezone) -> datetime:
            return fixed_now

    monkeypatch.setattr(http_module, "datetime", _FixedDatetime)

    transport = HttpTransport(TransportConfig(max_retries=1, retry_backoff_factor=0.5))

    with (
        patch("kpubdata.transport.http.httpx.Client.request") as request_mock,
        patch("kpubdata.transport.http.time.sleep") as sleep_mock,
    ):
        request_mock.side_effect = [_response(429, retry_after=retry_after_header), _response(200)]

        response = transport.request("GET", "https://example.test/resource")

    assert response.status_code == 200
    assert request_mock.call_count == 2
    sleep_mock.assert_called_once_with(4.0)


def test_429_with_invalid_retry_after_falls_back_to_exponential_backoff() -> None:
    transport = HttpTransport(TransportConfig(max_retries=1, retry_backoff_factor=0.75))

    with (
        patch("kpubdata.transport.http.httpx.Client.request") as request_mock,
        patch("kpubdata.transport.http.time.sleep") as sleep_mock,
    ):
        request_mock.side_effect = [_response(429, retry_after="abc"), _response(200)]

        response = transport.request("GET", "https://example.test/resource")

    assert response.status_code == 200
    sleep_mock.assert_called_once_with(0.75)


def test_429_without_retry_after_uses_exponential_backoff() -> None:
    transport = HttpTransport(TransportConfig(max_retries=1, retry_backoff_factor=0.25))

    with (
        patch("kpubdata.transport.http.httpx.Client.request") as request_mock,
        patch("kpubdata.transport.http.time.sleep") as sleep_mock,
    ):
        request_mock.side_effect = [_response(429), _response(200)]

        response = transport.request("GET", "https://example.test/resource")

    assert response.status_code == 200
    sleep_mock.assert_called_once_with(0.25)


def test_503_with_retry_after_respects_header_delay() -> None:
    transport = HttpTransport(TransportConfig(max_retries=1, retry_backoff_factor=0.5))

    with (
        patch("kpubdata.transport.http.httpx.Client.request") as request_mock,
        patch("kpubdata.transport.http.time.sleep") as sleep_mock,
    ):
        request_mock.side_effect = [_response(503, retry_after="3"), _response(200)]

        response = transport.request("GET", "https://example.test/resource")

    assert response.status_code == 200
    sleep_mock.assert_called_once_with(3.0)


def test_non_retryable_status_does_not_retry_even_with_retry_after() -> None:
    transport = HttpTransport(TransportConfig(max_retries=3, retry_backoff_factor=0.5))

    with (
        patch(
            "kpubdata.transport.http.httpx.Client.request",
            return_value=_response(400, retry_after="9"),
        ) as request_mock,
        patch("kpubdata.transport.http.time.sleep") as sleep_mock,
        pytest.raises(TransportError, match="HTTP status error 400"),
    ):
        _ = transport.request("GET", "https://example.test/resource")

    assert request_mock.call_count == 1
    sleep_mock.assert_not_called()
