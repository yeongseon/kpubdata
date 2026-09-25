"""구조화된 오류 컨텍스트를 갖는 KPubData 예외 계층."""

from __future__ import annotations

from typing import Any


class PublicDataError(Exception):
    """구조화된 컨텍스트 속성을 갖는 모든 KPubData 오류의 기반 클래스."""

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        dataset_id: str | None = None,
        operation: str | None = None,
        status_code: int | None = None,
        provider_code: str | None = None,
        retryable: bool = False,
        detail: object = None,
    ) -> None:
        """선택적 Provider/전송 메타데이터와 함께 오류를 초기화한다."""

        super().__init__(message)
        self.provider = provider
        self.dataset_id = dataset_id
        self.operation = operation
        self.status_code = status_code
        self.provider_code = provider_code
        self.retryable = retryable
        self.detail = detail

    def __repr__(self) -> str:
        """Provider 및 전송 메타데이터를 포함한 구조화된 repr를 반환한다."""
        parts = [f"{type(self).__name__}({self.args[0]!r}"]
        if self.provider:
            parts.append(f"provider={self.provider!r}")
        if self.dataset_id:
            parts.append(f"dataset={self.dataset_id!r}")
        if self.status_code is not None:
            parts.append(f"status={self.status_code}")
        if self.retryable:
            parts.append("retryable=True")
        return ", ".join(parts) + ")"


class ConfigError(PublicDataError):
    """KPubData 설정이 잘못되었거나 불완전할 때 발생한다."""


#: 다시 보낼 가치가 있는 4xx. 나머지 4xx 는 같은 답이 돌아온다.
_RETRYABLE_CLIENT_STATUSES = frozenset({408, 425, 429})


def _status_is_retryable(status_code: object) -> bool:
    """이 상태 코드의 실패를 재시도해도 되는지.

    판정은 ``transport.http._is_retryable_status`` 의 재시도 정책과 같은 뜻이되,
    거기에 없는 408·425 까지 포함한다 — transport 는 그 둘을 재시도하지 않지만,
    호출자에게 "다시 시도해도 된다" 고 알려 주는 것은 옳다.
    """
    if not isinstance(status_code, int) or isinstance(status_code, bool):
        # 상태 코드가 없는 실패는 전송 계층 자체의 실패다(연결/타임아웃).
        return True
    if status_code in _RETRYABLE_CLIENT_STATUSES:
        return True
    return status_code >= 500


class AuthError(PublicDataError):
    """인증 또는 권한 부여 실패 시 발생한다."""


class TransportError(PublicDataError):
    """네트워크 및 전송 계층 실패 시 발생한다."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        """전송 오류를 초기화한다. 기본 ``retryable`` 은 상태 코드에서 나온다.

        예전에는 무조건 ``True`` 였다. 그래서 400·401·403·404 처럼 다시 보내도
        같은 답이 오는 실패까지 "재시도 가능" 으로 표시됐고, 그 값을 믿는
        호출자(kpubdata-builder 의 Bronze fetch)는 잘못된 키나 잘못된 요청을
        재시도 예산만큼 반복했다.

        상태 코드를 모르면(연결 실패·타임아웃 등 전송 계층 자체의 실패) 예전처럼
        재시도 가능으로 둔다 — 그쪽은 실제로 다시 시도할 가치가 있다.
        """
        status_code = kwargs.get("status_code")
        kwargs.setdefault("retryable", _status_is_retryable(status_code))
        super().__init__(message, **kwargs)


class TransportTimeoutError(TransportError):
    """Provider 요청이 타임아웃 한도를 초과할 때 발생한다."""


class RateLimitError(TransportError):
    """Provider가 throttling 등으로 요청을 거부할 때 발생한다."""


class ServiceUnavailableError(TransportError):
    """상위 Provider 서비스가 일시적으로 사용 불가할 때 발생한다."""


class ParseError(PublicDataError):
    """Provider 페이로드를 안전하게 파싱할 수 없을 때 발생한다."""


class InvalidRequestError(PublicDataError):
    """질의 또는 작업 입력이 의미적으로 잘못되었을 때 발생한다."""


class ProviderResponseError(PublicDataError):
    """Provider 응답이 계약 기대사항을 위반할 때 발생한다."""


class UnsupportedCapabilityError(PublicDataError):
    """요청한 작업이 데이터셋에서 지원되지 않을 때 발생한다."""


class DatasetNotFoundError(PublicDataError):
    """요청한 데이터셋 식별자를 해석할 수 없을 때 발생한다."""


class ProviderNotRegisteredError(PublicDataError):
    """Provider 키가 레지스트리에 없을 때 발생한다."""


class CapabilityContractError(PublicDataError):
    """Provider 어댑터의 선언된 capability와 실제 동작이 일치하지 않을 때 발생한다.

    예: catalogue의 dataset이 ``LIST``를 선언했지만 ``list_datasets`` 호출이
    실패하거나, ``operations``가 빈 집합으로 선언된 dataset이 노출되는 경우.
    """


__all__ = [
    "AuthError",
    "CapabilityContractError",
    "ConfigError",
    "DatasetNotFoundError",
    "InvalidRequestError",
    "ParseError",
    "ProviderNotRegisteredError",
    "ProviderResponseError",
    "PublicDataError",
    "RateLimitError",
    "ServiceUnavailableError",
    "TransportError",
    "TransportTimeoutError",
    "UnsupportedCapabilityError",
]
