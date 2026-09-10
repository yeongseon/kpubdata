"""Generic Executor — 선언적 spec만으로 데이터셋 조회를 수행한다.

spec 시스템(#378)의 실행 계층이다. ``kpubdata.core.spec.SpecDefinition``가
선언한 인증·파라미터·페이지네이션·envelope·에러 규칙을 그대로 해석해
기존 어댑터와 동일한 관찰 가능한 동작(RecordBatch 의미론)을 낸다.

범위(파일럿):
- 인증: ``query_param`` (그 외는 미구현 — 커스텀 어댑터가 담당)
- 페이지네이션: ``page_no_rows``, ``none`` (그 외 미구현)
- envelope: ``datago_standard`` (경로 기반 일반 추출 — data.go.kr 계열 공용)
- 에러: ``header_result_code`` (data.go.kr resultCode 표준 표)

계층 규칙: core는 providers를 import하지 않는다. datago 어댑터의 동작은
복제하되 의존하지 않는다(검증: tests/unit/core/test_executor.py).
"""

from __future__ import annotations

import logging

import httpx

from kpubdata.config import KPubDataConfig
from kpubdata.core.capability import Operation, PaginationMode, QuerySupport
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.core.representation import Representation
from kpubdata.core.spec import SpecDefinition
from kpubdata.exceptions import (
    AuthError,
    DatasetNotFoundError,
    InvalidRequestError,
    ProviderResponseError,
    RateLimitError,
    ServiceUnavailableError,
    TransportError,
)
from kpubdata.transport.decode import decode_json, decode_xml, detect_content_type
from kpubdata.transport.http import HttpTransport

logger = logging.getLogger("kpubdata.core.executor")

_AUTH_ERROR_CODES = frozenset({"30", "31", "20", "32"})
_SERVICE_UNAVAILABLE_CODES = frozenset({"01", "02"})
_DEFAULT_PAGE_SIZE = 100
# core가 providers를 import하지 않기 위해, datago 403 힌트를 일반화해 재정의한다.
_FORBIDDEN_HINT = (
    "Provider returned 403. This usually means the specific API has not been activated "
    "(활용신청) for your key. Check the dataset's documentation page for your provider."
)


def _resolve_path(path: str | None, spec: SpecDefinition | None = None) -> str | None:
    """경로의 ``{operation}`` 플레이스홀더를 해당 데이터셋의 operation으로 치환한다."""
    if path is None:
        return None
    if spec is None:
        return path
    return path.replace("{operation}", spec.endpoint.operation)


def _dot_get(payload: object, path: str | None) -> object | None:
    """점 경로로 페이로드를 순회한다.

    숫자 세그먼트는 배열 인덱스로 취급한다(예: ``AJGCF.0.head.0.list_total_count``).
    특수 경로 ``$`` 는 루트 페이로드 자체를 반환한다(kosis 최상위 배열 등).
    """
    if path is None:
        return None
    if path == "$":
        return payload
    current: object = payload
    for raw_segment in path.split("."):
        if isinstance(current, dict):
            current = current.get(raw_segment)
        elif isinstance(current, list) and raw_segment.lstrip("-").isdigit():
            index = int(raw_segment)
            current = current[index] if -len(current) <= index < len(current) else None
        else:
            return None
        if current is None:
            return None
    return current


