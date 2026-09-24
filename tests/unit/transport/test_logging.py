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
from kpubdata.core.models import Query
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
    mask_url = cast(Callable[[str], str], http_module._mask_url)

    masked = mask_url(
        "https://api.example.test/data?serviceKey=secret&SERVICE_KEY=other&query=station"
    )
    assert masked == (
        "https://api.example.test/data?serviceKey=[REDACTED]&SERVICE_KEY=[REDACTED]&query=station"
    )
    assert mask_url("https://api.example.test/data?query=station") == (
        "https://api.example.test/data?query=station"
    )
    assert mask_url("https://api.example.test/data") == "https://api.example.test/data"
    assert mask_url("https://[invalid") == "[invalid url]"


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


class TestPathSegmentSecretMasking:
    """URL 경로에 실제 값으로 실리는 키의 마스킹 (#354)."""

    def test_path_segment_matching_secret_is_redacted(self) -> None:
        """seoul 형상 URL의 경로 키 세그먼트가 [REDACTED]로 치환된다."""
        from kpubdata.transport.http import _mask_url

        url = "http://openapi.seoul.go.kr:8088/SECRET-KEY-123/json/SearchParkInfoService/1/10"
        masked = _mask_url(url, secret_values=("SECRET-KEY-123",))

        assert "SECRET-KEY-123" not in masked
        assert "[REDACTED]" in masked
        # 서비스명·인덱스는 값이 다르므로 오인 치환되지 않는다.
        assert "SearchParkInfoService" in masked
        assert masked.endswith("/1/10")

    def test_transport_logs_never_contain_path_key(self, caplog) -> None:
        """transport 로그(success/debug)에 경로 키 원문이 남지 않는다."""
        transport = HttpTransport(TransportConfig(max_retries=0))
        response = httpx.Response(
            200,
            text='{"ok": true}',
            request=httpx.Request("GET", "http://openapi.seoul.go.kr:8088/REAL-KEY-9/json/x/1/5"),
        )
        with (
            patch("kpubdata.transport.http.httpx.Client.send", return_value=response),
            caplog.at_level(logging.DEBUG, logger="kpubdata.transport"),
        ):
            transport.request(
                "GET",
                "http://openapi.seoul.go.kr:8088/REAL-KEY-9/json/x/1/5",
                secret_values=("REAL-KEY-9",),
            )

        for record in caplog.records:
            assert "REAL-KEY-9" not in record.getMessage()

    def test_seoul_adapter_passes_its_key_as_secret_value(self, monkeypatch) -> None:
        """seoul adapter가 transport 호출에 실제 키를 secret_values로 넘긴다."""
        import json as json_module

        from kpubdata.config import KPubDataConfig
        from kpubdata.providers.seoul.adapter import SeoulAdapter

        captured: dict[str, object] = {}

        def fake_request(method, url, **kwargs):
            captured.update(kwargs)
            return httpx.Response(
                200,
                text=json_module.dumps(
                    {
                        "SearchParkInfoService": {
                            "list_total_count": 1,
                            "RESULT": {"CODE": "INFO-000"},
                            "row": [{}],
                        }
                    }
                ),
                request=httpx.Request("GET", url),
            )

        adapter = SeoulAdapter(config=KPubDataConfig(provider_keys={"seoul": "SEOUL-SECRET-42"}))
        monkeypatch.setattr(adapter._transport, "request", fake_request)

        dataset = adapter.get_dataset("park_usage")
        _ = adapter.query_records(dataset, Query(page_size=5))

        assert captured.get("secret_values") == ("SEOUL-SECRET-42",)


def test_mask_url_redacts_the_law_oc_key_parameter() -> None:
    """law(국가법령정보)는 API 키를 ``OC`` 파라미터로 보낸다.

    이름만 봐서는 credential로 보이지 않아 마스킹 목록에서 빠져 있었고, 예외
    메시지에 담긴 URL에 키가 평문으로 남았다.
    """
    mask_url = cast(Callable[[str], str], http_module._mask_url)

    masked = mask_url("https://www.law.go.kr/DRF/lawSearch.do?OC=real-law-key&target=law")

    assert "real-law-key" not in masked
    assert "OC=[REDACTED]" in masked
    assert "target=law" in masked


def test_mask_url_redacts_the_oc_parameter_case_insensitively() -> None:
    mask_url = cast(Callable[[str], str], http_module._mask_url)

    assert "real-law-key" not in mask_url("https://law.test/x?oc=real-law-key")


def test_mask_url_redacts_the_sgis_oauth_parameters() -> None:
    """sgis(통계지리정보)는 OAuth 스타일 이름을 쓴다.

    목록은 부분 문자열 매칭이 아니라 정확한 이름이므로 각각 등재해야 한다 —
    ``consumer_key`` 는 ``key`` 를 포함하지만 걸리지 않았다.
    """
    mask_url = cast(Callable[[str], str], http_module._mask_url)

    masked = mask_url(
        "https://sgisapi.kostat.go.kr/OpenAPI3/auth/authentication.json"
        "?consumer_key=real-key&consumer_secret=real-secret&accessToken=real-token"
    )

    for secret in ("real-key", "real-secret", "real-token"):
        assert secret not in masked
    assert masked.count("[REDACTED]") == 3


