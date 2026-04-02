"""Tests for the exception hierarchy."""

from __future__ import annotations

import pytest

from kpubdata.exceptions import (
    AuthError,
    ConfigError,
    DatasetNotFoundError,
    ProviderNotRegisteredError,
    ProviderResponseError,
    PublicDataError,
    RateLimitError,
    ServiceUnavailableError,
    TransportError,
    TransportTimeoutError,
    UnsupportedCapabilityError,
)


class TestPublicDataError:
    def test_message(self) -> None:
        err = PublicDataError("boom")
        assert str(err) == "boom"

    def test_context_attrs(self) -> None:
        err = PublicDataError(
            "fail",
            provider="datago",
            dataset_id="datago.apt",
            operation="list",
            status_code=500,
            provider_code="ERR01",
            retryable=True,
            detail={"raw": "data"},
        )
        assert err.provider == "datago"
        assert err.dataset_id == "datago.apt"
        assert err.status_code == 500
        assert err.retryable is True

    def test_repr(self) -> None:
        err = PublicDataError("fail", provider="x", status_code=404)
        r = repr(err)
        assert "PublicDataError" in r
        assert "x" in r
        assert "404" in r


class TestTransportError:
    def test_retryable_default(self) -> None:
        err = TransportError("network issue")
        assert err.retryable is True

    def test_retryable_override(self) -> None:
        err = TransportError("permanent", retryable=False)
        assert err.retryable is False


class TestHierarchy:
    def test_transport_timeout_is_transport(self) -> None:
        assert issubclass(TransportTimeoutError, TransportError)

    def test_rate_limit_is_transport(self) -> None:
        assert issubclass(RateLimitError, TransportError)

    def test_service_unavailable_is_transport(self) -> None:
        assert issubclass(ServiceUnavailableError, TransportError)

    def test_all_inherit_base(self) -> None:
        for cls in [
            ConfigError,
            AuthError,
            TransportError,
            TransportTimeoutError,
            RateLimitError,
            ServiceUnavailableError,
            ProviderResponseError,
            UnsupportedCapabilityError,
            DatasetNotFoundError,
            ProviderNotRegisteredError,
        ]:
            assert issubclass(cls, PublicDataError), f"{cls} should inherit PublicDataError"

    def test_catch_base(self) -> None:
        with pytest.raises(PublicDataError):
            raise DatasetNotFoundError("not found", dataset_id="x.y")
