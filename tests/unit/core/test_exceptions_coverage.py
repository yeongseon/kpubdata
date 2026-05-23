"""테스트 모듈.

이 파일은 ``tests/unit/core/test_exceptions_coverage.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

from kpubdata.exceptions import PublicDataError


# test public data error repr includes retryable flag 테스트가 검증하는 시나리오를 설명한다.
def test_public_data_error_repr_includes_retryable_flag() -> None:
    """
    test public data error repr includes retryable flag 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    error = PublicDataError("retry me", retryable=True)

    assert "retryable=True" in repr(error)
