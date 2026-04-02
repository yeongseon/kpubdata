"""Tests for retry utility."""

from __future__ import annotations

import pytest

from kpubdata.transport.retry import with_retry


class TestWithRetry:
    def test_success_first_try(self) -> None:
        result = with_retry(lambda: 42, retryable_exceptions=(ValueError,))
        assert result == 42

    def test_retry_then_success(self) -> None:
        calls = {"count": 0}

        def flaky() -> str:
            calls["count"] += 1
            if calls["count"] < 3:
                raise ValueError("transient")
            return "ok"

        result = with_retry(
            flaky, max_retries=3, backoff_factor=0.0, retryable_exceptions=(ValueError,)
        )
        assert result == "ok"
        assert calls["count"] == 3

    def test_exhausted_retries(self) -> None:
        def always_fail() -> None:
            raise ValueError("permanent")

        with pytest.raises(ValueError, match="permanent"):
            with_retry(
                always_fail, max_retries=2, backoff_factor=0.0, retryable_exceptions=(ValueError,)
            )

    def test_non_retryable_raises_immediately(self) -> None:
        calls = {"count": 0}

        def fail_type() -> None:
            calls["count"] += 1
            raise TypeError("not retryable")

        with pytest.raises(TypeError):
            with_retry(
                fail_type, max_retries=3, backoff_factor=0.0, retryable_exceptions=(ValueError,)
            )
        assert calls["count"] == 1

    def test_invalid_max_retries(self) -> None:
        with pytest.raises(ValueError, match="max_retries"):
            with_retry(lambda: None, max_retries=-1, retryable_exceptions=())