class TestKeysPassedAsParamsAreAlsoMasked:
    """키를 ``params=`` 로 넘기는 경로의 예외 체인.

    체인을 끊을지 말지를 ``_mask_url(url) != url`` 하나로 판정했다. 그래서 키가
    URL 문자열에 박혀 있을 때만 끊겼고, ``params=`` 로 넘길 때는 URL이 그대로라
    체인이 유지됐다 — httpx 는 예외 메시지에 params 를 합친 **최종** URL을 넣으
    므로, 그 메시지가 ``__cause__`` 를 타고 traceback 에 그대로 남았다.

    그런데 키를 params 로 보내는 것이 오히려 다수다 — datago·localdata·semas·
    sgis 와 spec executor 가 전부 그렇다. 기존 테스트가 전부 URL 문자열 쪽만
    확인해서 드러나지 않았다.
    """

    _SECRET = "SUPERSECRETKEY"
    _URL = "https://apis.data.go.kr/service/rest/data"

    def _forbidden(self) -> httpx.Response:
        request = httpx.Request("GET", self._URL, params={"serviceKey": self._SECRET, "page": "1"})
        return httpx.Response(status_code=403, request=request)

    def test_the_chain_is_broken_when_the_key_travels_in_params(self) -> None:
        transport = HttpTransport(TransportConfig(max_retries=0))

        with (
            patch("kpubdata.transport.http.httpx.Client.send", return_value=self._forbidden()),
            pytest.raises(TransportError) as excinfo,
        ):
            _ = transport.request(
                "GET", self._URL, params={"serviceKey": self._SECRET, "page": "1"}
            )

        assert excinfo.value.__cause__ is None
        assert excinfo.value.__suppress_context__ is True

    def test_the_key_appears_nowhere_in_the_rendered_traceback(self) -> None:
        """``__cause__`` 가 None 인 것만으로는 부족하다 — 실제 출력에 없어야 한다."""
        import traceback

        transport = HttpTransport(TransportConfig(max_retries=0))

        with (
            patch("kpubdata.transport.http.httpx.Client.send", return_value=self._forbidden()),
            pytest.raises(TransportError) as excinfo,
        ):
            _ = transport.request(
                "GET", self._URL, params={"serviceKey": self._SECRET, "page": "1"}
            )

        rendered = "".join(
            traceback.format_exception(
                type(excinfo.value), excinfo.value, excinfo.value.__traceback__
            )
        )
        assert self._SECRET not in rendered

    def test_the_status_code_survives_the_broken_chain(self) -> None:
        """체인을 끊으면 원래 응답도 함께 사라진다 — 상태 코드는 예외가 직접 들어야 한다.

        datago 의 403 안내와 spec executor 의 AuthError 가 이 값을 본다.
        """
        transport = HttpTransport(TransportConfig(max_retries=0))

        with (
            patch("kpubdata.transport.http.httpx.Client.send", return_value=self._forbidden()),
            pytest.raises(TransportError) as excinfo,
        ):
            _ = transport.request(
                "GET", self._URL, params={"serviceKey": self._SECRET, "page": "1"}
            )

        assert excinfo.value.status_code == 403

    def test_a_request_without_any_credential_keeps_its_chain(self) -> None:
        """자격이 없는 요청까지 체인을 끊으면 디버깅만 어려워진다."""
        transport = HttpTransport(TransportConfig(max_retries=0))
        request = httpx.Request("GET", self._URL, params={"page": "1"})
        response = httpx.Response(status_code=403, request=request)

        with (
            patch("kpubdata.transport.http.httpx.Client.send", return_value=response),
            pytest.raises(TransportError) as excinfo,
        ):
            _ = transport.request("GET", self._URL, params={"page": "1"})

        assert isinstance(excinfo.value.__cause__, httpx.HTTPStatusError)

    def test_a_credential_header_also_breaks_the_chain(self) -> None:
        """Authorization 헤더로 인증하는 provider 도 같은 보호를 받아야 한다."""
        transport = HttpTransport(TransportConfig(max_retries=0))
        request = httpx.Request("GET", self._URL)
        response = httpx.Response(status_code=403, request=request)

        with (
            patch("kpubdata.transport.http.httpx.Client.send", return_value=response),
            pytest.raises(TransportError) as excinfo,
        ):
            _ = transport.request(
                "GET", self._URL, headers={"Authorization": f"Bearer {self._SECRET}"}
            )

        assert excinfo.value.__cause__ is None


class TestForbiddenDetectionDoesNotDependOnTheChain:
    """403 판정이 ``__cause__`` 에 의존하면 마스킹과 서로를 무효화한다.

    datago 는 키를 params 로 보내므로, 체인을 끊는 순간 ``__cause__`` 기반
    판정은 아무것도 찾지 못한다 — 사용자는 키 등록 안내 대신 일반 오류를 본다.
    """

    def test_datago_reads_the_status_code(self) -> None:
        from kpubdata.providers.datago.adapter import DataGoAdapter

        chained = TransportError("forbidden", provider="datago", status_code=403)

        assert DataGoAdapter._is_http_403(chained) is True
        assert DataGoAdapter._is_http_403(TransportError("boom", status_code=503)) is False
        assert DataGoAdapter._is_http_403(TransportError("boom")) is False
