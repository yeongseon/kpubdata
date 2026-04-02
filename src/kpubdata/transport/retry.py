"""Retry utilities with exponential backoff."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

logger = logging.getLogger("kpubdata.transport")


def with_retry(
    fn: Callable[[], T],
    *,
    max_retries: int = 3,
    backoff_factor: float = 0.5,
    retryable_exceptions: tuple[type[BaseException], ...] = (),
) -> T:
    """Execute ``fn`` with exponential backoff retry.

    Args:
        fn: Callable to execute.
        max_retries: Number of retries after the first attempt.
        backoff_factor: Base factor for exponential backoff.
        retryable_exceptions: Exception types that should trigger retries.

    Returns:
        The value returned by ``fn``.

    Raises:
        BaseException: Re-raises the final exception from ``fn``.
        ValueError: If retry configuration values are invalid.
    """
    if max_retries < 0:
        msg = "max_retries must be >= 0"
        raise ValueError(msg)
    if backoff_factor < 0:
        msg = "backoff_factor must be >= 0"
        raise ValueError(msg)

    total_attempts = max_retries + 1
    for attempt in range(1, total_attempts + 1):
        try:
            return fn()
        except retryable_exceptions as exc:
            if attempt >= total_attempts:
                raise

            delay = backoff_factor * (2 ** (attempt - 1))
            logger.debug(
                "Retrying operation after exception",
                extra={
                    "attempt": attempt,
                    "max_retries": max_retries,
                    "delay_seconds": delay,
                    "exception_type": type(exc).__name__,
                },
            )
            time.sleep(delay)

    msg = "unreachable retry state"
    raise RuntimeError(msg)


__all__ = ["with_retry"]
