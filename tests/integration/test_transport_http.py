"""테스트 모듈.

이 파일은 ``tests/integration/test_transport_http.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

# pyright: reportImplicitOverride=false, reportPrivateUsage=false
import http.server
import json
import threading
import time
from collections.abc import Generator
from dataclasses import dataclass
from typing import cast

import pytest
from typing_extensions import TypedDict

from kpubdata.exceptions import TransportError, TransportTimeoutError
from kpubdata.transport.decode import decode_json, detect_content_type
from kpubdata.transport.http import HttpTransport, TransportConfig


class Scenario(TypedDict, total=False):
    """
    Scenario 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/integration/test_transport_http.py`` 모듈 안에서 Scenario의 상태와 동작을 함께 관리한다.
    주요 메서드: 없음.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    status: int
    body: str | bytes
    content_type: str
    delay: float


class MockThreadingHTTPServer(http.server.ThreadingHTTPServer):
    """
    MockThreadingHTTPServer 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/integration/test_transport_http.py`` 모듈 안에서 MockThreadingHTTPServer의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    hit_count: int
    hit_lock: threading.Lock
    last_body: bytes
    last_headers: dict[str, str]

    def __init__(
        self,
        server_address: tuple[str, int],
        request_handler: type[http.server.BaseHTTPRequestHandler],
    ) -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        매개변수:
            server_address (tuple[str, int]): 호출자가 제공하는 입력 값이다.
            request_handler (type[http.server.BaseHTTPRequestHandler]): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        super().__init__(server_address, request_handler)
        self.scenarios: list[Scenario] = []
        self.hit_count = 0
        self.hit_lock = threading.Lock()
        self.last_body = b""
        self.last_headers = {}


class MockHandler(http.server.BaseHTTPRequestHandler):
    """
    MockHandler 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/integration/test_transport_http.py`` 모듈 안에서 MockHandler의 상태와 동작을 함께 관리한다.
    주요 메서드: log_message, do_GET, do_POST, _handle_request.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002, ARG002
        """
        기본 HTTP 서버의 표준 출력 로그를 비활성화한다.

        매개변수:
            format (str): BaseHTTPRequestHandler가 전달하는 로그 포맷 문자열이다.
            *args (object): 포맷 문자열에 주입할 위치 인자들이다.

        반환값:
            None: 별도 로그를 남기지 않고 즉시 반환한다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return

    def do_GET(self) -> None:  # noqa: N802
        """GET 요청을 공통 핸들러로 위임한다."""
        self._handle_request()

    def do_POST(self) -> None:  # noqa: N802
        """POST 요청을 공통 핸들러로 위임한다."""
        self._handle_request()

    def _handle_request(self) -> None:
        """
        내부 헬퍼로서 handle request 처리를 담당한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        # 시나리오 큐에서 현재 요청에 대응하는 응답 정의를 가져오고, 관측 가능한 서버 상태를 갱신한다.
        server = cast(MockThreadingHTTPServer, self.server)
        length = int(self.headers.get("Content-Length", "0"))
        request_body = self.rfile.read(length) if length else b""

        with server.hit_lock:
            server.hit_count += 1
            server.last_body = request_body
            server.last_headers = {k.lower(): v for k, v in self.headers.items()}
            scenario: Scenario = server.scenarios.pop(0) if server.scenarios else {}

        # 지연 응답 시나리오를 통해 timeout 및 retry 동작을 재현한다.
        delay = scenario.get("delay", 0.0)
        if delay > 0:
            time.sleep(delay)

        # 응답 본문과 헤더를 구성한 뒤 간단한 in-process 테스트 서버처럼 결과를 반환한다.
        status = scenario.get("status", 200)
        body = scenario.get("body", "")
        payload = body if isinstance(body, bytes) else body.encode("utf-8")
        content_type = scenario.get("content_type", "text/plain; charset=utf-8")

        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()

        try:
            _ = self.wfile.write(payload)
        except BrokenPipeError:
            return


