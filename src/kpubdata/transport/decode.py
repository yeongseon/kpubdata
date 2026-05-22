"""응답 디코딩 유틸리티 — content-type 감지와 JSON/XML 헬퍼."""

from __future__ import annotations

import json
import logging
from importlib import import_module

import httpx

from ..exceptions import ParseError

logger = logging.getLogger("kpubdata.transport.decode")


def detect_content_type(response: httpx.Response) -> str:
    """content-type 헤더를 기준으로 응답이 JSON, XML 또는 기타인지 감지한다."""
    header_value_obj = response.headers.get("content-type", "")
    content_type = str(header_value_obj).lower()
    if "json" in content_type:
        return "json"
    if "xml" in content_type:
        return "xml"
    logger.debug(
        "Unrecognized content-type, defaulting to 'other'",
        extra={"content_type": content_type},
    )
    return "other"


def decode_json(data: str | bytes) -> object:
    """실패 시 명확한 에러와 함께 JSON을 디코딩한다."""
    try:
        payload = data.decode("utf-8") if isinstance(data, bytes) else data
    except UnicodeDecodeError as exc:
        logger.debug(
            "JSON UTF-8 decode failed",
            extra={"byte_length": len(data) if isinstance(data, bytes) else None},
        )
        msg = "Failed to decode JSON bytes as UTF-8"
        raise ParseError(msg) from exc

    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        logger.debug(
            "JSON parse failed",
            extra={
                "char_length": len(payload),
                "preview": payload[:200],
                "line": exc.lineno,
                "column": exc.colno,
            },
        )
        msg = "Failed to decode JSON payload"
        raise ParseError(msg) from exc


def decode_xml(data: str | bytes) -> dict[str, object]:
    """XML을 dict로 디코딩한다.

    Raises:
        ImportError: ``xmltodict``가 설치되지 않은 경우.
        ParseError: 파싱에 실패한 경우.
    """
    try:
        xmltodict = import_module("xmltodict")
    except ImportError as exc:
        msg = (
            "decode_xml requires optional dependency 'xmltodict'. Install with: "
            "pip install kpubdata[xml]"
        )
        raise ImportError(msg) from exc

    try:
        payload = data.decode("utf-8") if isinstance(data, bytes) else data
    except UnicodeDecodeError as exc:
        logger.debug(
            "XML UTF-8 decode failed",
            extra={"byte_length": len(data) if isinstance(data, bytes) else None},
        )
        msg = "Failed to decode XML bytes as UTF-8"
        raise ParseError(msg) from exc

    try:
        parsed: object = xmltodict.parse(payload)
    except Exception as exc:  # noqa: BLE001
        logger.debug(
            "XML parse failed",
            extra={
                "char_length": len(payload),
                "preview": payload[:200],
                "exception_type": type(exc).__name__,
            },
        )
        msg = "Failed to decode XML payload"
        raise ParseError(msg) from exc

    if isinstance(parsed, dict):
        return parsed

    logger.debug(
        "XML payload decoded but root is not a dict",
        extra={"root_type": type(parsed).__name__},
    )
    msg = "XML payload did not decode into a dictionary"
    raise ParseError(msg)


__all__ = ["decode_json", "decode_xml", "detect_content_type"]
