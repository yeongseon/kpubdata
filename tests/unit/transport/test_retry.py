"""Tests for retry utility."""

from __future__ import annotations

import pytest

from kpubdata.transport.retry import with_retry


class TestWithRetry:
    """
    TestWithRetry 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/transport/test_retry.py`` 모듈 안에서 TestWithRetry의 상태와 동작을 함께 관리한다.
    주요 메서드: test_success_first_try, test_retry_then_success, test_exhausted_retries, test_non_retryable_raises_immediately, test_invalid_max_retries.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    # test success first try 테스트가 검증하는 시나리오를 설명한다.
    def test_success_first_try(self) -> None:
        """
        test success first try 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        result = with_retry(lambda: 42, retryable_exceptions=(ValueError,))
        assert result == 42

    # test retry then success 테스트가 검증하는 시나리오를 설명한다.
    def test_retry_then_success(self) -> None:
        """
        test retry then success 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        calls = {"count": 0}

        def flaky() -> str:
            """
            flaky 동작을 수행한다.

            반환값:
                str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

            예외:
                구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
            """
            calls["count"] += 1
            if calls["count"] < 3:
                raise ValueError("transient")
            return "ok"

        result = with_retry(
            flaky, max_retries=3, backoff_factor=0.0, retryable_exceptions=(ValueError,)
        )
        assert result == "ok"
        assert calls["count"] == 3

    # test exhausted retries 테스트가 검증하는 시나리오를 설명한다.
    def test_exhausted_retries(self) -> None:
        """
        test exhausted retries 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """

        def always_fail() -> None:
            """
            always fail 동작을 수행한다.

            반환값:
                None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

            예외:
                구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
            """
            raise ValueError("permanent")

        with pytest.raises(ValueError, match="permanent"):
            with_retry(
                always_fail, max_retries=2, backoff_factor=0.0, retryable_exceptions=(ValueError,)
            )

    # test non retryable raises immediately 테스트가 검증하는 시나리오를 설명한다.
    def test_non_retryable_raises_immediately(self) -> None:
        """
        test non retryable raises immediately 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        calls = {"count": 0}

        def fail_type() -> None:
            """
            fail type 동작을 수행한다.

            반환값:
                None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

            예외:
                구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
            """
            calls["count"] += 1
            raise TypeError("not retryable")

        with pytest.raises(TypeError):
            with_retry(
                fail_type, max_retries=3, backoff_factor=0.0, retryable_exceptions=(ValueError,)
            )
        assert calls["count"] == 1

    # test invalid max retries 테스트가 검증하는 시나리오를 설명한다.
    def test_invalid_max_retries(self) -> None:
        """
        test invalid max retries 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        with pytest.raises(ValueError, match="max_retries"):
            with_retry(lambda: None, max_retries=-1, retryable_exceptions=())