@dataclass
class MockServer:
    """
    MockServer 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/integration/test_transport_http.py`` 모듈 안에서 MockServer의 상태와 동작을 함께 관리한다.
    주요 메서드: hit_count, last_body, last_headers.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    base_url: str
    scenarios: list[Scenario]
    server: MockThreadingHTTPServer

    @property
    def hit_count(self) -> int:
        """
        hit count 동작을 수행한다.

        반환값:
            int: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return self.server.hit_count

    @property
    def last_body(self) -> bytes:
        """
        last body 동작을 수행한다.

        반환값:
            bytes: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return self.server.last_body

    @property
    def last_headers(self) -> dict[str, str]:
        """
        last headers 동작을 수행한다.

        반환값:
            dict[str, str]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return self.server.last_headers


@pytest.fixture
def mock_server() -> Generator[MockServer, None, None]:
    """
    mock server 동작을 수행한다.

    반환값:
        Generator[MockServer, None, None]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    server = MockThreadingHTTPServer(("127.0.0.1", 0), MockHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        yield MockServer(
            base_url=f"http://127.0.0.1:{server.server_port}",
            scenarios=server.scenarios,
            server=server,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)


@pytest.fixture
def transport_config() -> TransportConfig:
    """
    transport config 동작을 수행한다.

    반환값:
        TransportConfig: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    return TransportConfig(timeout=2.0, max_retries=2, retry_backoff_factor=0)


# test get success 테스트가 검증하는 시나리오를 설명한다.
def test_get_success(mock_server: MockServer, transport_config: TransportConfig) -> None:
    """
    test get success 시나리오를 검증한다.

    매개변수:
        mock_server (MockServer): 호출자가 제공하는 입력 값이다.
        transport_config (TransportConfig): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    mock_server.scenarios.append(
        {
            "status": 200,
            "body": '{"ok": true}',
            "content_type": "application/json",
        }
    )

    with HttpTransport(transport_config) as transport:
        response = transport.request("GET", f"{mock_server.base_url}/ok")

    assert response.status_code == 200
    assert response.text == '{"ok": true}'
    assert detect_content_type(response) == "json"
    assert decode_json(response.text) == {"ok": True}


# test post with json body 테스트가 검증하는 시나리오를 설명한다.
def test_post_with_json_body(mock_server: MockServer, transport_config: TransportConfig) -> None:
    """
    test post with json body 시나리오를 검증한다.

    매개변수:
        mock_server (MockServer): 호출자가 제공하는 입력 값이다.
        transport_config (TransportConfig): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    mock_server.scenarios.append({"status": 200, "body": "ok"})

    with HttpTransport(transport_config) as transport:
        response = transport.request(
            "POST",
            f"{mock_server.base_url}/submit",
            json_body={"key": "value"},
        )

    assert response.status_code == 200
    assert json.loads(mock_server.last_body.decode("utf-8")) == {"key": "value"}
    assert mock_server.last_headers["content-type"].startswith("application/json")


# test retry on 500 then success 테스트가 검증하는 시나리오를 설명한다.
def test_retry_on_500_then_success(
    mock_server: MockServer, transport_config: TransportConfig
) -> None:
    """
    test retry on 500 then success 시나리오를 검증한다.

    매개변수:
        mock_server (MockServer): 호출자가 제공하는 입력 값이다.
        transport_config (TransportConfig): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    mock_server.scenarios.extend(
        [
            {"status": 500, "body": "server error"},
            {"status": 200, "body": "ok"},
        ]
    )

    with HttpTransport(transport_config) as transport:
        response = transport.request("GET", f"{mock_server.base_url}/retry-500")

    assert response.status_code == 200
    assert mock_server.hit_count == 2


# test retry on 429 then success 테스트가 검증하는 시나리오를 설명한다.
def test_retry_on_429_then_success(
    mock_server: MockServer, transport_config: TransportConfig
) -> None:
    """
    test retry on 429 then success 시나리오를 검증한다.

    매개변수:
        mock_server (MockServer): 호출자가 제공하는 입력 값이다.
        transport_config (TransportConfig): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    mock_server.scenarios.extend(
        [
            {"status": 429, "body": "rate limited"},
            {"status": 200, "body": "ok"},
        ]
    )

    with HttpTransport(transport_config) as transport:
        response = transport.request("GET", f"{mock_server.base_url}/retry-429")

    assert response.status_code == 200
    assert mock_server.hit_count == 2


