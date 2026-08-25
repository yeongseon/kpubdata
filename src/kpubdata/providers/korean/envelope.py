"""국립국어원 API 응답 래퍼 파싱."""

from __future__ import annotations

from typing import Any


def validate_envelope(response_data: dict[str, Any]) -> dict[str, Any]:
    """국립국어원 API 응답 래퍼를 검증하고 내부 데이터를 추출한다."""
    if not response_data:
        raise ValueError("Empty response")

    if response_data.get("errorMessage"):
        error_msg = response_data.get("errorMessage", "Unknown error")
        raise ValueError(f"API error: {error_msg}")

    items = response_data.get("item", [])

    if not items:
        return {"items": [], "total_count": 0}

    if not isinstance(items, list):
        items = [items] if items else []

    total_count = response_data.get("total", len(items))
    return {"items": items, "total_count": total_count}


def extract_items(response_data: dict[str, Any]) -> list[dict[str, Any]]:
    """국립국어원 API 응답에서 아이템 목록을 추출한다."""
    envelope = validate_envelope(response_data)
    return envelope["items"]