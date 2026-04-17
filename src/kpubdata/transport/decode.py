"""Response decoding utilities — content-type detection, JSON/XML helpers."""

from __future__ import annotations

import json
from importlib import import_module

import httpx

from ..exceptions import ParseError


def detect_content_type(response: httpx.Response) -> str:
    """Detect whether response is JSON, XML, or other based on content-type header."""
    header_value_obj = response.headers.get("content-type", "")
    content_type = str(header_value_obj).lower()
    if "json" in content_type:
        return "json"
    if "xml" in content_type:
        return "xml"
    return "other"


def decode_json(data: str | bytes) -> object:
    """Decode JSON with clear error on failure."""
    try:
        payload = data.decode("utf-8") if isinstance(data, bytes) else data
    except UnicodeDecodeError as exc:
        msg = "Failed to decode JSON bytes as UTF-8"
        raise ParseError(msg) from exc

    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        msg = "Failed to decode JSON payload"
        raise ParseError(msg) from exc


def decode_xml(data: str | bytes) -> dict[str, object]:
    """Decode XML to dict.

    Raises:
        ImportError: If ``xmltodict`` is not installed.
        ParseError: If parsing fails.
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
        msg = "Failed to decode XML bytes as UTF-8"
        raise ParseError(msg) from exc

    try:
        parsed: object = xmltodict.parse(payload)
    except Exception as exc:  # noqa: BLE001
        msg = "Failed to decode XML payload"
        raise ParseError(msg) from exc

    if isinstance(parsed, dict):
        return parsed

    msg = "XML payload did not decode into a dictionary"
    raise ParseError(msg)


__all__ = ["decode_json", "decode_xml", "detect_content_type"]