# test no retry on 404 테스트가 검증하는 시나리오를 설명한다.
def test_no_retry_on_404(mock_server: MockServer, transport_config: TransportConfig) -> None:
    """
    test no retry on 404 시나리오를 검증한다.

    매개변수:
        mock_server (MockServer): 호출자가 제공하는 입력 값이다.
        transport_config (TransportConfig): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    mock_server.scenarios.append({"status": 404, "body": "not found"})

    with HttpTransport(transport_config) as transport, pytest.raises(TransportError):
        _ = transport.request("GET", f"{mock_server.base_url}/not-found")

    assert mock_server.hit_count == 1


# test timeout then success 테스트가 검증하는 시나리오를 설명한다.
def test_timeout_then_success(mock_server: MockServer) -> None:
    """
    test timeout then success 시나리오를 검증한다.

    매개변수:
        mock_server (MockServer): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    mock_server.scenarios.extend(
        [
            {"status": 200, "body": "slow", "delay": 5.0},
            {"status": 200, "body": "ok"},
        ]
    )
    config = TransportConfig(timeout=0.3, max_retries=2, retry_backoff_factor=0)

    with HttpTransport(config) as transport:
        response = transport.request("GET", f"{mock_server.base_url}/timeout-then-success")

    assert response.status_code == 200
    assert response.text == "ok"
    assert mock_server.hit_count == 2


# test timeout exhausted 테스트가 검증하는 시나리오를 설명한다.
def test_timeout_exhausted(mock_server: MockServer) -> None:
    """
    test timeout exhausted 시나리오를 검증한다.

    매개변수:
        mock_server (MockServer): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    mock_server.scenarios.extend(
        [
            {"status": 200, "body": "slow-1", "delay": 5.0},
            {"status": 200, "body": "slow-2", "delay": 5.0},
            {"status": 200, "body": "slow-3", "delay": 5.0},
        ]
    )
    config = TransportConfig(timeout=0.3, max_retries=2, retry_backoff_factor=0)

    with HttpTransport(config) as transport, pytest.raises(TransportTimeoutError):
        _ = transport.request("GET", f"{mock_server.base_url}/timeout-exhausted")

    assert mock_server.hit_count == 3


# test retryable status exhausted 테스트가 검증하는 시나리오를 설명한다.
def test_retryable_status_exhausted(
    mock_server: MockServer, transport_config: TransportConfig
) -> None:
    """
    test retryable status exhausted 시나리오를 검증한다.

    매개변수:
        mock_server (MockServer): 호출자가 제공하는 입력 값이다.
        transport_config (TransportConfig): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    mock_server.scenarios.extend(
        [
            {"status": 500, "body": "boom-1"},
            {"status": 500, "body": "boom-2"},
            {"status": 500, "body": "boom-3"},
        ]
    )

    with HttpTransport(transport_config) as transport, pytest.raises(TransportError):
        _ = transport.request("GET", f"{mock_server.base_url}/retryable-exhausted")

    assert mock_server.hit_count == 3


# test context manager lifecycle 테스트가 검증하는 시나리오를 설명한다.
def test_context_manager_lifecycle(
    mock_server: MockServer, transport_config: TransportConfig
) -> None:
    """
    test context manager lifecycle 시나리오를 검증한다.

    매개변수:
        mock_server (MockServer): 호출자가 제공하는 입력 값이다.
        transport_config (TransportConfig): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    mock_server.scenarios.append({"status": 200, "body": "ok"})

    transport = HttpTransport(transport_config)
    with transport as t:
        response = t.request("GET", f"{mock_server.base_url}/context")
        assert response.status_code == 200

    assert transport._client is None
