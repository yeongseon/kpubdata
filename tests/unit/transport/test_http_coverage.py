"""테스트 모듈.

이 파일은 ``tests/unit/transport/test_http_coverage.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from kpubdata.exceptions import TransportError
from kpubdata.transport.http import HttpTransport, TransportConfig


def _response(status_code: int) -> httpx.Response:
    """
    내부 헬퍼로서 response 처리를 담당한다.

    매개변수:
        status_code (int): 호출자가 제공하는 입력 값이다.

    반환값:
        httpx.Response: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    request = httpx.Request("GET", "https://example.test/resource")
    return httpx.Response(status_code=status_code, request=request)


def _request_error() -> httpx.RequestError:
    """
    내부 헬퍼로서 request error 처리를 담당한다.

    반환값:
        httpx.RequestError: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    request = httpx.Request("GET", "https://example.test/resource")
    return httpx.RequestError("boom", request=request)


# test repr reports configuration and client state 테스트가 검증하는 시나리오를 설명한다.
def test_repr_reports_configuration_and_client_state() -> None:
    """
    test repr reports configuration and client state 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    transport = HttpTransport(TransportConfig(timeout=2.5, max_retries=4, retry_backoff_factor=0.2))

    assert "client_initialized=False" in repr(transport)

    transport._client = MagicMock(spec=httpx.Client)
    assert "client_initialized=True" in repr(transport)


# test client property initializes client lazily 테스트가 검증하는 시나리오를 설명한다.
def test_client_property_initializes_client_lazily() -> None:
    """
    test client property initializes client lazily 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    transport = HttpTransport()
    fake_client = MagicMock(spec=httpx.Client)

    with patch.object(transport, "_build_client", return_value=fake_client) as build_client:
        client = transport.client

    assert client is fake_client
    build_client.assert_called_once_with()


# test request rejects negative max retries 테스트가 검증하는 시나리오를 설명한다.
def test_request_rejects_negative_max_retries() -> None:
    """
    test request rejects negative max retries 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    transport = HttpTransport(TransportConfig(max_retries=-1))

    with pytest.raises(ValueError, match="max_retries"):
        _ = transport.request("GET", "https://example.test")


# test request rejects negative retry backoff factor 테스트가 검증하는 시나리오를 설명한다.
def test_request_rejects_negative_retry_backoff_factor() -> None:
    """
    test request rejects negative retry backoff factor 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    transport = HttpTransport(TransportConfig(max_retries=0, retry_backoff_factor=-0.1))

    with pytest.raises(ValueError, match="retry_backoff_factor"):
        _ = transport.request("GET", "https://example.test")


# test request retries on request error then succeeds 테스트가 검증하는 시나리오를 설명한다.
def test_request_retries_on_request_error_then_succeeds() -> None:
    """
    test request retries on request error then succeeds 시나리오를 검증한다.

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
        request_mock.side_effect = [_request_error(), _response(200)]

        response = transport.request("GET", "https://example.test")

    assert response.status_code == 200
    assert request_mock.call_count == 2
    sleep_mock.assert_called_once_with(0.5)


# test request error exhaustion raises transport error 테스트가 검증하는 시나리오를 설명한다.
def test_request_error_exhaustion_raises_transport_error() -> None:
    """
    test request error exhaustion raises transport error 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    transport = HttpTransport(TransportConfig(max_retries=2, retry_backoff_factor=0.25))

    with (
        patch("kpubdata.transport.http.httpx.Client.request", side_effect=_request_error()),
        patch("kpubdata.transport.http.time.sleep") as sleep_mock,
        pytest.raises(TransportError, match="Request failed after 3 attempts"),
    ):
        transport.request("GET", "https://example.test")

    assert sleep_mock.call_count == 2


# test request unreachable state raises runtime error 테스트가 검증하는 시나리오를 설명한다.
def test_request_unreachable_state_raises_runtime_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    test request unreachable state raises runtime error 시나리오를 검증한다.

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

    transport = HttpTransport(TransportConfig(max_retries=0))
    monkeypatch.setattr(http_module, "range", lambda *_args: [], raising=False)

    with pytest.raises(RuntimeError, match="unreachable transport retry state"):
        _ = transport.request("GET", "https://example.test")
