"""KPubData exception hierarchy with structured error context."""

from __future__ import annotations

from typing import Any


class PublicDataError(Exception):
    """Base for all KPubData errors with structured context attributes."""

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        dataset_id: str | None = None,
        operation: str | None = None,
        status_code: int | None = None,
        provider_code: str | None = None,
        retryable: bool = False,
        detail: Any = None,
    ) -> None:
        """Initialize an error with optional provider and transport metadata."""

        super().__init__(message)
        self.provider = provider
        self.dataset_id = dataset_id
        self.operation = operation
        self.status_code = status_code
        self.provider_code = provider_code
        self.retryable = retryable
        self.detail = detail

    def __repr__(self) -> str:
        parts = [f"{type(self).__name__}({self.args[0]!r}"]
        if self.provider:
            parts.append(f"provider={self.provider!r}")
        if self.dataset_id:
            parts.append(f"dataset={self.dataset_id!r}")
        if self.status_code is not None:
            parts.append(f"status={self.status_code}")
        if self.retryable:
            parts.append("retryable=True")
        return ", ".join(parts) + ")"


class ConfigError(PublicDataError):
    """Raised when KPubData configuration is invalid or incomplete."""


class AuthError(PublicDataError):
    """Raised for authentication or authorization failures."""


class TransportError(PublicDataError):
    """Raised for network and transport-layer failures."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        """Initialize a retryable transport error by default."""

        kwargs.setdefault("retryable", True)
        super().__init__(message, **kwargs)


class TransportTimeoutError(TransportError):
    """Raised when a provider request exceeds timeout limits."""


class RateLimitError(TransportError):
    """Raised when the provider rejects requests due to throttling."""


class ServiceUnavailableError(TransportError):
    """Raised when the upstream provider service is temporarily unavailable."""


class ParseError(PublicDataError):
    """Raised when provider payloads cannot be parsed safely."""


class InvalidRequestError(PublicDataError):
    """Raised when query or operation inputs are semantically invalid."""


class ProviderResponseError(PublicDataError):
    """Raised when provider responses violate contract expectations."""


class UnsupportedCapabilityError(PublicDataError):
    """Raised when a requested operation is unsupported for a dataset."""


class DatasetNotFoundError(PublicDataError):
    """Raised when a requested dataset identifier cannot be resolved."""


class ProviderNotRegisteredError(PublicDataError):
    """Raised when a provider key is not present in the registry."""


__all__ = [
    "AuthError",
    "ConfigError",
    "DatasetNotFoundError",
    "InvalidRequestError",
    "ParseError",
    "ProviderNotRegisteredError",
    "ProviderResponseError",
    "PublicDataError",
    "RateLimitError",
    "ServiceUnavailableError",
    "TransportError",
    "TransportTimeoutError",
    "UnsupportedCapabilityError",
]
