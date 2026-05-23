"""간결한 HTTP 전송 계층 — 세션 관리, 재시도, 타임아웃, 디코딩.

이 계층은 다음을 처리하지 않는다:
- 인증 주입(어댑터 책임)
- 파라미터 이름 규칙(어댑터 책임)
- 응답 엔벌로프 파싱(어댑터 책임)
- Provider별 에러 매핑(어댑터 책임)
"""

from __future__ import annotations

import logging
import ssl
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import TYPE_CHECKING, cast

import httpx
from typing_extensions import override

from kpubdata.exceptions import TransportError, TransportTimeoutError
from kpubdata.transport.cache import ResponseCache, make_cache_key

if TYPE_CHECKING:
    import ssl

logger = logging.getLogger("kpubdata.transport")
_SENSITIVE_PARAM_KEYS = {
    "servicekey",
    "service_key",
    "api_key",
    "apikey",
    "token",
    "authorization",
    "secret",
    "password",
    "key",
}


@dataclass
class TransportConfig:
    """전송 계층 설정."""

    timeout: float = 30.0
    max_retries: int = 3
    retry_backoff_factor: float = 0.5
    headers: dict[str, str] | None = None
    verify_ssl: bool = True
    ssl_context: ssl.SSLContext | None = None
    cache: ResponseCache | None = None
    cache_ttl_seconds: int = 86400


@dataclass(frozen=True)
class TransportRequirements:
    """제공자 어댑터를 위한 선언적 전송 커스터마이징."""

    verify_ssl: bool | None = None
    headers: Mapping[str, str] | None = None
    ssl_context_factory: Callable[[], ssl.SSLContext] | None = None


