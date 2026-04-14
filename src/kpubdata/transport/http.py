"""Thin HTTP transport — session management, retries, timeouts, decode.

This layer does NOT handle:
- Auth injection (adapter responsibility)
- Parameter naming conventions (adapter responsibility)
- Response envelope parsing (adapter responsibility)
- Provider-specific error mapping (adapter responsibility)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import cast

import httpx

from kpubdata.exceptions import TransportError, TransportTimeoutError

logger = logging.getLogger("kpubdata.transport")
_SENSITIVE_PARAM_KEYS = {
    "servicekey",
    "service_key",
    "api_key",
    "apikey",
    "token",
    "authorization",
    "secret",
    "password",
    "key",
}


@dataclass
class TransportConfig:
    """Transport-level configuration."""

    timeout: float = 30.0
    max_retries: int = 3
    retry_backoff_factor: float = 0.5
    headers: dict[str, str] | None = None


class HttpTransport:
    """Managed httpx client with retry, timeout, and structured logging."""

    def __init__(self, config: TransportConfig | None = None) -> None:
        """Initialize transport with optional explicit configuration."""
        self._config = config or TransportConfig()
        self._client: httpx.Client | None = None

    def __enter__(self) -> HttpTransport:
        """Enter context manager and initialize client eagerly."""
        self._client = self._build_client()
        return self

    def __exit__(self, *exc: object) -> None:
        """Exit context manager and close managed client."""
        self.close()

    def __repr__(self) -> str:
        """Return concise debug representation."""
        return (
            "HttpTransport("
            f"timeout={self._config.timeout}, "
            f"max_retries={self._config.max_retries}, "
            f"retry_backoff_factor={self._config.retry_backoff_factor}, "
            f"client_initialized={self._client is not None}"
            ")"
        )

    def _build_client(self) -> httpx.Client:
        return httpx.Client(
            timeout=self._config.timeout,
            headers=self._config.headers or {},
            follow_redirects=True,
        )

    def close(self) -> None:
        """Close client if initialized."""
        if self._client is not None:
            self._client.close()
            self._client = None

    @property
    def client(self) -> httpx.Client:
        """Get lazy-initialized shared ``httpx.Client`` instance."""
        if self._client is None:
            self._client = self._build_client()
        return self._client

    def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        content: bytes | None = None,
        json_body: object = None,
    ) -> httpx.Response:
        """Execute HTTP request with retry logic.

        Returns:
            Raw ``httpx.Response``.

        Raises:
            TransportError: On non-timeout transport failures.
            TransportTimeoutError: On timeout failures.
        """
        if self._config.max_retries < 0:
            msg = "max_retries must be >= 0"
            raise ValueError(msg)
        if self._config.retry_backoff_factor < 0:
            msg = "retry_backoff_factor must be >= 0"
            raise ValueError(msg)

        total_attempts = self._config.max_retries + 1
        for attempt in range(1, total_attempts + 1):
            retry_delay: float | None = None
            try:
                logger.debug(
                    "HTTP request start",
                    extra={
                        "method": method,
                        "url": url,
                        "attempt": attempt,
                        "max_retries": self._config.max_retries,
                    },
                )

                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        "HTTP request params",
                        extra={
                            "method": method,
                            "url": url,
                            "params": _sanitize_params(params),
                        },
                    )

                response = self.client.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=headers,
                    content=content,
                    json=json_body,
                )
                response.raise_for_status()

                logger.debug(
                    "HTTP request success",
                    extra={
                        "method": method,
                        "url": url,
                        "status_code": response.status_code,
                        "attempt": attempt,
                    },
                )

                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        "HTTP response preview",
                        extra={
                            "status_code": response.status_code,
                            "content_type": response.headers.get("content-type", ""),
                            "content_length": len(response.content),
                            "preview": _response_preview(response),
                        },
                    )
                return response

            except httpx.TimeoutException as exc:
                logger.debug(
                    "HTTP request timeout",
                    extra={
                        "method": method,
                        "url": url,
                        "attempt": attempt,
                        "exception_type": type(exc).__name__,
                    },
                )
                if attempt >= total_attempts:
                    raise TransportTimeoutError(
                        f"Request timed out after {attempt} attempts: {method} {url}"
                    ) from exc

            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                logger.debug(
                    "HTTP status error",
                    extra={
                        "method": method,
                        "url": url,
                        "attempt": attempt,
                        "status_code": status_code,
                    },
                )
                if not _is_retryable_status(status_code) or attempt >= total_attempts:
                    raise TransportError(
                        f"HTTP status error {status_code} for {method} {url}"
                    ) from exc

                retry_after = cast(str | None, exc.response.headers.get("Retry-After"))
                if retry_after is not None:
                    retry_delay = _parse_retry_after(retry_after)

            except httpx.RequestError as exc:
                logger.debug(
                    "HTTP request error",
                    extra={
                        "method": method,
                        "url": url,
                        "attempt": attempt,
                        "exception_type": type(exc).__name__,
                    },
                )
                if attempt >= total_attempts:
                    raise TransportError(
                        f"Request failed after {attempt} attempts: {method} {url}"
                    ) from exc

            if retry_delay is not None:
                delay = retry_delay
            else:
                delay = self._config.retry_backoff_factor * (2 ** (attempt - 1))
            logger.debug(
                "Retrying HTTP request",
                extra={
                    "method": method,
                    "url": url,
                    "attempt": attempt,
                    "delay_seconds": delay,
                },
            )
            time.sleep(delay)

        msg = "unreachable transport retry state"
        raise RuntimeError(msg)


def _is_retryable_status(status_code: int) -> bool:
    return status_code == 429 or 500 <= status_code <= 599


def _sanitize_params(params: dict[str, str] | None) -> dict[str, str]:
    if params is None:
        return {}

    sanitized: dict[str, str] = {}
    for key, value in params.items():
        if key.casefold() in _SENSITIVE_PARAM_KEYS:
            sanitized[key] = "[REDACTED]"
        else:
            sanitized[key] = str(value)
    return sanitized


def _response_preview(response: httpx.Response, max_chars: int = 500) -> str:
    content_type = response.headers.get("content-type", "").casefold()
    is_text = (
        content_type.startswith("text/")
        or "json" in content_type
        or "xml" in content_type
        or "javascript" in content_type
    )

    if not is_text:
        return f"[binary content, {len(response.content)} bytes]"

    try:
        return response.text[:max_chars]
    except (LookupError, UnicodeDecodeError, ValueError):
        return "[decode error]"


def _parse_retry_after(header_value: str) -> float | None:
    """Parse Retry-After header value as delay in seconds.

    Supports both delta-seconds and HTTP-date formats per RFC 7231 §7.1.3.
    Returns None if the value cannot be parsed.
    """

    normalized = header_value.strip()

    try:
        return max(float(int(normalized)), 0.0)
    except ValueError:
        pass

    try:
        retry_at = parsedate_to_datetime(normalized)
    except (TypeError, ValueError, IndexError, OverflowError):
        return None

    if retry_at.tzinfo is None:
        retry_at = retry_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    return max((retry_at - now).total_seconds(), 0.0)


__all__ = ["HttpTransport", "TransportConfig"]
