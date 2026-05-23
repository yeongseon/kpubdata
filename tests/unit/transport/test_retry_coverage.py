"""테스트 모듈.

이 파일은 ``tests/unit/transport/test_retry_coverage.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

import pytest

from kpubdata.transport.retry import with_retry


# test with retry rejects negative backoff factor 테스트가 검증하는 시나리오를 설명한다.
def test_with_retry_rejects_negative_backoff_factor() -> None:
    """
    test with retry rejects negative backoff factor 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    with pytest.raises(ValueError, match="backoff_factor"):
        _ = with_retry(lambda: 1, backoff_factor=-0.1)


# test with retry unreachable state raises runtime error 테스트가 검증하는 시나리오를 설명한다.
def test_with_retry_unreachable_state_raises_runtime_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    test with retry unreachable state raises runtime error 시나리오를 검증한다.

    매개변수:
        monkeypatch (pytest.MonkeyPatch): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    import kpubdata.transport.retry as retry_module

    monkeypatch.setattr(retry_module, "range", lambda *_args: [], raising=False)

    with pytest.raises(RuntimeError, match="unreachable retry state"):
        _ = with_retry(lambda: 1)
