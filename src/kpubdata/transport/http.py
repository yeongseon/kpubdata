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
from typing import Any

import httpx

from kpubdata.exceptions import TransportError, TransportTimeoutError

logger = logging.getLogger("kpubdata.transport")


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
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        content: bytes | None = None,
        json_body: Any = None,
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


__all__ = ["HttpTransport", "TransportConfig"]
