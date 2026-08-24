"""테스트 모듈.

이 파일은 ``tests/unit/transport/test_logging.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, cast
from unittest.mock import patch

import httpx
import pytest

import kpubdata.transport.http as http_module
from kpubdata.exceptions import TransportError, TransportTimeoutError
from kpubdata.transport.http import HttpTransport, TransportConfig


def _response_with_content(content: bytes, content_type: str) -> httpx.Response:
    """
    내부 헬퍼로서 response with content 처리를 담당한다.

    매개변수:
        content (bytes): 호출자가 제공하는 입력 값이다.
        content_type (str): 호출자가 제공하는 입력 값이다.

    반환값:
        httpx.Response: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    request = httpx.Request("GET", "https://example.test/resource")
    return httpx.Response(
        status_code=200,
        headers={"content-type": content_type},
        content=content,
        request=request,
    )


# test request params log redacts service key 테스트가 검증하는 시나리오를 설명한다.
def test_request_params_log_redacts_service_key(caplog: pytest.LogCaptureFixture) -> None:
    """
    test request params log redacts service key 시나리오를 검증한다.

    매개변수:
        caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    transport = HttpTransport(TransportConfig(max_retries=0))
    response = _response_with_content(b'{"ok": true}', "application/json")
    caplog.set_level(logging.DEBUG, logger="kpubdata.transport")

    with patch("kpubdata.transport.http.httpx.Client.send", return_value=response):
        _ = transport.request(
            "GET",
            "https://example.test/resource",
            params={"serviceKey": "super-secret", "query": "station"},
        )

    param_records = [record for record in caplog.records if record.message == "HTTP request params"]
    assert len(param_records) == 1
    params = cast(dict[str, str], cast(Any, param_records[0]).params)
    assert params == {"serviceKey": "[REDACTED]", "query": "station"}


# test response preview logged and truncated 테스트가 검증하는 시나리오를 설명한다.
def test_response_preview_logged_and_truncated(caplog: pytest.LogCaptureFixture) -> None:
    """
    test response preview logged and truncated 시나리오를 검증한다.

    매개변수:
        caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    transport = HttpTransport(TransportConfig(max_retries=0))
    long_text = "a" * 900
    response = _response_with_content(long_text.encode("utf-8"), "text/plain; charset=utf-8")
    caplog.set_level(logging.DEBUG, logger="kpubdata.transport")

    with patch("kpubdata.transport.http.httpx.Client.send", return_value=response):
        _ = transport.request("GET", "https://example.test/resource")

    preview_records = [
        record for record in caplog.records if record.message == "HTTP response preview"
    ]
    assert len(preview_records) == 1
    content_length = cast(int, cast(Any, preview_records[0]).content_length)
    preview = cast(str, cast(Any, preview_records[0]).preview)
    assert content_length == 900
    assert preview == long_text[:500]
    assert len(preview) == 500


# test sanitize params redacts sensitive keys 테스트가 검증하는 시나리오를 설명한다.
def test_sanitize_params_redacts_sensitive_keys() -> None:
    """
    test sanitize params redacts sensitive keys 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    sanitize_params = cast(
        Callable[[dict[str, object] | None], dict[str, str]],
        http_module._sanitize_params,
    )
    sanitized = sanitize_params(
        {
            "serviceKey": "a",
            "SERVICE_KEY": "b",
            "api_key": "c",
            "apikey": "d",
            "token": "e",
            "Authorization": "f",
            "secret": "g",
            "password": "h",
            "KEY": "i",
            "query": "station",
        }
    )

    assert sanitized == {
        "serviceKey": "[REDACTED]",
        "SERVICE_KEY": "[REDACTED]",
        "api_key": "[REDACTED]",
        "apikey": "[REDACTED]",
        "token": "[REDACTED]",
        "Authorization": "[REDACTED]",
        "secret": "[REDACTED]",
        "password": "[REDACTED]",
        "KEY": "[REDACTED]",
        "query": "station",
    }


# test response preview handles text and binary content 테스트가 검증하는 시나리오를 설명한다.
def test_response_preview_handles_text_and_binary_content() -> None:
    """
    test response preview handles text and binary content 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    response_preview = cast(Callable[[httpx.Response], str], http_module._response_preview)
    text_response = _response_with_content(b'{"count": 1}', "application/json")
    binary_response = _response_with_content(b"\x00\x01\x02\x03", "application/octet-stream")

    assert response_preview(text_response) == '{"count": 1}'
    assert response_preview(binary_response) == "[binary content, 4 bytes]"