class HttpTransport:
    """재시도, 타임아웃, 구조화 로깅을 갖춘 관리형 httpx 클라이언트."""

    def __init__(
        self,
        config: TransportConfig | None = None,
        requirements: TransportRequirements | None = None,
        cache: ResponseCache | None = None,
        cache_ttl_seconds: int = 86400,
    ) -> None:
        """선택적 명시 설정으로 전송 계층을 초기화한다."""
        self._config: TransportConfig = config or TransportConfig()
        self._requirements: TransportRequirements | None = requirements
        self._cache: ResponseCache | None = self._config.cache if cache is None else cache
        self._cache_ttl_seconds: int = (
            self._config.cache_ttl_seconds if cache_ttl_seconds == 86400 else cache_ttl_seconds
        )
        self._client: httpx.Client | None = None

    @classmethod
    def with_requirements(
        cls,
        config: TransportConfig,
        requirements: TransportRequirements,
    ) -> HttpTransport:
        """기본 전송 설정에 Provider 요구사항을 합친 새 HttpTransport를 만든다."""
        return cls(
            config=TransportConfig(
                timeout=config.timeout,
                max_retries=config.max_retries,
                retry_backoff_factor=config.retry_backoff_factor,
                headers=_merge_headers(config.headers, requirements.headers),
                cache=config.cache,
                cache_ttl_seconds=config.cache_ttl_seconds,
            ),
            requirements=requirements,
        )

    def __enter__(self) -> HttpTransport:
        """컨텍스트 관리자에 진입하며 클라이언트를 즉시 초기화한다."""
        self._client = self._build_client()
        return self

    def __exit__(self, *exc: object) -> None:
        """컨텍스트 관리자를 종료하고 관리 중인 클라이언트를 닫는다."""
        self.close()

    @override
    def __repr__(self) -> str:
        """간결한 디버그 표현을 반환한다."""
        return (
            "HttpTransport("
            f"timeout={self._config.timeout}, "
            f"max_retries={self._config.max_retries}, "
            f"retry_backoff_factor={self._config.retry_backoff_factor}, "
            f"client_initialized={self._client is not None}"
            ")"
        )

    def _build_client(self, requirements: TransportRequirements | None = None) -> httpx.Client:
        """현재 설정과 요구사항을 반영한 httpx.Client를 생성한다."""
        effective_requirements = requirements or self._requirements
        return httpx.Client(
            timeout=self._config.timeout,
            headers=_merge_headers(
                self._config.headers,
                # Provider 전용 헤더가 있으면 공용 헤더 위에 덮어쓴다.
                None if effective_requirements is None else effective_requirements.headers,
            )
            or {},
            follow_redirects=True,
            verify=self._resolve_verify(effective_requirements),
        )

    def _resolve_verify(self, requirements: TransportRequirements | None) -> bool | ssl.SSLContext:
        """SSL 검증 여부와 SSLContext의 최종 적용 값을 결정한다."""
        # 명시적 SSLContext는 verify_ssl 불리언보다 구체적이므로 최우선으로 사용한다.
        if self._config.ssl_context is not None:
            return self._config.ssl_context
        if requirements is None:
            return self._config.verify_ssl
        # Provider가 SSLContext factory를 제공하면 요청 직전에 전용 컨텍스트를 생성한다.
        if requirements.ssl_context_factory is not None:
            return requirements.ssl_context_factory()
        # 마지막으로 Provider별 verify_ssl override가 있으면 기본 설정을 덮어쓴다.
        if requirements.verify_ssl is not None:
            return requirements.verify_ssl
        return self._config.verify_ssl

    def close(self) -> None:
        """클라이언트가 초기화되었으면 닫는다."""
        if self._client is not None:
            self._client.close()
            self._client = None

    @property
    def client(self) -> httpx.Client:
        """지연 초기화되는 공유 ``httpx.Client`` 인스턴스를 반환한다."""
        if self._client is None:
            self._client = self._build_client()
        return self._client

    @property
    def cache(self) -> ResponseCache | None:
        """현재 전송 인스턴스에 연결된 응답 캐시를 반환한다."""
        return self._cache

    @property
    def cache_ttl_seconds(self) -> int:
        """응답 캐시에 적용할 기본 TTL 초 값을 반환한다."""
        return self._cache_ttl_seconds

    def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        content: bytes | None = None,
        json_body: object = None,
        dataset_id: str | None = None,
        provider: str | None = None,
    ) -> httpx.Response:
        """재시도 로직과 함께 HTTP 요청을 실행한다.

        반환값:
            원시 ``httpx.Response``.

        예외:
            TransportError: 타임아웃이 아닌 전송 실패가 발생한 경우.
            TransportTimeoutError: 타임아웃 실패가 발생한 경우.
        """
        if self._config.max_retries < 0:
            msg = "max_retries must be >= 0"
            raise ValueError(msg)
        if self._config.retry_backoff_factor < 0:
            msg = "retry_backoff_factor must be >= 0"
            raise ValueError(msg)

        total_attempts = self._config.max_retries + 1
        # 메서드/URL/헤더 조합이 안전할 때만 캐시 키를 만들고 GET 응답을 재사용한다.
        cache_key = self._make_cache_key(method=method, url=url, params=params, headers=headers)
        request_context = _request_context(dataset_id=dataset_id, provider=provider)
        if cache_key is not None and self._cache is not None:
            cached_body = self._cache.get(cache_key)
            if cached_body is not None:
                logger.debug(
                    "transport cache hit",
                    extra={
                        "url": url,
                        "cache_key": cache_key,
                        **request_context,
                    },
                )
                return httpx.Response(
                    status_code=200,
                    content=cached_body,
                    request=httpx.Request(method.upper(), url, params=params, headers=headers),
                )

        for attempt in range(1, total_attempts + 1):
            retry_delay: float | None = None
            try:
                logger.debug(
                    "HTTP request start",
                    extra={
                        "method": method,
                        "url": url,
                        "attempt": attempt,
                        "max_retries": self._config.max_retries,
                        **request_context,
                    },
                )

                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        "HTTP request params",
                        extra={
                            "method": method,
                            "url": url,
                            "params": _sanitize_params(params),
                            **request_context,
                        },
                    )

                response = self.client.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=headers,
                    content=content,
                    json=json_body,
                )
                _ = response.raise_for_status()

                logger.debug(
                    "HTTP request success",
                    extra={
                        "method": method,
                        "url": url,
                        "status_code": response.status_code,
                        "attempt": attempt,
                        **request_context,
                    },
                )

                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        "HTTP response preview",
                        extra={
                            "status_code": response.status_code,
                            "content_type": response.headers.get("content-type", ""),
                            "content_length": len(response.content),
                            "preview": _response_preview(response),
                            **request_context,
                        },
                    )

                if (
                    cache_key is not None
                    and self._cache is not None
                    and 200 <= response.status_code < 300
                ):
                    self._cache.set(cache_key, response.content, self._cache_ttl_seconds)
                    logger.debug(
                        "transport cache miss; stored",
                        extra={
                            "url": url,
                            "cache_key": cache_key,
                            **request_context,
                        },
                    )
                return response

            except httpx.TimeoutException as exc:
                logger.debug(
                    "HTTP request timeout",
                    extra={
                        "method": method,
                        "url": url,
                        "attempt": attempt,
                        "exception_type": type(exc).__name__,
                        **request_context,
                    },
                )
                if attempt >= total_attempts:
                    raise TransportTimeoutError(
                        f"Request timed out after {attempt} attempts: {method} {url}"
                    ) from exc

            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                logger.debug(
                    "HTTP status error",
                    extra={
                        "method": method,
                        "url": url,
                        "attempt": attempt,
                        "status_code": status_code,
                        **request_context,
                    },
                )
                if not _is_retryable_status(status_code) or attempt >= total_attempts:
                    raise TransportError(
                        f"HTTP status error {status_code} for {method} {url}"
                    ) from exc

                retry_after = cast(str | None, exc.response.headers.get("Retry-After"))
                if retry_after is not None:
                    retry_delay = _parse_retry_after(retry_after)

            except httpx.RequestError as exc:
                logger.debug(
                    "HTTP request error",
                    extra={
                        "method": method,
                        "url": url,
                        "attempt": attempt,
                        "exception_type": type(exc).__name__,
                        **request_context,
                    },
                )
                if attempt >= total_attempts:
                    raise TransportError(
                        f"Request failed after {attempt} attempts: {method} {url}"
                    ) from exc

            delay: float
            if retry_delay is not None:
                # 서버가 Retry-After를 주면 지수 백오프보다 서버 힌트를 우선한다.
                delay = retry_delay
            else:
                delay = cast(float, self._config.retry_backoff_factor * (2 ** (attempt - 1)))
            logger.debug(
                "Retrying HTTP request",
                extra={
                    "method": method,
                    "url": url,
                    "attempt": attempt,
                    "delay_seconds": delay,
                    **request_context,
                },
            )
            time.sleep(delay)

        msg = "unreachable transport retry state"
        raise RuntimeError(msg)

    def _make_cache_key(
        self,
        *,
        method: str,
        url: str,
        params: dict[str, str] | None,
        headers: dict[str, str] | None,
    ) -> str | None:
        """캐시 가능한 GET 요청에 대해서만 캐시 키를 계산한다."""
        if self._cache is None:
            return None
        if method.upper() != "GET":
            return None
        if _contains_sensitive_headers(headers):
            return None
        return make_cache_key(method, url, params, _cache_headers_subset(headers))


