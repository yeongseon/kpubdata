"""선언적 데이터셋 spec 로더 — YAML 정의를 검증된 데이터클래스로 변환한다.

spec 시스템(#378)의 읽기 계층이다. 데이터셋 정의는
``src/kpubdata/specs/{provider}/{dataset_key}.yaml``에 담기며
``specs/schema.json``이 계약(contract)이다. Generic Executor
(``kpubdata.core.executor``)가 이 모듈의 산출물만으로 조회를 수행한다.

설계 원칙:
- 스키마 검증의 완전한 형태는 ``scripts/validate_spec.py``(jsonschema)가 담당하고,
  이 모듈은 런타임에 필요한 최소 구조 검증만 수행한다(의존성 최소화).
- 알 수 없는 키는 거부하지 않고 ``raw_metadata``에 보존해 상위 호환을 유지한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from importlib import resources
from pathlib import Path

import yaml

from kpubdata.exceptions import InvalidRequestError

# schema.json과 동일하게 유지되는 enum 집합(런타임 구조 검증용).
_AUTH_TYPES = frozenset({"query_param", "path_segment", "oauth_exchange", "none"})
_PAGINATION_TYPES = frozenset(
    {"page_no_rows", "page_display", "pindex_psize", "index_range", "date_window", "none"}
)
_FORMATS = frozenset({"json", "xml", "geojson"})
_ENVELOPES = frozenset(
    {
        "datago_standard",
        "datago_gyeonggi_msg",
        "datago_its_flat",
        "datago_odcloud",
        "localdata_rows",
        "semas_rows",
        "lofin_head_row",
        "neis_double_list",
        "kipris_items",
        "seoul_service_row",
        "bok_statistic_row",
        "kosis_top_array",
        "law_item_key",
        "korean_channel",
        "fds_row",
    }
)
_ERROR_STYLES = frozenset(
    {"header_result_code", "result_code", "status_code", "err_cd", "err_field", "http_status"}
)
_STATUSES = frozenset({"active", "deprecated", "broken", "unstable"})


@dataclass(slots=True, frozen=True)
class SourceRef:
    """원본 문서 출처 정보."""

    url: str | None = None
    doc_version: str | None = None
    verified_at: date | None = None


@dataclass(slots=True, frozen=True)
class FormatParamSpec:
    """응답 포맷 선택 파라미터(data.go.kr 계열의 dataType/_type/resultType 등)."""

    name: str
    values: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class EndpointSpec:
    """엔드포인트 조립 정보."""

    base_url: str
    operation: str
    method: str = "GET"
    format_param: FormatParamSpec | None = None


@dataclass(slots=True, frozen=True)
class AuthSpec:
    """인증 방식 선언."""

    type: str
    param_name: str | None = None
    provider_key: str | None = None


@dataclass(slots=True, frozen=True)
class ParamSpec:
    """데이터 필터 파라미터 선언."""

    name: str
    type: str = "string"
    alias: str | None = None
    required: bool = False
    enum: tuple[str, ...] = ()
    description: str | None = None
    example: str | int | float | None = None

    @property
    def exposed_name(self) -> str:
        """라이브러리가 필터에 노출하는 이름(alias 우선)."""
        return self.alias or self.name


@dataclass(slots=True, frozen=True)
class ErrorSpec:
    """응답 에러 표현 선언."""

    style: str
    code_path: str | None = None
    ok_values: tuple[str | int, ...] = ()


@dataclass(slots=True, frozen=True)
class ResponseSpec:
    """응답 포맷·envelope·경로 선언."""

    format: str
    envelope: str
    items_path: str | None = None
    total_count_path: str | None = None
    error: ErrorSpec = field(default_factory=lambda: ErrorSpec(style="http_status"))


@dataclass(slots=True, frozen=True)
class PaginationSpec:
    """페이지네이션 방식 선언."""

    type: str
    page_param: str | None = None
    size_param: str | None = None
    max_size: int | None = None
    start_index_base: int | None = None


@dataclass(slots=True, frozen=True)
class FieldSpec:
    """정규화 규칙이 있는 단일 필드 선언."""

    name: str
    type: str
    source_name: str | None = None
    unit: str | None = None
    transform: str | None = None
    description: str | None = None


@dataclass(slots=True, frozen=True)
class ExampleSpec:
    """호출 예제 선언(record·smoke·예제 생성에 공통 사용)."""

    name: str
    description: str | None = None
    params: dict[str, str | int | float] = field(default_factory=dict)
    page: int | None = None
    page_size: int | None = None
    format: str | None = None


@dataclass(slots=True, frozen=True)
class SpecDefinition:
    """검증된 데이터셋 spec 정의."""

    id: str
    provider: str
    title: str
    endpoint: EndpointSpec
    auth: AuthSpec
    response: ResponseSpec
    pagination: PaginationSpec
    status: str = "active"
    description: str | None = None
    source: SourceRef | None = None
    params: tuple[ParamSpec, ...] = ()
    fields: tuple[FieldSpec, ...] = ()
    examples: tuple[ExampleSpec, ...] = ()
    last_verified: date | None = None
    raw_metadata: dict[str, object] = field(default_factory=dict)

    @property
    def dataset_key(self) -> str:
        """Provider 로컬 데이터셋 키(id의 마지막 세그먼트)."""
        return self.id.split(".", 1)[1] if "." in self.id else self.id


def _parse_date(value: object, problems: list[str], label: str) -> date | None:
    """ISO YYYY-MM-DD 문자열을 date로 변환한다(실패 시 문제 목록에 기록)."""
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            problems.append(f"{label}은(는) YYYY-MM-DD 형식이어야 합니다: {value!r}")
            return None
    problems.append(f"{label}은(는) 문자열 또는 null이어야 합니다: {type(value).__name__}")
    return None


def _parse_params(raw: object, problems: list[str]) -> tuple[ParamSpec, ...]:
    """params[] 섹션을 ParamSpec 튜플로 변환한다."""
    if raw is None:
        return ()
    if not isinstance(raw, list):
        problems.append("params는 리스트여야 합니다.")
        return ()
    parsed: list[ParamSpec] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            problems.append(f"params[{index}]은(는) 객체여야 합니다.")
            continue
        name = item.get("name")
        if not isinstance(name, str) or not name:
            problems.append(f"params[{index}].name은(는) 비어 있지 않은 문자열이어야 합니다.")
            continue
        enum_raw = item.get("enum") or []
        if not isinstance(enum_raw, list):
            problems.append(f"params[{index}].enum은(는) 리스트여야 합니다.")
            enum_raw = []
        parsed.append(
            ParamSpec(
                name=name,
                type=item.get("type", "string") if isinstance(item.get("type"), str) else "string",
                alias=item.get("alias") if isinstance(item.get("alias"), str) else None,
                required=bool(item.get("required", False)),
                enum=tuple(v for v in enum_raw if isinstance(v, str)),
                description=item.get("description")
                if isinstance(item.get("description"), str)
                else None,
                example=item.get("example")
                if isinstance(item.get("example"), (str, int, float))
                else None,
            )
        )
    return tuple(parsed)


def _section(data: dict[str, object], key: str) -> dict[str, object]:
    """매핑 내부의 하위 섹션을 dict로 반환한다(없거나 다른 타입이면 빈 dict)."""
    value = data.get(key)
    if isinstance(value, dict):
        return dict(value)
    return {}


def _get_str(section: dict[str, object], key: str) -> str | None:
    """섹션에서 비어 있지 않은 문자열 값을 꺼낸다(조건 불충족 시 None)."""
    value = section.get(key)
    if isinstance(value, str) and value:
        return value
    return None


def from_mapping(data: dict[str, object]) -> SpecDefinition:
    """스키마 구조를 따르는 매핑을 검증된 SpecDefinition으로 변환한다.

    예외:
        InvalidRequestError: 필수 누락·enum 불일치·id 불일치 등 구조 문제가
            하나라도 있으면 모든 문제를 하나의 메시지로 묶어 발생시킨다.
    """
    problems: list[str] = []

    spec_id = _get_str(data, "id")
    provider = _get_str(data, "provider")
    title = _get_str(data, "title")
    if spec_id is None:
        problems.append("id은(는) 비어 있지 않은 문자열이어야 합니다.")
    if provider is None:
        problems.append("provider은(는) 비어 있지 않은 문자열이어야 합니다.")
    if title is None:
        problems.append("title은(는) 비어 있지 않은 문자열이어야 합니다.")

    endpoint_raw = _section(data, "endpoint")
    base_url = _get_str(endpoint_raw, "base_url")
    if base_url is None:
        problems.append("endpoint.base_url은(는) 비어 있지 않은 문자열이어야 합니다.")
    operation = _get_str(endpoint_raw, "operation")
    if operation is None:
        problems.append("endpoint.operation은(는) 비어 있지 않은 문자열이어야 합니다.")
    method = _get_str(endpoint_raw, "method") or "GET"
    if method not in {"GET", "POST"}:
        problems.append(f"endpoint.method는 GET 또는 POST여야 합니다: {method!r}")
    format_param: FormatParamSpec | None = None
    fp_raw = _section(endpoint_raw, "format_param")
    fp_name = _get_str(fp_raw, "name")
    if fp_raw and fp_name is None:
        problems.append("endpoint.format_param.name은(는) 비어 있지 않은 문자열이어야 합니다.")
    if fp_name is not None:
        values_raw = _section(fp_raw, "values")
        format_param = FormatParamSpec(
            name=fp_name,
            values={k: v for k, v in values_raw.items() if isinstance(v, str)},
        )
    endpoint = (
        EndpointSpec(
            base_url=base_url or "",
            operation=operation or "",
            method=method,
            format_param=format_param,
        )
        if base_url and operation
        else None
    )

    auth_raw = _section(data, "auth")
    auth_type = _get_str(auth_raw, "type")
    auth: AuthSpec | None = None
    if auth_type is None:
        problems.append("auth.type는 필수입니다.")
    elif auth_type not in _AUTH_TYPES:
        problems.append(f"auth.type는 {_sorted(_AUTH_TYPES)} 중 하나여야 합니다: {auth_type!r}")
        auth = AuthSpec(type=auth_type)
    else:
        auth = AuthSpec(
            type=auth_type,
            param_name=_get_str(auth_raw, "param_name"),
            provider_key=_get_str(auth_raw, "provider_key"),
        )

    response_raw = _section(data, "response")
    resp_format = _get_str(response_raw, "format")
    envelope = _get_str(response_raw, "envelope")
    response: ResponseSpec | None = None
    if resp_format is None:
        problems.append("response.format는 필수입니다.")
    elif resp_format not in _FORMATS:
        problems.append(
            f"response.format는 {_sorted(_FORMATS)} 중 하나여야 합니다: {resp_format!r}"
        )
    if envelope is None:
        problems.append("response.envelope는 필수입니다.")
    elif envelope not in _ENVELOPES:
        problems.append(
            f"response.envelope는 {_sorted(_ENVELOPES)} 중 하나여야 합니다: {envelope!r}"
        )
    error_raw = _section(response_raw, "error")
    error_style = _get_str(error_raw, "style")
    if error_style is None:
        problems.append("response.error.style는 필수입니다.")
    elif error_style not in _ERROR_STYLES:
        allowed_styles = _sorted(_ERROR_STYLES)
        problems.append(
            f"response.error.style는 {allowed_styles} 중 하나여야 합니다: {error_style!r}"
        )
    if resp_format and envelope and error_style:
        ok_values_raw = error_raw.get("ok_values")
        ok_values = (
            tuple(v for v in ok_values_raw if isinstance(v, (str, int)) and not isinstance(v, bool))
            if isinstance(ok_values_raw, list)
            else ()
        )
        response = ResponseSpec(
            format=resp_format,
            envelope=envelope,
            items_path=_get_str(response_raw, "items_path"),
            total_count_path=_get_str(response_raw, "total_count_path"),
            error=ErrorSpec(
                style=error_style, code_path=_get_str(error_raw, "code_path"), ok_values=ok_values
            ),
        )

    pagination_raw = _section(data, "pagination")
    pg_type = _get_str(pagination_raw, "type")
    pagination: PaginationSpec | None = None
    if pg_type is None:
        problems.append("pagination.type는 필수입니다.")
    elif pg_type not in _PAGINATION_TYPES:
        allowed_pg = _sorted(_PAGINATION_TYPES)
        problems.append(f"pagination.type는 {allowed_pg} 중 하나여야 합니다: {pg_type!r}")
    else:
        max_size_obj = pagination_raw.get("max_size")
        if max_size_obj is not None and (
            isinstance(max_size_obj, bool) or not isinstance(max_size_obj, int) or max_size_obj < 1
        ):
            problems.append("pagination.max_size는 1 이상의 정수여야 합니다.")
            max_size_obj = None
        start_base = pagination_raw.get("start_index_base")
        pagination = PaginationSpec(
            type=pg_type,
            page_param=_get_str(pagination_raw, "page_param"),
            size_param=_get_str(pagination_raw, "size_param"),
            max_size=max_size_obj if isinstance(max_size_obj, int) else None,
            start_index_base=start_base if isinstance(start_base, int) else None,
        )

    status = _get_str(data, "status") or "active"
    if status not in _STATUSES:
        problems.append(f"status는 {_sorted(_STATUSES)} 중 하나여야 합니다: {status!r}")

    if spec_id is not None and "." not in spec_id:
        problems.append(f"id는 '{{provider}}.{{dataset_key}}' 형식이어야 합니다: {spec_id!r}")
    if spec_id is not None and provider is not None and "." in spec_id:
        id_prefix = spec_id.split(".", 1)[0]
        if id_prefix != provider:
            problems.append(f"id 접두사({id_prefix})가 provider 필드({provider})와 불일치합니다.")

    if problems:
        raise InvalidRequestError(
            "데이터셋 spec 구조 검증 실패: " + " | ".join(problems),
            provider=provider,
            dataset_id=spec_id,
        )

    source_raw = _section(data, "source")
    fields_list = data.get("fields")
    examples_list = data.get("examples")

    fields_parsed: list[FieldSpec] = []
    if isinstance(fields_list, list):
        for item in fields_list:
            if not isinstance(item, dict):
                continue
            item_dict: dict[str, object] = dict(item)
            name = _get_str(item_dict, "name")
            if name is None:
                continue
            type_value = _get_str(item_dict, "type") or "string"
            fields_parsed.append(
                FieldSpec(
                    name=name,
                    type=type_value,
                    source_name=_get_str(item_dict, "source_name"),
                    unit=_get_str(item_dict, "unit"),
                    transform=_get_str(item_dict, "transform"),
                    description=_get_str(item_dict, "description"),
                )
            )

    examples_parsed: list[ExampleSpec] = []
    if isinstance(examples_list, list):
        for item in examples_list:
            if not isinstance(item, dict):
                continue
            ex_dict: dict[str, object] = dict(item)
            name = _get_str(ex_dict, "name")
            if name is None:
                continue
            params_raw = ex_dict.get("params")
            params = (
                {
                    k: v
                    for k, v in dict(params_raw).items()
                    if isinstance(k, str)
                    and isinstance(v, (str, int, float))
                    and not isinstance(v, bool)
                }
                if isinstance(params_raw, dict)
                else {}
            )
            page_obj = ex_dict.get("page")
            size_obj = ex_dict.get("page_size")
            examples_parsed.append(
                ExampleSpec(
                    name=name,
                    description=_get_str(ex_dict, "description"),
                    params=params,
                    page=page_obj
                    if isinstance(page_obj, int) and not isinstance(page_obj, bool)
                    else None,
                    page_size=(
                        size_obj
                        if isinstance(size_obj, int) and not isinstance(size_obj, bool)
                        else None
                    ),
                    format=_get_str(ex_dict, "format"),
                )
            )

    assert endpoint is not None  # noqa: S101 — 위 검증 통과 시 항상 존재
    assert auth is not None  # noqa: S101
    assert response is not None  # noqa: S101
    assert pagination is not None  # noqa: S101

    return SpecDefinition(
        id=spec_id or "",
        provider=provider or "",
        title=title or "",
        endpoint=endpoint,
        auth=auth,
        response=response,
        pagination=pagination,
        status=status,
        description=_get_str(data, "description"),
        source=SourceRef(
            url=_get_str(source_raw, "url"),
            doc_version=_get_str(source_raw, "doc_version"),
            verified_at=_parse_date(source_raw.get("verified_at"), problems, "source.verified_at"),
        ),
        params=_parse_params(data.get("params"), problems),
        fields=tuple(fields_parsed),
        examples=tuple(examples_parsed),
        last_verified=_parse_date(data.get("last_verified"), problems, "last_verified"),
        raw_metadata=dict(data),
    )


def load_spec_file(path: Path) -> SpecDefinition:
    """YAML spec 파일을 읽어 검증된 SpecDefinition으로 변환한다."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        msg = f"spec YAML 파싱 실패: {path}"
        raise InvalidRequestError(msg) from exc
    if not isinstance(data, dict):
        msg = f"spec 루트는 매핑이어야 합니다: {path}"
        raise InvalidRequestError(msg)
    return from_mapping(data)


