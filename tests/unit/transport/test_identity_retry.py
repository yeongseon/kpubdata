"""전송 계층 identity 재시도 단위 테스트 — KorService2류 디코딩 결함 대응(#414).

Content-Encoding 불일치로 httpx.DecodingError가 나면 Accept-Encoding: identity로
1회 재시해 응답을 회수한다. 실제 HttpTransport.request 경로를 통과한다.
"""

from __future__ import annotations

import httpx
import pytest

from kpubdata.exceptions import TransportError
from kpubdata.transport.http import HttpTransport, TransportConfig


class FakeGzipBrokenClient:
    """기본 헤더 요청은 gzip 선언+원시 본문으로 DecodingError를 내고, identity 요청은 정상 응답."""

    def __init__(self, *, always_broken: bool = False) -> None:
        self.sent_accept_encodings: list[str | None] = []
        self.always_broken = always_broken

    def build_request(
        self,
        method: str,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        content: bytes | None = None,
        json: object = None,
    ) -> httpx.Request:
        accept = (headers or {}).get("Accept-Encoding")
        self.sent_accept_encodings.append(accept)
        return httpx.Request(method, url, params=params, headers=headers)

    def send(self, request: httpx.Request, stream: bool = True) -> httpx.Response:
        accept = request.headers.get("accept-encoding")
        if accept == "identity" and not self.always_broken:
            return httpx.Response(200, content=b'{"ok": true}', request=request)
        # gzip 선언 + gzip이 아닌 본문 → httpx가 읽기에서 DecodingError를 발생시킨다.
        return httpx.Response(
            200,
            headers={"Content-Encoding": "gzip"},
            content=b"plain-not-gzip-body",
            request=request,
        )


def _transport_with(client: FakeGzipBrokenClient) -> HttpTransport:
    transport = HttpTransport(config=TransportConfig(timeout=5, max_retries=0, cache=None))
    sentinel = object()
    object.__setattr__(transport, "_client", None)
    transport.__dict__["_client"] = sentinel
    # client 프로퍼티가 _client를 반환하므로 실제 클라이언트 대치
    transport.__dict__["_client"] = client  # type: ignore[assignment]
    return transport


def test_decoding_error_retries_with_identity() -> None:
    """DecodingError 발생 시 identity 헤더 재시도로 응답을 회수한다."""
    client = FakeGzipBrokenClient()
    transport = _transport_with(client)

    response = transport.request("GET", "https://example.test/api", params={"a": "1"})

    assert response.status_code == 200
    assert response.content == b'{"ok": true}'
    assert client.sent_accept_encodings[0] is None
    assert client.sent_accept_encodings[1] == "identity"


def test_identity_failure_raises_transport_error() -> None:
    """identity 재시도에서도 실패하면 TransportError로 종결한다."""
    client = FakeGzipBrokenClient(always_broken=True)
    transport = _transport_with(client)

    with pytest.raises(TransportError):
        transport.request("GET", "https://example.test/api")
