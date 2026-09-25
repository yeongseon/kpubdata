"""HTTP 200 으로 온 거부를 캐시하지 않는다.

한국 공공 API 다수는 실패를 상태 코드가 아니라 본문 envelope 으로 알린다 —
한도 초과(22), 미등록 키(30), 게이트웨이 거부가 전부 200 이다. transport 가
상태만 보고 캐시하던 시절에는 일시적인 한도 초과가 24시간 장애로 굳었고,
그 캐시는 kpubdata-builder 의 Bronze fetch 로 그대로 전파돼 스케줄 빌드가
빈 데이터를 "성공" 으로 게시할 수 있었다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import httpx
import pytest

from kpubdata.transport._envelope import is_upstream_error_envelope
from kpubdata.transport.cache import ResponseCache
from kpubdata.transport.http import HttpTransport, TransportConfig

_JSON = "application/json"
_XML = "text/xml"


class TestRecognisingAnErrorEnvelope:
    @pytest.mark.parametrize(
        ("label", "body", "content_type"),
        [
            ("서비스 한도 초과", b'{"response":{"header":{"resultCode":"22"}}}', _JSON),
            (
                "게이트웨이 미등록 키",
                b'{"OpenAPI_ServiceResponse":{"cmmMsgHeader":{"returnReasonCode":"30"}}}',
                _JSON,
            ),
            ("최상단 resultCode", b'{"resultCode":"12"}', _JSON),
            (
                "XML 한도 초과",
                b"<response><header><resultCode>22</resultCode></header></response>",
                _XML,
            ),
            (
                "XML 게이트웨이",
                b"<cmmMsgHeader><returnReasonCode>30</returnReasonCode></cmmMsgHeader>",
                _XML,
            ),
        ],
    )
    def test_failures_are_recognised(self, label: str, body: bytes, content_type: str) -> None:
        assert is_upstream_error_envelope(body, content_type), label

    @pytest.mark.parametrize(
        ("label", "body", "content_type"),
        [
            ("정상 00", b'{"response":{"header":{"resultCode":"00"}}}', _JSON),
            ("정상 000", b'{"response":{"header":{"resultCode":"000"}}}', _JSON),
            ("정수 0", b'{"response":{"header":{"resultCode":0}}}', _JSON),
            ("코드 없음", b'{"data":[1,2,3]}', _JSON),
            ("깨진 JSON", b"{oops", _JSON),
            ("숫자 아닌 코드", b'{"resultCode":"OK"}', _JSON),
            ("바이너리", b"\x00\x01", "application/octet-stream"),
            (
                "XML 정상",
                b"<response><header><resultCode>00</resultCode></header></response>",
                _XML,
            ),
        ],
    )
    def test_everything_else_is_left_alone(
        self, label: str, body: bytes, content_type: str
    ) -> None:
        """모르면 캐시한다.

        판정이 비대칭이라 이 방향이 맞다 — 거짓 양성은 캐시 미스 한 번이지만,
        거짓 음성은 잘못된 응답을 하루 동안 재사용한다.
        """
        assert not is_upstream_error_envelope(body, content_type), label


class TestTheCacheHonoursIt:
    def _transport(self, tmp_path: Path) -> HttpTransport:
        return HttpTransport(TransportConfig(max_retries=0), cache=ResponseCache(tmp_path))

    def _counting_send(self, body: bytes, calls: list[int]) -> Any:
        def _send(self: object, request: httpx.Request, **_kwargs: Any) -> httpx.Response:
            calls.append(1)
            return httpx.Response(
                200, content=body, headers={"content-type": _JSON}, request=request
            )

        return _send

    def test_a_quota_error_is_requested_again(self, tmp_path: Path) -> None:
        calls: list[int] = []
        body = json.dumps({"response": {"header": {"resultCode": "22"}}}).encode()
        transport = self._transport(tmp_path)

        with patch("kpubdata.transport.http.httpx.Client.send", self._counting_send(body, calls)):
            _ = transport.request("GET", "https://x/limited", params={"q": "1"})
            _ = transport.request("GET", "https://x/limited", params={"q": "1"})

        assert len(calls) == 2, "한도 초과가 캐시되면 하루 동안 고착된다"

    def test_a_good_response_is_still_cached(self, tmp_path: Path) -> None:
        calls: list[int] = []
        body = json.dumps({"response": {"header": {"resultCode": "00"}, "body": {}}}).encode()
        transport = self._transport(tmp_path)

        with patch("kpubdata.transport.http.httpx.Client.send", self._counting_send(body, calls)):
            _ = transport.request("GET", "https://x/ok", params={"q": "1"})
            _ = transport.request("GET", "https://x/ok", params={"q": "1"})

        assert len(calls) == 1


class TestNoStoreRequests:
    """응답 자체가 credential 인 요청은 캐시하지 않는다."""

    def test_the_body_never_reaches_disk(self, tmp_path: Path) -> None:
        body = json.dumps(
            {"errCd": 0, "result": {"accessToken": "TOKEN-ABC", "accessTimeout": "1790000000000"}}
        ).encode()
        calls: list[int] = []
        transport = HttpTransport(TransportConfig(max_retries=0), cache=ResponseCache(tmp_path))

        def _send(self: object, request: httpx.Request, **_kwargs: Any) -> httpx.Response:
            calls.append(1)
            return httpx.Response(
                200, content=body, headers={"content-type": _JSON}, request=request
            )

        with patch("kpubdata.transport.http.httpx.Client.send", _send):
            _ = transport.request("GET", "https://sgis/auth", params={"k": "v"}, no_store=True)
            _ = transport.request("GET", "https://sgis/auth", params={"k": "v"}, no_store=True)

        assert len(calls) == 2, "force_refresh 가 캐시를 읽으면 만료된 토큰이 돌아온다"
        on_disk = [p for p in tmp_path.rglob("*") if p.is_file() and b"TOKEN-ABC" in p.read_bytes()]
        assert not on_disk, "access token 이 ~/.cache 에 평문으로 남으면 안 된다"


class TestRetryableComesFromTheStatusCode:
    """4xx 를 재시도 가능으로 표시하면 호출자가 잘못된 키를 계속 다시 보낸다."""

    @pytest.mark.parametrize("status_code", [400, 401, 403, 404])
    def test_client_errors_are_not_retryable(self, status_code: int) -> None:
        from kpubdata.exceptions import TransportError

        assert TransportError("x", status_code=status_code).retryable is False

    @pytest.mark.parametrize("status_code", [408, 425, 429, 500, 503])
    def test_transient_failures_stay_retryable(self, status_code: int) -> None:
        from kpubdata.exceptions import TransportError

        assert TransportError("x", status_code=status_code).retryable is True

    def test_a_failure_with_no_status_is_still_retryable(self) -> None:
        """연결 실패·타임아웃은 상태 코드가 없다 — 그쪽은 다시 시도할 가치가 있다."""
        from kpubdata.exceptions import TransportError

        assert TransportError("connection refused").retryable is True

    def test_an_explicit_value_still_wins(self) -> None:
        from kpubdata.exceptions import TransportError

        assert TransportError("x", status_code=403, retryable=True).retryable is True


class TestTheCachePreservesContentType:
    """캐시 히트가 캐시 미스와 같은 결과를 내야 한다 (#480 두 번째 결함).

    캐시가 본문 바이트만 저장해서, 히트하면 Content-Type 이 사라지고 타입 추론이
    다시 돌았다. XML 응답이 JSON 으로 디코딩되는 경로가 그렇게 생겼다 — 같은
    요청이 캐시 여부에 따라 다른 답을 내는 상태였다.
    """

    _XML = b"<response><header><resultCode>00</resultCode></header><body><items/></body></response>"

    def _transport(self, tmp_path: Path) -> HttpTransport:
        return HttpTransport(TransportConfig(max_retries=0), cache=ResponseCache(tmp_path))

    def _xml_send(self) -> Any:
        def _send(self: object, request: httpx.Request, **_kwargs: Any) -> httpx.Response:
            return httpx.Response(
                200,
                content=TestTheCachePreservesContentType._XML,
                headers={"content-type": "text/xml; charset=utf-8"},
                request=request,
            )

        return _send

    def test_xml_is_still_xml_on_a_cache_hit(self, tmp_path: Path) -> None:
        from kpubdata.transport.decode import detect_content_type

        transport = self._transport(tmp_path)

        with patch("kpubdata.transport.http.httpx.Client.send", self._xml_send()):
            miss = transport.request("GET", "https://x/y", params={"q": "1"})
            hit = transport.request("GET", "https://x/y", params={"q": "1"})

        assert detect_content_type(miss) == "xml"
        assert detect_content_type(hit) == detect_content_type(miss)

    def test_an_entry_without_a_stored_type_still_reads(self, tmp_path: Path) -> None:
        """예전 캐시 엔트리에는 content_type 키가 없다 — 지우지 말고 예전대로 읽는다."""
        import base64
        import json
        import time

        cache = ResponseCache(tmp_path)
        cache.set("legacy", b"body", 3600, "text/xml")
        # content_type 키를 지워 예전 포맷으로 되돌린다.
        path = next(p for p in tmp_path.rglob("*") if p.is_file())
        payload = json.loads(path.read_text(encoding="utf-8"))
        del payload["content_type"]
        payload["created_at"] = time.time()
        path.write_text(json.dumps(payload), encoding="utf-8")

        stored = cache.get("legacy")

        assert stored == (base64.b64decode(payload["body_b64"]), "")
