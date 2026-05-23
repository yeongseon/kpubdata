"""테스트 모듈.

이 파일은 ``tests/unit/transport/test_transport_requirements.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from kpubdata.transport.http import HttpTransport, TransportConfig, TransportRequirements


# test transport requirements defaults 테스트가 검증하는 시나리오를 설명한다.
def test_transport_requirements_defaults() -> None:
    """
    test transport requirements defaults 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    requirements = TransportRequirements()

    assert requirements.verify_ssl is None
    assert requirements.headers is None
    assert requirements.ssl_context_factory is None


# test with requirements merges headers without mutating base config 테스트가 검증하는 시나리오를 설명한다.
def test_with_requirements_merges_headers_without_mutating_base_config() -> None:
    """
    test with requirements merges headers without mutating base config 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    config = TransportConfig(
        timeout=12.0,
        max_retries=5,
        retry_backoff_factor=0.25,
        headers={"User-Agent": "kpubdata", "Accept": "application/json"},
    )
    requirements = TransportRequirements(headers={"Accept": "application/xml", "X-Test": "1"})

    transport = HttpTransport.with_requirements(config, requirements)

    with patch("kpubdata.transport.http.httpx.Client") as client_cls:
        _ = transport.client

    client_cls.assert_called_once_with(
        timeout=12.0,
        headers={
            "User-Agent": "kpubdata",
            "Accept": "application/xml",
            "X-Test": "1",
        },
        follow_redirects=True,
        verify=True,
    )
    assert config.headers == {"User-Agent": "kpubdata", "Accept": "application/json"}


# test build client calls ssl context factory when provided 테스트가 검증하는 시나리오를 설명한다.
def test_build_client_calls_ssl_context_factory_when_provided() -> None:
    """
    test build client calls ssl context factory when provided 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    ssl_context = MagicMock(name="ssl_context")
    ssl_context_factory = MagicMock(return_value=ssl_context)
    transport = HttpTransport(
        requirements=TransportRequirements(ssl_context_factory=ssl_context_factory),
    )

    with patch("kpubdata.transport.http.httpx.Client") as client_cls:
        _ = transport.client

    ssl_context_factory.assert_called_once_with()
    client_cls.assert_called_once_with(
        timeout=30.0,
        headers={},
        follow_redirects=True,
        verify=ssl_context,
    )


# test build client passes verify false when ssl verification disabled 테스트가 검증하는 시나리오를 설명한다.
def test_build_client_passes_verify_false_when_ssl_verification_disabled() -> None:
    """
    test build client passes verify false when ssl verification disabled 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    transport = HttpTransport(requirements=TransportRequirements(verify_ssl=False))

    with patch("kpubdata.transport.http.httpx.Client") as client_cls:
        _ = transport.client

    client_cls.assert_called_once_with(
        timeout=30.0,
        headers={},
        follow_redirects=True,
        verify=False,
    )
