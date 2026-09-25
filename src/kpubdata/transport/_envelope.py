"""HTTP 200 으로 온 응답이 실은 거부인지 가려낸다.

한국 공공 API 다수는 실패를 HTTP 상태가 아니라 본문 envelope 으로 알린다 —
한도 초과(``22``), 미등록 키(``30``), 게이트웨이 거부 모두 200 으로 온다.
transport 는 상태 코드만 보고 캐시해 왔으므로, 일시적인 한도 초과가 24시간짜리
장애로 굳었다. 그 캐시는 builder 의 Bronze fetch 로도 그대로 전파돼, 스케줄
빌드가 빈 데이터를 "성공" 으로 게시할 수 있었다.

**판정은 일부러 보수적이다.** transport 는 spec 을 모르므로 ``code_path`` 도
``ok_values`` 도 볼 수 없고, 여기서는 널리 쓰이는 envelope 모양만 고정 위치에서
확인한다. 코드가 보이지 않거나 파싱되지 않으면 "모른다"로 두고 예전처럼 캐시한다.

방향이 비대칭이라 이렇게 둔다 — 거짓 양성은 캐시를 한 번 더 미스하는 것으로
끝나지만, 거짓 음성은 잘못된 응답을 하루 동안 재사용한다.

XML 은 정규식으로 태그만 본다. 파싱에는 optional extra(``kpubdata[xml]``)가
필요한데, 캐시 여부를 정하자고 그걸 요구할 수는 없다.
"""

from __future__ import annotations

import json
import re

#: 성공으로 보는 코드. executor 의 판정(``ok_values`` 또는 정수 0)과 같은 어휘다.
_SUCCESS_CODES = frozenset({"00", "000", "0"})

#: 고정 위치의 envelope 코드 경로. 앞에서부터 먼저 발견된 것을 쓴다.
_JSON_CODE_PATHS: tuple[tuple[str, ...], ...] = (
    # 게이트웨이가 서비스 대신 답한 경우 (미등록 키, 한도 초과 등)
    ("OpenAPI_ServiceResponse", "cmmMsgHeader", "returnReasonCode"),
    # 표준 data.go.kr 서비스 envelope
    ("response", "header", "resultCode"),
    # 한국관광공사 KorService 류 — envelope 밖 최상단
    ("resultCode",),
)

_XML_CODE_TAGS = ("returnReasonCode", "resultCode")
_XML_CODE_PATTERN = re.compile(
    rb"<(?:\w+:)?(" + b"|".join(t.encode() for t in _XML_CODE_TAGS) + rb")>([^<]{0,32})</",
    re.IGNORECASE,
)


def _is_failure_code(code: str) -> bool:
    code = code.strip()
    if not code:
        return False
    if code in _SUCCESS_CODES:
        return False
    try:
        return int(code) != 0
    except ValueError:
        # 숫자가 아닌 코드는 판단하지 않는다 — 모르는 어휘다.
        return False


def _json_code(body: bytes) -> str | None:
    try:
        payload = json.loads(body)
    except (ValueError, UnicodeDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    for path in _JSON_CODE_PATHS:
        node: object = payload
        for key in path:
            if not isinstance(node, dict):
                node = None
                break
            node = node.get(key)
        if isinstance(node, str | int) and not isinstance(node, bool):
            return str(node)
    return None


def is_upstream_error_envelope(body: bytes, content_type: str) -> bool:
    """이 200 응답이 실은 거부인지. 확실할 때만 True."""
    kind = content_type.split(";", 1)[0].strip().casefold()
    if "json" in kind:
        code = _json_code(body)
        return code is not None and _is_failure_code(code)
    if "xml" in kind:
        match = _XML_CODE_PATTERN.search(body)
        if match is None:
            return False
        return _is_failure_code(match.group(2).decode("ascii", "ignore"))
    return False


__all__ = ["is_upstream_error_envelope"]
