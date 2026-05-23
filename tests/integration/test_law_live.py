"""테스트 모듈.

이 파일은 ``tests/integration/test_law_live.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

import pytest

from kpubdata.client import Client
from kpubdata.core.models import RecordBatch


# test law search returns record batch 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_law_search_returns_record_batch(live_client: Client) -> None:
    """
    test law search returns record batch 시나리오를 검증한다.

    매개변수:
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    ds = live_client.dataset("law.law_search")

    result = ds.list(query="민법")

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0
    assert isinstance(result.items[0], dict)


# test law search raw returns envelope 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_law_search_raw_returns_envelope(live_client: Client) -> None:
    """
    test law search raw returns envelope 시나리오를 검증한다.

    매개변수:
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    ds = live_client.dataset("law.law_search")

    raw = ds.call_raw("list", query="헌법")

    assert isinstance(raw, dict)


# test law search item has law name 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_law_search_item_has_law_name(live_client: Client) -> None:
    """
    test law search item has law name 시나리오를 검증한다.

    매개변수:
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    ds = live_client.dataset("law.law_search")
    result = ds.list(query="민법")

    item = result.items[0]
    assert any(key in item for key in ("법령명한글", "lawNameKorean", "법령명"))


# test law search pagination 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_law_search_pagination(live_client: Client) -> None:
    """
    test law search pagination 시나리오를 검증한다.

    매개변수:
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    ds = live_client.dataset("law.law_search")

    result = ds.list(query="법", page_size=5)

    assert isinstance(result, RecordBatch)
    assert len(result.items) <= 5


# test ordin search returns record batch 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.integration
def test_ordin_search_returns_record_batch(live_client: Client) -> None:
    """
    test ordin search returns record batch 시나리오를 검증한다.

    매개변수:
        live_client (Client): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    ds = live_client.dataset("law.ordin_search")

    result = ds.list(query="서울")

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0