def _to_int(value: object) -> int | None:
    """문자열/정수를 int로 변환한다(불가·불리언은 None)."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _normalize_item_list(value: object) -> list[dict[str, object]]:
    """items 리프 값을 레코드 dict 목록으로 정규화한다(단일 dict → 1개 리스트)."""
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _apply_transform(value: object, transform: str) -> object:
    """단일 필드 변환을 적용한다(값이 없으면 그대로 반환)."""
    if value is None:
        return None
    if isinstance(value, str) and transform == "strip_comma":
        return value.replace(",", "")
    if (
        isinstance(value, str)
        and transform == "date_yyyymmdd"
        and len(value) == 8
        and value.isdigit()
    ):
        return f"{value[:4]}-{value[4:6]}-{value[6:]}"
    if (
        isinstance(value, str)
        and transform == "date_yyyymm"
        and len(value) == 6
        and value.isdigit()
    ):
        return f"{value[:4]}-{value[4:]}"
    return value


def _cast_field(value: object, field_type: str) -> object:
    """선언된 타입으로 캐스팅한다(실패 시 원문을 보존한다)."""
    if value is None:
        return None
    if field_type == "integer":
        coerced = _to_int(value)
        return coerced if coerced is not None else value
    if field_type == "number":
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return value
    return value


class SpecExecutor:
    """spec 정의를 해석해 조회를 실행하는 Provider 비종속 실행기."""

    def __init__(self, transport: HttpTransport, config: KPubDataConfig) -> None:
        """전송 계층과 설정을 주입받아 실행기를 초기화한다."""
        self._transport = transport
        self._config = config

    # ------------------------------------------------------------------
    # 요청 조립
    # ------------------------------------------------------------------

    def _resolve_format_value(self, spec: SpecDefinition, format_hint: str | None) -> str | None:
        """format_hint에 해당하는 포맷 파라미터 값을 spec에서 해석한다."""
        format_param = spec.endpoint.format_param
        if format_param is None or not format_param.name:
            return None
        hint = format_hint or spec.response.format
        if format_param.values:
            return format_param.values.get(hint)
        return hint

    def build_params(
        self, spec: SpecDefinition, query: Query, format_hint: str | None = None
    ) -> dict[str, str]:
        """인증·포맷·페이지네이션·필터를 조립한 쿼리 파라미터를 만든다.

        예외:
            InvalidRequestError: 파라미터 이름이 선언되지 않은 페이지네이션 방식인 경우.
        """
        params: dict[str, str] = {}

        if spec.auth.type == "query_param":
            if not spec.auth.param_name:
                msg = f"{spec.id}: auth.query_param 방식은 param_name 선언이 필요합니다."
                raise InvalidRequestError(msg, provider=spec.provider, dataset_id=spec.id)
            provider_key = spec.auth.provider_key or spec.provider
            params[spec.auth.param_name] = self._config.require_provider_key(provider_key)
        elif spec.auth.type == "path_segment":
            # 키는 URL 경로(path_template의 {key})로 싣는다 — 쿼리에서는 제거된다.
            template = spec.endpoint.path_template or ""
            if "{key}" not in template:
                msg = f"{spec.id}: path_segment 인증은 path_template의 {{key}}가 필요합니다."
                raise InvalidRequestError(msg, provider=spec.provider, dataset_id=spec.id)
            params[spec.auth.param_name or "__path_key__"] = self._config.require_provider_key(
                spec.auth.provider_key or spec.provider
            )
        elif spec.auth.type != "none":
            msg = (
                f"{spec.id}: auth.type={spec.auth.type!r}은(는) 아직 spec 실행기가 "
                "지원하지 않습니다."
            )
            raise NotImplementedError(msg)

        format_value = self._resolve_format_value(spec, format_hint)
        format_param = spec.endpoint.format_param
        if format_param is not None and format_param.name and format_value is not None:
            params[format_param.name] = format_value

        page = query.page or 1
        page_size = query.page_size or _DEFAULT_PAGE_SIZE
        if spec.pagination.max_size is not None:
            page_size = min(page_size, spec.pagination.max_size)
        if spec.pagination.type == "page_no_rows":
            page_param = spec.pagination.page_param or "pageNo"
            size_param = spec.pagination.size_param or "numOfRows"
            params[page_param] = str(page)
            params[size_param] = str(page_size)
        elif spec.pagination.type in {"pindex_psize", "page_display"}:
            # lofin(pIndex/pSize, 1-기반)·law(page/display) — 쿼리 파라미터 방식
            defaults: dict[str, tuple[str, str, int, int]] = {
                "pindex_psize": ("pIndex", "pSize", 1, 100),
                "page_display": ("page", "display", 1, 20),
            }
            default_page_p, default_size_p, default_page, default_size = defaults[
                spec.pagination.type
            ]
            page_param = spec.pagination.page_param or default_page_p
            size_param = spec.pagination.size_param or default_size_p
            params[page_param] = str(query.page or default_page)
            params[size_param] = str(query.page_size or default_size)
        elif spec.pagination.type == "index_range":
            # bok/seoul 계열 — start/end가 URL 경로에 들어간다(path_template {{start}}/{{end}}).
            if not spec.endpoint.path_template:
                msg = f"{spec.id}: index_range 페이지네이션은 path_template이 필요합니다."
                raise InvalidRequestError(msg, provider=spec.provider, dataset_id=spec.id)
        elif spec.pagination.type != "none":
            msg = (
                f"{spec.id}: pagination.type={spec.pagination.type!r}은(는) "
                "아직 spec 실행기가 지원하지 않습니다."
            )
            raise NotImplementedError(msg)

        reserved = {key.lower() for key in params}
        alias_map = {param.exposed_name: param.name for param in spec.params}
        for key, raw_value in query.filters.items():
            # 인증·포맷·페이지 파라미터는 이미 채웠으므로 사용자 필터로 덮어쓰지 않는다.
            if key.lower() in reserved:
                continue
            provider_name = alias_map.get(key, key)
            params[provider_name] = str(raw_value)

        return params

    # ------------------------------------------------------------------
    # 전송·디코딩
    # ------------------------------------------------------------------

    def build_url(
        self,
        spec: SpecDefinition,
        page: int = 1,
        page_size: int = _DEFAULT_PAGE_SIZE,
        api_key: str = "",
    ) -> str:
        """spec 엔드포인트 URL을 조립한다.

        ``endpoint.path_template``이 있으면 ``{key}``·``{operation}``·``{start}``·``{end}``
        플레이스홀더를 치환한다(bok/seoul 계열의 경로 내 키·범위). 없으면
        ``{base}/{operation}`` 기본 형태를 쓴다.
        """
        template = spec.endpoint.path_template
        if template:
            start_index = spec.pagination.start_index_base or 1
            start = (page - 1) * page_size + start_index
            end = start + page_size - 1
            return template.format(
                base_url=spec.endpoint.base_url.rstrip("/"),
                key=api_key,
                operation=spec.endpoint.operation,
                start=start,
                end=end,
            )
        return f"{spec.endpoint.base_url.rstrip('/')}/{spec.endpoint.operation.lstrip('/')}"

    def _request(self, spec: SpecDefinition, params: dict[str, str]) -> dict[str, object]:
        """spec 엔드포인트로 GET 요청을 보내고 디코딩된 dict를 반환한다.

        예외:
            AuthError: 전송 계층 403의 경우(활용신청 힌트 포함).
            ProviderResponseError: 디코딩 결과가 dict가 아닌 경우.
        """
        page_part = params.get(spec.pagination.page_param or "", "1")
        size_part = params.get(spec.pagination.size_param or "", str(_DEFAULT_PAGE_SIZE))
        url = self.build_url(
            spec,
            page=_to_int(page_part) or 1,
            page_size=_to_int(size_part) or _DEFAULT_PAGE_SIZE,
            api_key=params.get(spec.auth.param_name or "", "")
            if spec.auth.type == "path_segment"
            else "",
        )
        if spec.auth.type == "path_segment":
            params = {k: v for k, v in params.items() if k != (spec.auth.param_name or "")}
        try:
            response = self._transport.request(
                "GET",
                url,
                params=params,
                dataset_id=spec.id,
                provider=spec.provider,
            )
        except TransportError as exc:
            cause = exc.__cause__
            if isinstance(cause, httpx.HTTPStatusError) and cause.response.status_code == 403:
                raise AuthError(
                    _FORBIDDEN_HINT,
                    provider=spec.provider,
                    dataset_id=spec.id,
                    status_code=403,
                ) from exc
            raise
        try:
            content_type = detect_content_type(response)
            if content_type == "xml":
                decoded: object = decode_xml(response.content)
            else:
                decoded = decode_json(response.content)
        except ImportError as exc:
            msg = "XML 응답을 파싱하려면 선택 의존성이 필요합니다: pip install kpubdata[xml]"
            raise InvalidRequestError(msg, provider=spec.provider, dataset_id=spec.id) from exc

        if isinstance(decoded, dict):
            return decoded
        msg = f"{spec.id}: 응답 페이로드가 객체가 아닙니다({type(decoded).__name__})."
        raise ProviderResponseError(msg, provider=spec.provider, dataset_id=spec.id)

    # ------------------------------------------------------------------
    # envelope·에러 매핑
    # ------------------------------------------------------------------

    def _require_supported_envelope(self, spec: SpecDefinition) -> None:
        """파일럿 범위 밖 envelope를 명확히 거부한다."""
        if spec.response.envelope != "datago_standard":
            msg = (
                f"{spec.id}: envelope={spec.response.envelope!r}은(는) "
                "아직 spec 실행기가 지원하지 않습니다."
            )
            raise NotImplementedError(msg)

    def _raise_for_code(self, spec: SpecDefinition, code: str, message: str) -> None:
        """에러 코드를 표준 예외로 매핑한다(data.go.kr resultCode 표준 표)."""
        if code in _AUTH_ERROR_CODES:
            raise AuthError(message, provider=spec.provider, dataset_id=spec.id, provider_code=code)
        if code == "22":
            raise RateLimitError(
                message,
                provider=spec.provider,
                dataset_id=spec.id,
                provider_code=code,
                retryable=False,
            )
        if code == "10":
            raise InvalidRequestError(
                message, provider=spec.provider, dataset_id=spec.id, provider_code=code
            )
        if code == "12":
            raise DatasetNotFoundError(
                message, provider=spec.provider, dataset_id=spec.id, provider_code=code
            )
        if code in _SERVICE_UNAVAILABLE_CODES:
            raise ServiceUnavailableError(
                message, provider=spec.provider, dataset_id=spec.id, provider_code=code
            )
        raise ProviderResponseError(
            message, provider=spec.provider, dataset_id=spec.id, provider_code=code
        )

    def _check_error(self, spec: SpecDefinition, payload: dict[str, object]) -> None:
        """에러 코드 경로를 검사하고 실패 코드면 예외를 발생시킨다."""
        error = spec.response.error
        raw_code = _dot_get(payload, error.code_path)
        if isinstance(raw_code, str):
            code = raw_code
        elif isinstance(raw_code, int) and not isinstance(raw_code, bool):
            code = str(raw_code)
        else:
            msg = f"{spec.id}: 응답 envelope에서 에러 코드를 찾을 수 없습니다({error.code_path!r})."
            raise ProviderResponseError(msg, provider=spec.provider, dataset_id=spec.id)

        ok_strings = {str(value) for value in error.ok_values}
        code_as_int = _to_int(code)
        is_success = code in ok_strings or (code_as_int == 0)
        if is_success:
            return

        raw_message = _dot_get(payload, _message_path(error.code_path))
        message = (
            raw_message
            if isinstance(raw_message, str) and raw_message
            else "Provider returned error"
        )
        self._raise_for_code(spec, code, message)

    def _extract_items(
        self, spec: SpecDefinition, payload: dict[str, object]
    ) -> list[dict[str, object]]:
        """items_path 규칙으로 레코드 목록을 추출한다."""
        items_path = spec.response.items_path or ""
        if "." in items_path:
            container_path, leaf = items_path.rsplit(".", 1)
        else:
            container_path, leaf = "", items_path
        container = _dot_get(payload, container_path) if container_path else payload
        if container is None:
            return []
        value = container.get(leaf) if isinstance(container, dict) else None
        return _normalize_item_list(value)

    def _extract_total_count(self, spec: SpecDefinition, payload: dict[str, object]) -> int | None:
        """total_count_path 규칙으로 총건수를 추출한다(없으면 None)."""
        raw = _dot_get(payload, spec.response.total_count_path)
        coerced = _to_int(raw)
        return coerced if coerced else None

    # ------------------------------------------------------------------
    # 정규화
    # ------------------------------------------------------------------

    def _normalize_fields(
        self, spec: SpecDefinition, items: list[dict[str, object]]
    ) -> list[dict[str, object]]:
        """fields[] 선언이 있을 때만 rename·transform·캐스팅을 적용한다."""
        if not spec.fields:
            return items
        normalized: list[dict[str, object]] = []
        for item in items:
            record: dict[str, object] = dict(item)
            for field in spec.fields:
                source_name = field.source_name or field.name
                if source_name not in record:
                    continue
                value = _apply_transform(record[source_name], field.transform or "")
                record[field.name] = _cast_field(value, field.type)
                if source_name != field.name:
                    record.pop(source_name, None)
            normalized.append(record)
        return normalized

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def query(
        self,
        spec: SpecDefinition,
        dataset: DatasetRef,
        query: Query,
        format_hint: str | None = None,
    ) -> RecordBatch:
        """spec에 따라 조회를 실행해 RecordBatch를 반환한다."""
        self._require_supported_envelope(spec)
        params = self.build_params(spec, query, format_hint=format_hint)
        payload = self._request(spec, params)
        self._check_error(spec, payload)

        items = self._normalize_fields(spec, self._extract_items(spec, payload))
        total_count = self._extract_total_count(spec, payload)

        page = query.page or 1
        page_size = query.page_size or _DEFAULT_PAGE_SIZE
        if spec.pagination.max_size is not None:
            page_size = min(page_size, spec.pagination.max_size)
        has_next = (total_count and page * page_size < total_count) or (
            not total_count and len(items) == page_size
        )
        next_page = page + 1 if has_next else None

        if not items:
            logger.debug("Spec executor: zero items", extra={"dataset_id": spec.id, "page": page})

        return RecordBatch(
            items=items,
            dataset=dataset,
            total_count=total_count,
            next_page=next_page,
            raw=payload,
        )

    def fetch(
        self,
        spec: SpecDefinition,
        query: Query,
        format_hint: str | None = None,
    ) -> tuple[dict[str, str], dict[str, object]]:
        """요청 파라미터와 디코딩된 원본 페이로드를 함께 반환한다(record용).

        query와 달리 envelope 해석·정규화를 수행하지 않는다 — 기록 도구가
        raw/expected를 각자 저장하기 위한 저수준 진입점이다.
        """
        self._require_supported_envelope(spec)
        params = self.build_params(spec, query, format_hint=format_hint)
        payload = self._request(spec, params)
        return params, payload

    def request_raw(
        self,
        spec: SpecDefinition,
        params: dict[str, object],
        format_hint: str | None = None,
    ) -> dict[str, object]:
        """envelope 해석 없이 디코딩된 원본 페이로드를 반환한다(raw 비상구)."""
        string_params: dict[str, str] = {key: str(value) for key, value in params.items()}
        if spec.auth.type == "query_param" and spec.auth.param_name:
            provider_key = spec.auth.provider_key or spec.provider
            string_params.setdefault(
                spec.auth.param_name, self._config.require_provider_key(provider_key)
            )
        format_value = self._resolve_format_value(spec, format_hint)
        format_param = spec.endpoint.format_param
        if format_param is not None and format_param.name and format_value is not None:
            string_params.setdefault(format_param.name, format_value)
        return self._request(spec, string_params)


def raise_for_code(spec: SpecDefinition, code: str, message: str) -> None:
    """에러 코드를 표준 예외로 매핑한다(data.go.kr resultCode 표준 표)."""
    if code in _AUTH_ERROR_CODES:
        raise AuthError(message, provider=spec.provider, dataset_id=spec.id, provider_code=code)
    if code == "22":
        raise RateLimitError(
            message, provider=spec.provider, dataset_id=spec.id, provider_code=code, retryable=False
        )
    if code == "10":
        raise InvalidRequestError(
            message, provider=spec.provider, dataset_id=spec.id, provider_code=code
        )
    if code == "12":
        raise DatasetNotFoundError(
            message, provider=spec.provider, dataset_id=spec.id, provider_code=code
        )
    if code in _SERVICE_UNAVAILABLE_CODES:
        raise ServiceUnavailableError(
            message, provider=spec.provider, dataset_id=spec.id, provider_code=code
        )
    raise ProviderResponseError(
        message, provider=spec.provider, dataset_id=spec.id, provider_code=code
    )


def check_payload_error(spec: SpecDefinition, payload: dict[str, object]) -> None:
    """에러 코드 경로를 검사하고 실패 코드면 예외를 발생시킨다(record·verify 공용)."""
    error = spec.response.error
    if error.style == "err_field":
        # kosis류: 코드 체계가 없고 err 필드 존재 자체가 실패를 뜻한다.
        err_raw = payload.get("err")
        if isinstance(err_raw, (str, dict)):
            raise ProviderResponseError(
                f"{spec.id}: Provider 오류 응답: {str(err_raw)[:200]}",
                provider=spec.provider,
                dataset_id=spec.id,
            )
        return
    raw_code = _dot_get(payload, _resolve_path(error.code_path, spec))
    # 폴백: 한국관광공사 KorService류는 에러를 envelope 밖 최상단 resultCode로
    # 평면 반환한다(성공은 정상 envelope). 선언 경로에 없으면 최상단을 확인한다.
    if raw_code is None and isinstance(payload.get("resultCode"), (str, int)):
        raw_code = payload.get("resultCode")
    if isinstance(raw_code, str):
        code = raw_code
    elif isinstance(raw_code, int) and not isinstance(raw_code, bool):
        code = str(raw_code)
    else:
        msg = f"{spec.id}: 응답 envelope에서 에러 코드를 찾을 수 없습니다({error.code_path!r})."
        raise ProviderResponseError(msg, provider=spec.provider, dataset_id=spec.id)

    ok_strings = {str(value) for value in error.ok_values}
    code_as_int = _to_int(code)
    is_success = code in ok_strings or (code_as_int == 0)
    if is_success:
        return

    raw_message = _dot_get(payload, _resolve_path(_message_path(error.code_path), spec))
    if not isinstance(raw_message, str) or not raw_message:
        raw_message = payload.get("resultMsg")
    if not isinstance(raw_message, str) or not raw_message:
        raw_message = payload.get("errMsg")
    message = (
        raw_message if isinstance(raw_message, str) and raw_message else "Provider returned error"
    )
    raise_for_code(spec, code, message)


def extract_items(spec: SpecDefinition, payload: dict[str, object]) -> list[dict[str, object]]:
    """spec의 items_path 규칙으로 레코드 목록을 추출한다(record·verify 공용).

    - ``{operation}`` 플레이스홀더 지원(lofin 계열: ``{operation}.1.row``)
    - ``$`` 는 루트(kosis 최상위 배열)
    - envelope ``neis_double_list`` 는 블록별 row를 병합한다
    """
    if spec.response.envelope == "neis_double_list":
        return _extract_neis_rows(spec, payload)
    resolved = _resolve_path(spec.response.items_path, spec) or ""
    if resolved == "$":
        return _normalize_item_list(payload)
    if "." in resolved:
        container_path, leaf = resolved.rsplit(".", 1)
    else:
        container_path, leaf = "", resolved
    container = _dot_get(payload, container_path) if container_path else payload
    if container is None:
        return []
    value = container.get(leaf) if isinstance(container, dict) else None
    return _normalize_item_list(value)


def _extract_neis_rows(spec: SpecDefinition, payload: dict[str, object]) -> list[dict[str, object]]:
    """NEIS 이중 리스트 envelope: ``{operation}[].row`` 블록을 모두 병합한다."""
    blocks = payload.get(spec.endpoint.operation)
    rows: list[dict[str, object]] = []
    if not isinstance(blocks, list):
        return rows
    for block in blocks:
        if not isinstance(block, dict):
            continue
        row_value = block.get("row")
        if isinstance(row_value, list):
            rows.extend(item for item in row_value if isinstance(item, dict))
        elif isinstance(row_value, dict):
            rows.append(row_value)
    return rows


def extract_total_count(spec: SpecDefinition, payload: dict[str, object]) -> int | None:
    """spec의 total_count_path 규칙으로 총건수를 추출한다(없으면 None)."""
    resolved = _resolve_path(spec.response.total_count_path, spec)
    raw = _dot_get(payload, resolved)
    coerced = _to_int(raw)
    return coerced if coerced else None


def _message_path(code_path: str | None) -> str | None:
    """resultCode 경로에서 대응하는 resultMsg 경로를 유추한다."""
    if not code_path:
        return None
    segments = code_path.split(".")
    segments[-1] = "resultMsg"
    return ".".join(segments)


def build_spec_dataset_ref(spec: SpecDefinition) -> DatasetRef:
    """SpecDefinition을 catalogue와 동일한 의미론의 DatasetRef로 변환한다."""
    paginated = spec.pagination.type in {"page_no_rows", "page_display", "pindex_psize"}
    query_support = QuerySupport(
        pagination=PaginationMode.OFFSET if paginated else PaginationMode.NONE,
        filterable_fields=frozenset(param.exposed_name for param in spec.params),
        max_page_size=spec.pagination.max_size,
    )
    return DatasetRef(
        id=spec.id,
        provider=spec.provider,
        dataset_key=spec.dataset_key,
        name=spec.title,
        representation=Representation.API_JSON,
        operations=frozenset({Operation.LIST, Operation.RAW}),
        query_support=query_support,
        description=spec.description,
        tags=(spec.provider, "spec"),
        source_url=spec.source.url if spec.source else None,
    )


class SpecDatasetAdapter:
    """하나의 Provider 분량 spec 묶음을 ProviderAdapter 프로토콜로 노출한다.

    레지스트리 통합 전 파일럿용: 기존 어댑터와 동일한 인터페이스를 제공하되
    spec 실행기가 조회를 수행한다. call_raw는 항상 원본 페이로드를 반환한다.
    """

    def __init__(self, provider: str, specs: list[SpecDefinition], executor: SpecExecutor) -> None:
        """Provider 식별자·spec 목록·실행기로 어댑터를 초기화한다."""
        self._provider = provider
        self._specs = {spec.dataset_key: spec for spec in specs if spec.provider == provider}
        self._executor = executor
        self.requires_api_key: bool = any(spec.auth.type != "none" for spec in self._specs.values())

    @property
    def name(self) -> str:
        """Provider 식별자를 반환한다."""
        return self._provider

    def list_datasets(self) -> list[DatasetRef]:
        """보유한 spec 전체를 DatasetRef로 반환한다."""
        return [build_spec_dataset_ref(spec) for spec in self._specs.values()]

    def search_datasets(self, text: str) -> list[DatasetRef]:
        """id·제목·설명에 대한 부분 문자열 검색 결과를 반환한다."""
        needle = text.lower()
        return [
            build_spec_dataset_ref(spec)
            for spec in self._specs.values()
            if needle in spec.id.lower()
            or needle in spec.title.lower()
            or (spec.description is not None and needle in spec.description.lower())
        ]

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        """Provider 로컬 키로 DatasetRef를 해석한다.

        예외:
            DatasetNotFoundError: 알 수 없는 키인 경우.
        """
        spec = self._specs.get(dataset_key)
        if spec is None:
            msg = f"Unknown dataset key for spec adapter: {self._provider}.{dataset_key}"
            raise DatasetNotFoundError(msg, provider=self._provider)
        return build_spec_dataset_ref(spec)

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        """spec 실행기로 정규 목록 질의를 실행한다."""
        spec = self._specs.get(dataset.dataset_key)
        if spec is None:
            msg = f"Unknown dataset key for spec adapter: {dataset.id}"
            raise DatasetNotFoundError(msg, provider=self._provider, dataset_id=dataset.id)
        return self._executor.query(spec, dataset, query)

    def get_schema(self, dataset: DatasetRef) -> SchemaDescriptor | None:
        """아직 스키마 메타데이터를 지원하지 않는다(정직한 선언)."""
        return None

    def call_raw(self, dataset: DatasetRef, operation: str, params: dict[str, object]) -> object:
        """원본 페이로드를 반환하는 raw 비상구를 보장한다."""
        spec = self._specs.get(dataset.dataset_key)
        if spec is None:
            msg = f"Unknown dataset key for spec adapter: {dataset.id}"
            raise DatasetNotFoundError(msg, provider=self._provider, dataset_id=dataset.id)
        return self._executor.request_raw(spec, params)


__all__ = [
    "SpecDatasetAdapter",
    "SpecExecutor",
    "build_spec_dataset_ref",
    "check_payload_error",
    "extract_items",
    "extract_total_count",
    "raise_for_code",
]
