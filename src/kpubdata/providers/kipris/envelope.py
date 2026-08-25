"""KIPRIS API 응답 래퍼 파싱."""

from __future__ import annotations

from typing import Any

import xmltodict


def parse_xml_response(xml_string: str | bytes) -> dict[str, Any]:
    """KIPRIS API의 XML 응답을 Python dict로 변환한다."""
    if isinstance(xml_string, bytes):
        xml_string = xml_string.decode("utf-8", errors="ignore")
    return xmltodict.parse(xml_string)


def validate_envelope(response_data: dict[str, Any]) -> dict[str, Any]:
    """KIPRIS API 응답 래퍼를 검증하고 내부 데이터를 추출한다."""
    if not response_data:
        raise ValueError("Empty response")

    response = response_data.get("response", {})
    header = response.get("header", {})
    body = response.get("body", {})

    result_code = header.get("resultCode")
    if result_code and result_code != "00":
        result_msg = header.get("resultMsg", "Unknown error")
        raise ValueError(f"API error: {result_code} - {result_msg}")

    if not body:
        raise ValueError("Empty response body")

    items = body.get("items", {})

    return {"items": items, "num_of_rows": body.get("numOfRows", 0), "page_no": body.get("pageNo", 1), "total_count": body.get("totalCount", 0)}


def extract_items(response_data: dict[str, Any]) -> list[dict[str, Any]]:
    """KIPRIS API 응답에서 아이템 목록을 추출한다."""
    envelope = validate_envelope(response_data)
    items = envelope["items"]

    if not items:
        return []

    if isinstance(items, dict) and "item" in items:
        item_data = items["item"]
        if isinstance(item_data, list):
            return item_data
        elif item_data:
            return [item_data]
        return []

    if isinstance(items, dict):
        return [items]

    if isinstance(items, list):
        return items

    return []