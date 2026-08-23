"""지수 백오프를 사용하는 재시도 유틸리티."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")

logger = logging.getLogger("kpubdata.transport")


def with_retry(
    fn: Callable[[], T],
    *,
    max_retries: int = 3,
    backoff_factor: float = 0.5,
    retryable_exceptions: tuple[type[BaseException], ...] = (),
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """지수 백오프 재시도와 함께 ``fn``을 실행한다.

    매개변수:
        fn: 실행할 호출 가능 객체.
        max_retries: 첫 시도 이후 재시도 횟수.
        backoff_factor: 지수 백오프의 기준 계수.
        retryable_exceptions: 재시도를 유발해야 하는 예외 타입들.
        sleep: 재시도 사이의 대기 함수. 기본은 ``time.sleep``이며, 테스트에서
            가짜 sleep을 주입하거나 async 래퍼가 ``asyncio.sleep``을 쓸 수 있다(#270).

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
            sleep(delay)

    msg = "unreachable retry state"
    raise RuntimeError(msg)


async def with_retry_async(
    fn: Callable[[], Awaitable[T]],
    *,
    max_retries: int = 3,
    backoff_factor: float = 0.5,
    retryable_exceptions: tuple[type[BaseException], ...] = (),
) -> T:
    """``with_retry``의 async 버전 — 대기에 ``asyncio.sleep``을 쓴다 (#270).

    이벤트 루프를 차단하지 않으므로 FastAPI/asyncio 기반 소비자(Builder 등)의
    이벤트 루프를 굳지 않게 한다. 재시도 정책·예외 의미론은 동기 버전과 동일하다.
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
            return await fn()
        except retryable_exceptions as exc:
            if attempt >= total_attempts:
                raise

            delay = backoff_factor * (2 ** (attempt - 1))
            logger.debug(
                "Retrying async operation after exception",
                extra={
                    "attempt": attempt,
                    "max_retries": max_retries,
                    "delay_seconds": delay,
                    "exception_type": type(exc).__name__,
                },
            )
            await asyncio.sleep(delay)

    msg = "unreachable retry state"
    raise RuntimeError(msg)


__all__ = ["with_retry", "with_retry_async"]
