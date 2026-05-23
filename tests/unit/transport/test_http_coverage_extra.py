"""Tests for uncovered branches in transport/http.py (L277-278, L301)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import cast
from unittest.mock import PropertyMock, patch

import httpx

import kpubdata.transport.http as http_module


# test response preview returns decode error on text decode failure 테스트가 검증하는 시나리오를 설명한다.
def test_response_preview_returns_decode_error_on_text_decode_failure() -> None:
    """
    test response preview returns decode error on text decode failure 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    response_preview = cast(Callable[[httpx.Response], str], http_module._response_preview)
    request = httpx.Request("GET", "https://example.test/resource")
    response = httpx.Response(
        status_code=200,
        headers={"content-type": "text/plain"},
        content=b"\x80\x81\x82",
        request=request,
    )

    with patch.object(
        type(response),
        "text",
        new_callable=PropertyMock,
        side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "bad"),
    ):
        result = response_preview(response)

    assert result == "[decode error]"


# test parse retry after naive datetime treated as utc 테스트가 검증하는 시나리오를 설명한다.
def test_parse_retry_after_naive_datetime_treated_as_utc() -> None:
    """
    test parse retry after naive datetime treated as utc 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    parse_retry_after = cast(Callable[[str], float | None], http_module._parse_retry_after)

    future = datetime.now(timezone.utc) + timedelta(seconds=10)
    naive_date_str = future.strftime("%a, %d %b %Y %H:%M:%S") + " GMT"

    with patch.object(
        http_module,
        "parsedate_to_datetime",
        return_value=future.replace(tzinfo=None),
    ):
        result = parse_retry_after(naive_date_str)

    assert result is not None
    assert result >= 0.0
