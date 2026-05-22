"""지수 백오프를 사용하는 재시도 유틸리티."""

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
    """지수 백오프 재시도와 함께 ``fn``을 실행한다.

    매개변수:
        fn: 실행할 호출 가능 객체.
        max_retries: 첫 시도 이후 재시도 횟수.
        backoff_factor: 지수 백오프의 기준 계수.
        retryable_exceptions: 재시도를 유발해야 하는 예외 타입들.

    반환값:
        ``fn``이 반환한 값.

    예외:
        BaseException: ``fn``에서 발생한 마지막 예외를 다시 발생시킨다.
        ValueError: 재시도 구성 값이 유효하지 않은 경우.
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
