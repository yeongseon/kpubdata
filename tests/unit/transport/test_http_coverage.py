from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from kpubdata.exceptions import TransportError
from kpubdata.transport.http import HttpTransport, TransportConfig


def _response(status_code: int) -> httpx.Response:
    request = httpx.Request("GET", "https://example.test/resource")
    return httpx.Response(status_code=status_code, request=request)


def _request_error() -> httpx.RequestError:
    request = httpx.Request("GET", "https://example.test/resource")
    return httpx.RequestError("boom", request=request)


def test_repr_reports_configuration_and_client_state() -> None:
    transport = HttpTransport(TransportConfig(timeout=2.5, max_retries=4, retry_backoff_factor=0.2))

    assert "client_initialized=False" in repr(transport)

    transport._client = MagicMock(spec=httpx.Client)
    assert "client_initialized=True" in repr(transport)


def test_client_property_initializes_client_lazily() -> None:
    transport = HttpTransport()
    fake_client = MagicMock(spec=httpx.Client)

    with patch.object(transport, "_build_client", return_value=fake_client) as build_client:
        client = transport.client

    assert client is fake_client
    build_client.assert_called_once_with()


def test_request_rejects_negative_max_retries() -> None:
    transport = HttpTransport(TransportConfig(max_retries=-1))

    with pytest.raises(ValueError, match="max_retries"):
        _ = transport.request("GET", "https://example.test")


def test_request_rejects_negative_retry_backoff_factor() -> None:
    transport = HttpTransport(TransportConfig(max_retries=0, retry_backoff_factor=-0.1))

    with pytest.raises(ValueError, match="retry_backoff_factor"):
        _ = transport.request("GET", "https://example.test")


def test_request_retries_on_request_error_then_succeeds() -> None:
    transport = HttpTransport(TransportConfig(max_retries=1, retry_backoff_factor=0.5))

    with (
        patch("kpubdata.transport.http.httpx.Client.request") as request_mock,
        patch("kpubdata.transport.http.time.sleep") as sleep_mock,
    ):
        request_mock.side_effect = [_request_error(), _response(200)]

        response = transport.request("GET", "https://example.test")

    assert response.status_code == 200
    assert request_mock.call_count == 2
    sleep_mock.assert_called_once_with(0.5)


def test_request_error_exhaustion_raises_transport_error() -> None:
    transport = HttpTransport(TransportConfig(max_retries=2, retry_backoff_factor=0.25))

    with (
        patch("kpubdata.transport.http.httpx.Client.request", side_effect=_request_error()),
        patch("kpubdata.transport.http.time.sleep") as sleep_mock,
        pytest.raises(TransportError, match="Request failed after 3 attempts"),
    ):
        transport.request("GET", "https://example.test")

    assert sleep_mock.call_count == 2


def test_request_unreachable_state_raises_runtime_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import kpubdata.transport.http as http_module

    transport = HttpTransport(TransportConfig(max_retries=0))
    monkeypatch.setattr(http_module, "range", lambda *_args: [], raising=False)

    with pytest.raises(RuntimeError, match="unreachable transport retry state"):
        _ = transport.request("GET", "https://example.test")
