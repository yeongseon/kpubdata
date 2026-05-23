"""KPubData Python 모듈.

이 파일은 ``src/kpubdata/providers/sgis/auth.py`` 경로의 구현을 담는다.
주요 클래스와 함수는 공개 API, 전송 계층, Provider 어댑터 중 하나의 역할을 담당한다.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import NoReturn, cast

from kpubdata.config import KPubDataConfig
from kpubdata.exceptions import AuthError, ConfigError, InvalidRequestError, ProviderResponseError
from kpubdata.transport.decode import decode_json
from kpubdata.transport.http import HttpTransport

_AUTH_ENDPOINT = "https://sgisapi.kostat.go.kr/OpenAPI3/auth/authentication.json"
_SGIS_PROVIDER = "sgis"
_SECRET_ENV = "KPUBDATA_SGIS_CONSUMER_SECRET"


@dataclass(slots=True)
class _TokenState:
    """
    _TokenState 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``src/kpubdata/providers/sgis/auth.py`` 모듈 안에서 _TokenState의 상태와 동작을 함께 관리한다.
    주요 메서드: 없음.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    value: str
    expires_at: datetime


class SgisAuthClient:
    """
    SgisAuthClient 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``src/kpubdata/providers/sgis/auth.py`` 모듈 안에서 SgisAuthClient의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__, get_access_token, invalidate, _request_access_token, _resolve_credentials.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    def __init__(self, *, config: KPubDataConfig, transport: HttpTransport) -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        매개변수:
            config (KPubDataConfig): 호출자가 제공하는 입력 값이다.
            transport (HttpTransport): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self._config: KPubDataConfig = config
        self._transport: HttpTransport = transport
        self._cached_token: _TokenState | None = None

    def get_access_token(self, *, force_refresh: bool = False) -> str:
        """
        get access token 동작을 수행한다.

        매개변수:
            force_refresh (bool): 호출자가 제공하는 입력 값이다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        if (
            not force_refresh
            and self._cached_token is not None
            and not self._is_expired(self._cached_token)
        ):
            return self._cached_token.value

        token_state = self._request_access_token()
        self._cached_token = token_state
        return token_state.value

    def invalidate(self) -> None:
        """
        invalidate 동작을 수행한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self._cached_token = None

    def _request_access_token(self) -> _TokenState:
        """
        내부 헬퍼로서 request access token 처리를 담당한다.

        반환값:
            _TokenState: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        consumer_key, consumer_secret = self._resolve_credentials()
        response = self._transport.request(
            "GET",
            _AUTH_ENDPOINT,
            params={"consumer_key": consumer_key, "consumer_secret": consumer_secret},
        )

        decoded = decode_json(response.content)
        if not isinstance(decoded, dict):
            raise ProviderResponseError(
                "SGIS auth response must be a JSON object",
                provider=_SGIS_PROVIDER,
            )
        payload = cast(dict[str, object], decoded)

        self._raise_for_err_code(payload)

        result_obj = payload.get("result")
        if not isinstance(result_obj, dict):
            raise ProviderResponseError(
                "SGIS auth response missing result object",
                provider=_SGIS_PROVIDER,
            )
        result = cast(dict[str, object], result_obj)

        token_obj = result.get("accessToken")
        timeout_obj = result.get("accessTimeout")
        if not isinstance(token_obj, str) or not token_obj:
            raise ProviderResponseError(
                "SGIS auth response missing accessToken",
                provider=_SGIS_PROVIDER,
            )

        expires_epoch = _coerce_epoch(timeout_obj)
        if expires_epoch is None:
            raise ProviderResponseError(
                "SGIS auth response has invalid accessTimeout",
                provider=_SGIS_PROVIDER,
            )

        expires_at = datetime.fromtimestamp(expires_epoch, tz=timezone.utc)
        return _TokenState(value=token_obj, expires_at=expires_at)

    def _resolve_credentials(self) -> tuple[str, str]:
        """
        내부 헬퍼로서 resolve credentials 처리를 담당한다.

        반환값:
            tuple[str, str]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        consumer_key_raw = self._config.require_provider_key(_SGIS_PROVIDER)
        consumer_secret_env = os.environ.get(_SECRET_ENV)

        if consumer_secret_env:
            return consumer_key_raw, consumer_secret_env

        if ":" in consumer_key_raw:
            key_part, secret_part = consumer_key_raw.split(":", 1)
            if key_part and secret_part:
                return key_part, secret_part

        raise ConfigError(
            "Missing SGIS consumer secret. "
            + "Set KPUBDATA_SGIS_CONSUMER_SECRET or pass provider key "
            + "as 'consumer_key:consumer_secret'."
        )

    def _is_expired(self, state: _TokenState) -> bool:
        """
        내부 헬퍼로서 is expired 처리를 담당한다.

        매개변수:
            state (_TokenState): 호출자가 제공하는 입력 값이다.

        반환값:
            bool: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        now = datetime.now(tz=timezone.utc)
        return now >= state.expires_at

    def _raise_for_err_code(self, payload: dict[str, object]) -> None:
        """
        내부 헬퍼로서 raise for err code 처리를 담당한다.

        매개변수:
            payload (dict[str, object]): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        err_code = _extract_err_code(payload)
        if err_code is None or err_code == 0:
            return

        message_obj = payload.get("errMsg")
        message = (
            message_obj if isinstance(message_obj, str) and message_obj else "SGIS auth failed"
        )
        self._raise_for_code(err_code, message)

    def _raise_for_code(self, err_code: int, message: str) -> NoReturn:
        """
        내부 헬퍼로서 raise for code 처리를 담당한다.

        매개변수:
            err_code (int): 호출자가 제공하는 입력 값이다.
            message (str): 호출자가 제공하는 입력 값이다.

        반환값:
            NoReturn: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        provider_code = str(err_code)
        if err_code in {-401, -402, -403}:
            raise AuthError(message, provider=_SGIS_PROVIDER, provider_code=provider_code)
        if err_code in {-413, -414}:
            raise InvalidRequestError(message, provider=_SGIS_PROVIDER, provider_code=provider_code)
        raise ProviderResponseError(message, provider=_SGIS_PROVIDER, provider_code=provider_code)


def _extract_err_code(payload: dict[str, object]) -> int | None:
    """
    내부 헬퍼로서 extract err code 처리를 담당한다.

    매개변수:
        payload (dict[str, object]): 호출자가 제공하는 입력 값이다.

    반환값:
        int | None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    err_obj = payload.get("errCd")
    if isinstance(err_obj, int):
        return err_obj
    if isinstance(err_obj, str):
        try:
            return int(err_obj)
        except ValueError:
            return None
    return None


def _coerce_epoch(value: object) -> int | None:
    """
    내부 헬퍼로서 coerce epoch 처리를 담당한다.

    매개변수:
        value (object): 호출자가 제공하는 입력 값이다.

    반환값:
        int | None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


__all__ = ["SgisAuthClient"]
