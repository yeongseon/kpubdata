"""응답 정화(redaction) — fixture에 민감값이 남지 않게 한다.

record.py가 저장하기 전에 원본 페이로드·파라미터에서 다음을 치환한다:
- API 키 실제 값(설정에서 읽어 전달받은 값 그대로)
- 이메일 주소
- 한국 전화번호(010-1234-5678, 02-123-4567 등)
"""

from __future__ import annotations

import re

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"\b(?:0\d{1,2}-\d{3,4}-\d{4}|01\d{8,9})\b")
_REDACTED = "[REDACTED]"


def redact_string(value: str, secrets: tuple[str, ...] = ()) -> str:
    """문자열에서 민감값을 치환한다."""
    result = value
    for secret in secrets:
        if secret:
            result = result.replace(secret, _REDACTED)
    result = _EMAIL_RE.sub(_REDACTED, result)
    result = _PHONE_RE.sub(_REDACTED, result)
    return result


def redact_mapping(data: dict[str, object], secrets: tuple[str, ...] = ()) -> dict[str, object]:
    """매핑을 재귀 순회하며 문자열 값을 정화한 사본을 반환한다.

    키 이름이 민감 파라미터(serviceKey 등)인 항목은 값 전체를 치환한다.
    """
    sensitive_keys = {"servicekey", "service_key", "apikey", "api_key", "key", "token", "secret"}
    redacted: dict[str, object] = {}
    for key, value in data.items():
        if isinstance(value, str):
            if key.strip().lower() in sensitive_keys:
                redacted[key] = _REDACTED
            else:
                redacted[key] = redact_string(value, secrets)
        elif isinstance(value, dict):
            redacted[key] = redact_mapping(value, secrets)
        elif isinstance(value, list):
            redacted[key] = _redact_list(value, secrets)
        else:
            redacted[key] = value
    return redacted


def _redact_list(values: list[object], secrets: tuple[str, ...]) -> list[object]:
    """리스트 내부를 재귀 정화한다."""
    result: list[object] = []
    for value in values:
        if isinstance(value, str):
            result.append(redact_string(value, secrets))
        elif isinstance(value, dict):
            result.append(redact_mapping(value, secrets))
        elif isinstance(value, list):
            result.append(_redact_list(value, secrets))
        else:
            result.append(value)
    return result


__all__ = ["redact_mapping", "redact_string"]
