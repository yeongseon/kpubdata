"""테스트 모듈.

이 파일은 ``tests/unit/providers/sgis/test_auth.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.exceptions import AuthError, ConfigError
from kpubdata.providers.sgis.auth import SgisAuthClient
from kpubdata.transport.http import HttpTransport


def _fixture_path(name: str) -> Path:
    """
    내부 헬퍼로서 fixture path 처리를 담당한다.

    매개변수:
        name (str): 호출자가 제공하는 입력 값이다.

    반환값:
        Path: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    return Path(__file__).resolve().parents[3] / "fixtures" / "sgis" / name


def _load_fixture(name: str) -> dict[str, object]:
    """
    내부 헬퍼로서 load fixture 처리를 담당한다.

    매개변수:
        name (str): 호출자가 제공하는 입력 값이다.

    반환값:
        dict[str, object]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    payload = cast(object, json.loads(_fixture_path(name).read_text(encoding="utf-8")))
    if isinstance(payload, dict):
        return cast(dict[str, object], payload)
    raise ValueError(f"Fixture must be object: {name}")


class _FakeResponse:
    """
    _FakeResponse 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/providers/sgis/test_auth.py`` 모듈 안에서 _FakeResponse의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    def __init__(self, payload: dict[str, object]) -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        매개변수:
            payload (dict[str, object]): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self.headers: dict[str, str] = {"content-type": "application/json"}
        self.text: str = json.dumps(payload, ensure_ascii=False)
        self.content: bytes = self.text.encode("utf-8")


class _FakeTransport:
    """
    _FakeTransport 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/providers/sgis/test_auth.py`` 모듈 안에서 _FakeTransport의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__, request.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    def __init__(self, responses: list[_FakeResponse]) -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        매개변수:
            responses (list[_FakeResponse]): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self._responses: list[_FakeResponse] = list(responses)
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> _FakeResponse:
        """
        request 동작을 수행한다.

        매개변수:
            method (str): 호출자가 제공하는 입력 값이다.
            url (str): 호출자가 제공하는 입력 값이다.
            **kwargs (object): 호출자가 제공하는 입력 값이다.

        반환값:
            _FakeResponse: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self.calls.append({"method": method, "url": url, **kwargs})
        if not self._responses:
            raise AssertionError("No fixture responses remaining")
        return self._responses.pop(0)


def _build_auth_client(
    responses: list[_FakeResponse],
    *,
    provider_key: str,
) -> tuple[SgisAuthClient, _FakeTransport]:
    """
    내부 헬퍼로서 build auth client 처리를 담당한다.

    매개변수:
        responses (list[_FakeResponse]): 호출자가 제공하는 입력 값이다.
        provider_key (str): 호출자가 제공하는 입력 값이다.

    반환값:
        tuple[SgisAuthClient, _FakeTransport]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    transport = _FakeTransport(responses)
    config = KPubDataConfig(provider_keys={"sgis": provider_key})
    return (
        SgisAuthClient(
            config=config,
            transport=cast(HttpTransport, cast(object, transport)),
        ),
        transport,
    )


# test get access token uses consumer secret env 테스트가 검증하는 시나리오를 설명한다.
def test_get_access_token_uses_consumer_secret_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    test get access token uses consumer secret env 시나리오를 검증한다.

    매개변수:
        monkeypatch (pytest.MonkeyPatch): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    monkeypatch.setenv("KPUBDATA_SGIS_CONSUMER_SECRET", "env-secret")
    auth_client, transport = _build_auth_client(
        [_FakeResponse(_load_fixture("auth_success.json"))],
        provider_key="consumer-key-only",
    )

    token = auth_client.get_access_token()

    assert token == "test-access-token-1"
    request_params = cast(dict[str, str], transport.calls[0]["params"])
    assert request_params["consumer_key"] == "consumer-key-only"
    assert request_params["consumer_secret"] == "env-secret"


# test get access token uses key and secret from provider key 테스트가 검증하는 시나리오를 설명한다.
def test_get_access_token_uses_key_and_secret_from_provider_key() -> None:
    """
    test get access token uses key and secret from provider key 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    auth_client, transport = _build_auth_client(
        [_FakeResponse(_load_fixture("auth_success.json"))],
        provider_key="consumer-key:consumer-secret",
    )

    token = auth_client.get_access_token()

    assert token == "test-access-token-1"
    request_params = cast(dict[str, str], transport.calls[0]["params"])
    assert request_params["consumer_key"] == "consumer-key"
    assert request_params["consumer_secret"] == "consumer-secret"


# test get access token raises on auth error 테스트가 검증하는 시나리오를 설명한다.
def test_get_access_token_raises_on_auth_error() -> None:
    """
    test get access token raises on auth error 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    auth_client, _ = _build_auth_client(
        [_FakeResponse(_load_fixture("error_invalid_token.json"))],
        provider_key="consumer-key:consumer-secret",
    )

    with pytest.raises(AuthError):
        _ = auth_client.get_access_token()


# test get access token caches until invalidate 테스트가 검증하는 시나리오를 설명한다.
def test_get_access_token_caches_until_invalidate() -> None:
    """
    test get access token caches until invalidate 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    auth_client, transport = _build_auth_client(
        [_FakeResponse(_load_fixture("auth_success.json"))],
        provider_key="consumer-key:consumer-secret",
    )

    first = auth_client.get_access_token()
    second = auth_client.get_access_token()

    assert first == second
    assert len(transport.calls) == 1


# test get access token refreshes after invalidate 테스트가 검증하는 시나리오를 설명한다.
def test_get_access_token_refreshes_after_invalidate() -> None:
    """
    test get access token refreshes after invalidate 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    auth_success = _load_fixture("auth_success.json")
    auth_success_2 = dict(auth_success)
    auth_success_2["result"] = {
        "accessToken": "test-access-token-2",
        "accessTimeout": "4102444800",
    }

    auth_client, transport = _build_auth_client(
        [_FakeResponse(auth_success), _FakeResponse(auth_success_2)],
        provider_key="consumer-key:consumer-secret",
    )

    first = auth_client.get_access_token()
    auth_client.invalidate()
    second = auth_client.get_access_token()

    assert first == "test-access-token-1"
    assert second == "test-access-token-2"
    assert len(transport.calls) == 2


# test get access token requires secret when env missing 테스트가 검증하는 시나리오를 설명한다.
def test_get_access_token_requires_secret_when_env_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    test get access token requires secret when env missing 시나리오를 검증한다.

    매개변수:
        monkeypatch (pytest.MonkeyPatch): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    monkeypatch.delenv("KPUBDATA_SGIS_CONSUMER_SECRET", raising=False)
    auth_client, _ = _build_auth_client(
        [_FakeResponse(_load_fixture("auth_success.json"))],
        provider_key="consumer-key-only",
    )

    with pytest.raises(ConfigError):
        _ = auth_client.get_access_token()
