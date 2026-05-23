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
    """
    TestPublicDataError 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/core/test_exceptions.py`` 모듈 안에서 TestPublicDataError의 상태와 동작을 함께 관리한다.
    주요 메서드: test_message, test_context_attrs, test_repr.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    # test message 테스트가 검증하는 시나리오를 설명한다.
    def test_message(self) -> None:
        """
        test message 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        err = PublicDataError("boom")
        assert str(err) == "boom"

    # test context attrs 테스트가 검증하는 시나리오를 설명한다.
    def test_context_attrs(self) -> None:
        """
        test context attrs 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
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

    # test repr 테스트가 검증하는 시나리오를 설명한다.
    def test_repr(self) -> None:
        """
        test repr 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        err = PublicDataError("fail", provider="x", status_code=404)
        r = repr(err)
        assert "PublicDataError" in r
        assert "x" in r
        assert "404" in r


class TestTransportError:
    """
    TestTransportError 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/core/test_exceptions.py`` 모듈 안에서 TestTransportError의 상태와 동작을 함께 관리한다.
    주요 메서드: test_retryable_default, test_retryable_override.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    # test retryable default 테스트가 검증하는 시나리오를 설명한다.
    def test_retryable_default(self) -> None:
        """
        test retryable default 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        err = TransportError("network issue")
        assert err.retryable is True

    # test retryable override 테스트가 검증하는 시나리오를 설명한다.
    def test_retryable_override(self) -> None:
        """
        test retryable override 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        err = TransportError("permanent", retryable=False)
        assert err.retryable is False


class TestHierarchy:
    """
    TestHierarchy 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/core/test_exceptions.py`` 모듈 안에서 TestHierarchy의 상태와 동작을 함께 관리한다.
    주요 메서드: test_transport_timeout_is_transport, test_rate_limit_is_transport, test_service_unavailable_is_transport, test_all_inherit_base, test_catch_base.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    # test transport timeout is transport 테스트가 검증하는 시나리오를 설명한다.
    def test_transport_timeout_is_transport(self) -> None:
        """
        test transport timeout is transport 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        assert issubclass(TransportTimeoutError, TransportError)

    # test rate limit is transport 테스트가 검증하는 시나리오를 설명한다.
    def test_rate_limit_is_transport(self) -> None:
        """
        test rate limit is transport 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        assert issubclass(RateLimitError, TransportError)

    # test service unavailable is transport 테스트가 검증하는 시나리오를 설명한다.
    def test_service_unavailable_is_transport(self) -> None:
        """
        test service unavailable is transport 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        assert issubclass(ServiceUnavailableError, TransportError)

    # test all inherit base 테스트가 검증하는 시나리오를 설명한다.
    def test_all_inherit_base(self) -> None:
        """
        test all inherit base 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
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

    # test catch base 테스트가 검증하는 시나리오를 설명한다.
    def test_catch_base(self) -> None:
        """
        test catch base 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        with pytest.raises(PublicDataError):
            raise DatasetNotFoundError("not found", dataset_id="x.y")