def _default_specs_dir() -> Path:
    """패키지에 번들된 specs 디렉터리 경로를 반환한다.

    파일시스템 기반 배포(site-packages·dev 체크아웃·wheel 설치)를 가정한다.
    zipimport로 직접 로드되는 특수 환경은 지원하지 않는다(정직한 제약).
    """
    base = resources.files("kpubdata")
    return Path(str(base)) / "specs"


def _iter_yaml_files(root: Path) -> list[Path]:
    """디렉터리를 재귀 순회하며 *.yaml/*.yml 파일을 정렬된 목록으로 반환한다."""
    files = [*root.rglob("*.yaml"), *root.rglob("*.yml")]
    return sorted(files)


def discover_specs(root: Path | None = None) -> list[SpecDefinition]:
    """specs 디렉터리의 모든 spec을 로드한다.

    ``root``를 주지 않으면 패키지 내 ``kpubdata/specs/``를 탐색한다.
    schema.json은 YAML이 아니므로 자연히 제외된다.
    """
    target = _default_specs_dir() if root is None else root
    if not target.is_dir():
        return []
    return [load_spec_file(path) for path in _iter_yaml_files(target)]


def spec_index(root: Path | None = None) -> dict[str, SpecDefinition]:
    """id → SpecDefinition 사전을 반환한다."""
    return {spec.id: spec for spec in discover_specs(root)}


def find_spec(
    dataset_key: str, provider: str | None = None, root: Path | None = None
) -> SpecDefinition | None:
    """ "provider.key" 또는 bare key로 spec을 찾는다(없으면 None)."""
    for spec in discover_specs(root):
        if spec.id == dataset_key:
            return spec
        bare_key_match = "." not in dataset_key and spec.dataset_key == dataset_key
        if bare_key_match and (provider is None or spec.provider == provider):
            return spec
    return None


def _sorted(values: frozenset[str]) -> str:
    """enum 집합을 사람이 읽는 선택지 문자열로 만든다."""
    return "|".join(sorted(values))


__all__ = [
    "AuthSpec",
    "EndpointSpec",
    "ErrorSpec",
    "ExampleSpec",
    "FieldSpec",
    "FormatParamSpec",
    "PaginationSpec",
    "ParamSpec",
    "ResponseSpec",
    "SourceRef",
    "SpecDefinition",
    "discover_specs",
    "find_spec",
    "from_mapping",
    "load_spec_file",
    "spec_index",
]
