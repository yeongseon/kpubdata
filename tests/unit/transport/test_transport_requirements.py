from __future__ import annotations

from unittest.mock import MagicMock, patch

from kpubdata.transport.http import HttpTransport, TransportConfig, TransportRequirements


def test_transport_requirements_defaults() -> None:
    requirements = TransportRequirements()

    assert requirements.verify_ssl is None
    assert requirements.headers is None
    assert requirements.ssl_context_factory is None


def test_with_requirements_merges_headers_without_mutating_base_config() -> None:
    config = TransportConfig(
        timeout=12.0,
        max_retries=5,
        retry_backoff_factor=0.25,
        headers={"User-Agent": "kpubdata", "Accept": "application/json"},
    )
    requirements = TransportRequirements(headers={"Accept": "application/xml", "X-Test": "1"})

    transport = HttpTransport.with_requirements(config, requirements)

    with patch("kpubdata.transport.http.httpx.Client") as client_cls:
        _ = transport.client

    client_cls.assert_called_once_with(
        timeout=12.0,
        headers={
            "User-Agent": "kpubdata",
            "Accept": "application/xml",
            "X-Test": "1",
        },
        follow_redirects=True,
        verify=True,
    )
    assert config.headers == {"User-Agent": "kpubdata", "Accept": "application/json"}


def test_build_client_calls_ssl_context_factory_when_provided() -> None:
    ssl_context = MagicMock(name="ssl_context")
    ssl_context_factory = MagicMock(return_value=ssl_context)
    transport = HttpTransport(
        requirements=TransportRequirements(ssl_context_factory=ssl_context_factory),
    )

    with patch("kpubdata.transport.http.httpx.Client") as client_cls:
        _ = transport.client

    ssl_context_factory.assert_called_once_with()
    client_cls.assert_called_once_with(
        timeout=30.0,
        headers={},
        follow_redirects=True,
        verify=ssl_context,
    )


def test_build_client_passes_verify_false_when_ssl_verification_disabled() -> None:
    transport = HttpTransport(requirements=TransportRequirements(verify_ssl=False))

    with patch("kpubdata.transport.http.httpx.Client") as client_cls:
        _ = transport.client

    client_cls.assert_called_once_with(
        timeout=30.0,
        headers={},
        follow_redirects=True,
        verify=False,
    )
