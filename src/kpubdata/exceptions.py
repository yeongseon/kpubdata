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


class AuthError(PublicDataError):
    """인증 또는 권한 부여 실패 시 발생한다."""


class TransportError(PublicDataError):
    """네트워크 및 전송 계층 실패 시 발생한다."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        """기본적으로 재시도 가능한 전송 오류를 초기화한다."""

        kwargs.setdefault("retryable", True)
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


__all__ = [
    "AuthError",
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