# test debug gating skips sanitization and preview helpers 테스트가 검증하는 시나리오를 설명한다.
def test_debug_gating_skips_sanitization_and_preview_helpers() -> None:
    """
    test debug gating skips sanitization and preview helpers 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    transport = HttpTransport(TransportConfig(max_retries=0))
    response = _response_with_content(b"ok", "text/plain")

    with (
        patch("kpubdata.transport.http.logger.isEnabledFor", return_value=False),
        patch(
            "kpubdata.transport.http._sanitize_params",
            side_effect=AssertionError("_sanitize_params should not be called"),
        ),
        patch(
            "kpubdata.transport.http._response_preview",
            side_effect=AssertionError("_response_preview should not be called"),
        ),
        patch("kpubdata.transport.http.httpx.Client.send", return_value=response),
    ):
        _ = transport.request("GET", "https://example.test/resource", params={"serviceKey": "x"})


# test request logs include dataset context 테스트가 검증하는 시나리오를 설명한다.
def test_request_logs_include_dataset_context(caplog: pytest.LogCaptureFixture) -> None:
    """
    test request logs include dataset context 시나리오를 검증한다.

    매개변수:
        caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    transport = HttpTransport(TransportConfig(max_retries=0))
    response = _response_with_content(b'{"ok": true}', "application/json")
    caplog.set_level(logging.DEBUG, logger="kpubdata.transport")

    with patch("kpubdata.transport.http.httpx.Client.send", return_value=response):
        _ = transport.request(
            "GET",
            "https://example.test/resource",
            dataset_id="datago.village_fcst",
            provider="datago",
        )

    for message in {
        "HTTP request start",
        "HTTP request success",
        "HTTP response preview",
    }:
        record = next(record for record in caplog.records if record.getMessage() == message)
        assert record.__dict__["dataset_id"] == "datago.village_fcst"
        assert record.__dict__["provider"] == "datago"