def _is_retryable_status(status_code: int) -> bool:
    """HTTP 상태 코드가 재시도 대상인지 반환한다."""
    return status_code == 429 or 500 <= status_code <= 599


def _request_context(*, dataset_id: str | None, provider: str | None) -> dict[str, str]:
    """로그 extra에 넣을 dataset/provider 문맥 딕셔너리를 만든다."""
    context: dict[str, str] = {}
    if dataset_id is not None:
        context["dataset_id"] = dataset_id
    if provider is not None:
        context["provider"] = provider
    return context


def _merge_headers(
    base_headers: Mapping[str, str] | None,
    override_headers: Mapping[str, str] | None,
) -> dict[str, str] | None:
    """기본 헤더와 재정의 헤더를 병합한 새 딕셔너리를 반환한다."""
    if base_headers is None and override_headers is None:
        return None

    merged_headers: dict[str, str] = {}
    if base_headers is not None:
        merged_headers.update(base_headers)
    if override_headers is not None:
        merged_headers.update(override_headers)
    return merged_headers


def _sanitize_params(params: dict[str, str] | None) -> dict[str, str]:
    """민감한 파라미터 값을 가린 로그용 파라미터 사본을 만든다."""
    if params is None:
        return {}

    sanitized: dict[str, str] = {}
    for key, value in params.items():
        if key.casefold() in _SENSITIVE_PARAM_KEYS:
            sanitized[key] = "[REDACTED]"
        else:
            sanitized[key] = str(value)
    return sanitized


def _cache_headers_subset(headers: dict[str, str] | None) -> dict[str, str]:
    """캐시 키 계산에 안전한 헤더만 추려 반환한다."""
    if headers is None:
        return {}
    return {
        key: value for key, value in headers.items() if key.casefold() not in _SENSITIVE_PARAM_KEYS
    }


def _contains_sensitive_headers(headers: dict[str, str] | None) -> bool:
    """헤더에 민감한 키가 포함되어 있는지 확인한다."""
    if headers is None:
        return False
    return any(key.casefold() in _SENSITIVE_PARAM_KEYS for key in headers)


def _response_preview(response: httpx.Response, max_chars: int = 500) -> str:
    """응답 본문을 디버그 로그용 짧은 미리보기 문자열로 만든다."""
    content_type = cast(str, response.headers.get("content-type", "")).casefold()
    is_text = (
        content_type.startswith("text/")
        or "json" in content_type
        or "xml" in content_type
        or "javascript" in content_type
    )

    if not is_text:
        return f"[binary content, {len(response.content)} bytes]"

    try:
        return response.text[:max_chars]
    except (LookupError, UnicodeDecodeError, ValueError):
        return "[decode error]"


def _parse_retry_after(header_value: str) -> float | None:
    """``Retry-After`` 헤더 값을 초 단위 지연으로 파싱한다.

    RFC 7231 §7.1.3에 따라 delta-seconds와 HTTP-date 형식을 모두 지원한다.
    값을 파싱할 수 없으면 None을 반환한다.
    """

    normalized = header_value.strip()

    try:
        return max(float(int(normalized)), 0.0)
    except ValueError:
        pass

    try:
        retry_at = parsedate_to_datetime(normalized)
    except (TypeError, ValueError, IndexError, OverflowError):
        return None

    if retry_at.tzinfo is None:
        retry_at = retry_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    return max((retry_at - now).total_seconds(), 0.0)


__all__ = ["HttpTransport", "TransportConfig", "TransportRequirements"]
