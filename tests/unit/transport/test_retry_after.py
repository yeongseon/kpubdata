"""테스트 모듈.

이 파일은 ``tests/unit/transport/test_retry_after.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from unittest.mock import patch

import httpx
import pytest

from kpubdata.exceptions import TransportError
from kpubdata.transport.http import HttpTransport, TransportConfig


def _response(status_code: int, *, retry_after: str | None = None) -> httpx.Response:
    """
    내부 헬퍼로서 response 처리를 담당한다.

    매개변수:
        status_code (int): 호출자가 제공하는 입력 값이다.
        retry_after (str | None): 호출자가 제공하는 입력 값이다.

    반환값:
        httpx.Response: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    request = httpx.Request("GET", "https://example.test/resource")
    headers = {"Retry-After": retry_after} if retry_after is not None else None
    return httpx.Response(status_code=status_code, headers=headers, request=request)


# test 429 with retry after seconds uses header delay 테스트가 검증하는 시나리오를 설명한다.
def test_429_with_retry_after_seconds_uses_header_delay() -> None:
    """
    test 429 with retry after seconds uses header delay 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    transport = HttpTransport(TransportConfig(max_retries=1, retry_backoff_factor=0.5))

    with (
        patch("kpubdata.transport.http.httpx.Client.request") as request_mock,
        patch("kpubdata.transport.http.time.sleep") as sleep_mock,
    ):
        request_mock.side_effect = [_response(429, retry_after="2"), _response(200)]

        response = transport.request("GET", "https://example.test/resource")

    assert response.status_code == 200
    assert request_mock.call_count == 2
    sleep_mock.assert_called_once_with(2.0)


# test 429 with retry after http date uses computed delay 테스트가 검증하는 시나리오를 설명한다.
def test_429_with_retry_after_http_date_uses_computed_delay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    test 429 with retry after http date uses computed delay 시나리오를 검증한다.

    매개변수:
        monkeypatch (pytest.MonkeyPatch): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    import kpubdata.transport.http as http_module

    fixed_now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    retry_at = fixed_now + timedelta(seconds=4)
    retry_after_header = format_datetime(retry_at, usegmt=True)

    class _FixedDatetime:
        """
        _FixedDatetime 관련 역할을 캡슐화하는 클래스.

        이 클래스는 ``tests/unit/transport/test_retry_after.py`` 모듈 안에서 _FixedDatetime의 상태와 동작을 함께 관리한다.
        주요 메서드: now.

        속성 설명:
            생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
        """

        @staticmethod
        def now(_tz: timezone) -> datetime:
            """
            now 동작을 수행한다.

            매개변수:
                _tz (timezone): 호출자가 제공하는 입력 값이다.

            반환값:
                datetime: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

            예외:
                구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
            """
            return fixed_now

    monkeypatch.setattr(http_module, "datetime", _FixedDatetime)

    transport = HttpTransport(TransportConfig(max_retries=1, retry_backoff_factor=0.5))

    with (
        patch("kpubdata.transport.http.httpx.Client.request") as request_mock,
        patch("kpubdata.transport.http.time.sleep") as sleep_mock,
    ):
        request_mock.side_effect = [_response(429, retry_after=retry_after_header), _response(200)]

        response = transport.request("GET", "https://example.test/resource")

    assert response.status_code == 200
    assert request_mock.call_count == 2
    sleep_mock.assert_called_once_with(4.0)


# test 429 with invalid retry after falls back to exponential backoff 테스트가 검증하는 시나리오를 설명한다.
def test_429_with_invalid_retry_after_falls_back_to_exponential_backoff() -> None:
    """
    test 429 with invalid retry after falls back to exponential backoff 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    transport = HttpTransport(TransportConfig(max_retries=1, retry_backoff_factor=0.75))

    with (
        patch("kpubdata.transport.http.httpx.Client.request") as request_mock,
        patch("kpubdata.transport.http.time.sleep") as sleep_mock,
    ):
        request_mock.side_effect = [_response(429, retry_after="abc"), _response(200)]

        response = transport.request("GET", "https://example.test/resource")

    assert response.status_code == 200
    sleep_mock.assert_called_once_with(0.75)


# test 429 without retry after uses exponential backoff 테스트가 검증하는 시나리오를 설명한다.
def test_429_without_retry_after_uses_exponential_backoff() -> None:
    """
    test 429 without retry after uses exponential backoff 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    transport = HttpTransport(TransportConfig(max_retries=1, retry_backoff_factor=0.25))

    with (
        patch("kpubdata.transport.http.httpx.Client.request") as request_mock,
        patch("kpubdata.transport.http.time.sleep") as sleep_mock,
    ):
        request_mock.side_effect = [_response(429), _response(200)]

        response = transport.request("GET", "https://example.test/resource")

    assert response.status_code == 200
    sleep_mock.assert_called_once_with(0.25)


# test 503 with retry after respects header delay 테스트가 검증하는 시나리오를 설명한다.
def test_503_with_retry_after_respects_header_delay() -> None:
    """
    test 503 with retry after respects header delay 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    transport = HttpTransport(TransportConfig(max_retries=1, retry_backoff_factor=0.5))

    with (
        patch("kpubdata.transport.http.httpx.Client.request") as request_mock,
        patch("kpubdata.transport.http.time.sleep") as sleep_mock,
    ):
        request_mock.side_effect = [_response(503, retry_after="3"), _response(200)]

        response = transport.request("GET", "https://example.test/resource")

    assert response.status_code == 200
    sleep_mock.assert_called_once_with(3.0)


# test non retryable status does not retry even with retry after 테스트가 검증하는 시나리오를 설명한다.
def test_non_retryable_status_does_not_retry_even_with_retry_after() -> None:
    """
    test non retryable status does not retry even with retry after 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    transport = HttpTransport(TransportConfig(max_retries=3, retry_backoff_factor=0.5))

    with (
        patch(
            "kpubdata.transport.http.httpx.Client.request",
            return_value=_response(400, retry_after="9"),
        ) as request_mock,
        patch("kpubdata.transport.http.time.sleep") as sleep_mock,
        pytest.raises(TransportError, match="HTTP status error 400"),
    ):
        _ = transport.request("GET", "https://example.test/resource")

    assert request_mock.call_count == 1
    sleep_mock.assert_not_called()