# test mask url redacts sensitive query params 테스트가 검증하는 시나리오를 설명한다.
def test_mask_url_redacts_sensitive_query_params() -> None:
    """
    test mask url redacts sensitive query params 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    mask_url = cast(Callable[[str, tuple[str, ...]], str], http_module._mask_url)

    masked = mask_url(
        "https://api.example.test/data?serviceKey=secret&SERVICE_KEY=other&query=station",
        sensitive_values=(),
    )
    assert masked == (
        "https://api.example.test/data?serviceKey=[REDACTED]&SERVICE_KEY=[REDACTED]&query=station"
    )
    assert mask_url(
        "https://api.example.test/data?query=station",
        sensitive_values=()
    ) == (
        "https://api.example.test/data?query=station"
    )
    assert mask_url(
        "https://api.example.test/data",
        sensitive_values=()
    ) == "https://api.example.test/data"
    assert mask_url(
        "https://[invalid",
        sensitive_values=()
    ) == "[invalid url]"


# test mask url redacts sensitive path segments 테스트가 검증하는 시나리오를 설명한다(#354).
def test_mask_url_redacts_sensitive_path_segments() -> None:
    """
    test mask url redacts sensitive path segments 시나리오를 검증한다(#354).

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        Seoul API 키가 URL 경로에 포함된 경우 마스킹되는지 확인한다.
    """
    mask_url = cast(Callable[[str, tuple[str, ...]], str], http_module._mask_url)

    # Seoul API 형태: http://openapi.seoul.go.kr:8088/{KEY}/json/{service}/...
    api_key = "SECRET-KEY-123"
    masked = mask_url(
        f"http://openapi.seoul.go.kr:8088/{api_key}/json/SearchParkInfoService/1/10",
        sensitive_values=(api_key,),
    )
    assert masked == "http://openapi.seoul.go.kr:8088/[REDACTED]/json/SearchParkInfoService/1/10"
    
    # 민감하지 않은 값은 마스킹되지 않음
    not_masked = mask_url(
        "http://openapi.seoul.go.kr:8088/public/json/SearchParkInfoService/1/10",
        sensitive_values=(api_key,),
    )
    assert not_masked == "http://openapi.seoul.go.kr:8088/public/json/SearchParkInfoService/1/10"
    
    # 경로와 쿼리 모두 마스킹 가능
    mixed_masked = mask_url(
        f"http://api.example.test/{api_key}/data?serviceKey=other-secret",
        sensitive_values=(api_key,),
    )
    assert mixed_masked == "http://api.example.test/[REDACTED]/data?serviceKey=[REDACTED]"


# test exception message masks sensitive query params 테스트가 검증하는 시나리오를 설명한다.
def test_exception_message_masks_sensitive_query_params() -> None:
    """
    test exception message masks sensitive query params 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    transport = HttpTransport(TransportConfig(max_retries=0))
    secret_url = "https://api.example.test/data?serviceKey=super-secret&query=station"
    response = httpx.Response(status_code=403, request=httpx.Request("GET", secret_url))

    with (
        patch("kpubdata.transport.http.httpx.Client.send", return_value=response),
        pytest.raises(TransportError) as excinfo,
    ):
        _ = transport.request("GET", secret_url)

    message = str(excinfo.value)
    assert "super-secret" not in message
    assert "serviceKey=[REDACTED]" in message
    assert "query=station" in message


# test request logs mask sensitive url 테스트가 검증하는 시나리오를 설명한다.
def test_request_logs_mask_sensitive_url(caplog: pytest.LogCaptureFixture) -> None:
    """
    test request logs mask sensitive url 시나리오를 검증한다.

    매개변수:
        caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    transport = HttpTransport(TransportConfig(max_retries=0))
    secret_url = "https://api.example.test/data?serviceKey=super-secret&query=station"
    response = _response_with_content(b'{"ok": true}', "application/json")
    caplog.set_level(logging.DEBUG, logger="kpubdata.transport")

    with patch("kpubdata.transport.http.httpx.Client.send", return_value=response):
        _ = transport.request("GET", secret_url)

    start_records = [
        record for record in caplog.records if record.getMessage() == "HTTP request start"
    ]
    assert len(start_records) == 1
    logged_url = cast(str, cast(Any, start_records[0]).url)
    assert "super-secret" not in logged_url
    assert logged_url == "https://api.example.test/data?serviceKey=[REDACTED]&query=station"


# test status error chain suppressed when url masked 테스트가 검증하는 시나리오를 설명한다.
def test_status_error_chain_suppressed_when_url_masked() -> None:
    """
    test status error chain suppressed when url masked 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        마스킹이 적용된 URL에서 HTTPStatusError가 발생하면 __cause__/__context__를
        남기지 않아 원본 httpx 예외에 든 민감 URL이 traceback에 노출되지 않는다.
    """
    transport = HttpTransport(TransportConfig(max_retries=0))
    secret_url = "https://api.example.test/data?serviceKey=super-secret&query=station"
    response = httpx.Response(status_code=403, request=httpx.Request("GET", secret_url))

    with (
        patch("kpubdata.transport.http.httpx.Client.send", return_value=response),
        pytest.raises(TransportError) as excinfo,
    ):
        _ = transport.request("GET", secret_url)

    assert excinfo.value.__cause__ is None
    assert excinfo.value.__suppress_context__ is True


# test timeout chain suppressed when url masked 테스트가 검증하는 시나리오를 설명한다.
def test_timeout_chain_suppressed_when_url_masked() -> None:
    """
    test timeout chain suppressed when url masked 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        마스킹이 적용된 URL에서 TimeoutException이 발생하면 TransportTimeoutError가
        원본 예외를 __cause__에 남기지 않는다.
    """
    transport = HttpTransport(TransportConfig(max_retries=0))
    secret_url = "https://api.example.test/data?serviceKey=super-secret&query=station"
    timeout_exc = httpx.TimeoutException("timed out", request=httpx.Request("GET", secret_url))

    with (
        patch("kpubdata.transport.http.httpx.Client.send", side_effect=timeout_exc),
        pytest.raises(TransportTimeoutError) as excinfo,
    ):
        _ = transport.request("GET", secret_url)

    assert excinfo.value.__cause__ is None
    assert excinfo.value.__suppress_context__ is True


# test request error chain suppressed when url masked 테스트가 검증하는 시나리오를 설명한다.
def test_request_error_chain_suppressed_when_url_masked() -> None:
    """
    test request error chain suppressed when url masked 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        마스킹이 적용된 URL에서 RequestError가 발생하면 TransportError가
        원본 예외를 __cause__에 남기지 않는다.
    """
    transport = HttpTransport(TransportConfig(max_retries=0))
    secret_url = "https://api.example.test/data?serviceKey=super-secret&query=station"
    request_exc = httpx.ConnectError("connect failed", request=httpx.Request("GET", secret_url))

    with (
        patch("kpubdata.transport.http.httpx.Client.send", side_effect=request_exc),
        pytest.raises(TransportError) as excinfo,
    ):
        _ = transport.request("GET", secret_url)

    assert excinfo.value.__cause__ is None
    assert excinfo.value.__suppress_context__ is True


# test exception chain preserved when url not masked 테스트가 검증하는 시나리오를 설명한다.
def test_exception_chain_preserved_when_url_not_masked() -> None:
    """
    test exception chain preserved when url not masked 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        마스킹이 적용되지 않은 URL에서는 디버깅 편의를 위해 원본 httpx 예외를
        __cause__에 그대로 유지한다.
    """
    transport = HttpTransport(TransportConfig(max_retries=0))
    plain_url = "https://api.example.test/data?query=station"
    response = httpx.Response(status_code=403, request=httpx.Request("GET", plain_url))

    with (
        patch("kpubdata.transport.http.httpx.Client.send", return_value=response),
        pytest.raises(TransportError) as excinfo,
    ):
        _ = transport.request("GET", plain_url)

    assert isinstance(excinfo.value.__cause__, httpx.HTTPStatusError)
