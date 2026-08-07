"""Provider와 어댑터 전반에서 공유되는 정규 도메인 모델."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import field
from importlib import import_module
from types import MappingProxyType

from kpubdata.core.capability import Operation, QuerySupport, _dataclass
from kpubdata.core.representation import Representation
from kpubdata.exceptions import InvalidRequestError


def _empty_proxy() -> MappingProxyType[str, object]:
    """비어 있는 불변 문자열 키 매핑 프록시를 반환한다."""
    return MappingProxyType({})


def _empty_object_proxy() -> MappingProxyType[str, object]:
    """비어 있는 불변 객체 값 매핑 프록시를 반환한다."""
    return MappingProxyType({})


@_dataclass(slots=True, frozen=True)
class DatasetRef:
    """Provider 데이터셋에 대한 정규 불변 참조.

    속성:
        description: 이 데이터셋이 제공하는 내용을 사람이 읽기 쉽게 설명한 문자열.
        tags: 탐색용 분류 태그(예: ``("weather", "forecast")``).
        source_url: 원본 API 문서 또는 데이터 포털 페이지의 URL.
        query_support: 알려진 경우 구조화된 목록 질의 기능 메타데이터.
        raw_metadata: 디버깅을 위한 Provider 고유 탐색 메타데이터.
    """

    id: str
    provider: str
    dataset_key: str
    name: str
    representation: Representation
    operations: frozenset[Operation] = frozenset()
    query_support: QuerySupport | None = None
    raw_metadata: MappingProxyType[str, object] = field(default_factory=_empty_proxy)
    description: str | None = None
    tags: tuple[str, ...] = ()
    source_url: str | None = None

    def supports(self, op: Operation) -> bool:
        """이 데이터셋이 요청된 작업을 지원하는지 반환한다."""

        return op in self.operations

    def __repr__(self) -> str:
        """개발자 친화적인 간결한 표현을 반환한다."""
        ops = ", ".join(sorted(operation.value for operation in self.operations))
        return f"DatasetRef(id={self.id!r}, provider={self.provider!r}, ops=[{ops}])"


@_dataclass(slots=True)
class Query:
    """레코드 목록 조회를 위한 Provider 비종속 질의 객체.

    속성:
        filters: 질의 변환에 병합되는 Provider별 필터 페이로드.
        extra: 정규 필드로 포괄되지 않는 추가 Provider 고유 파라미터.
    """

    filters: dict[str, object] = field(default_factory=dict)
    page: int | None = None
    page_size: int | None = None
    cursor: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    fields: list[str] | None = None
    sort: list[str] | None = None
    extra: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Query 생성 시 canonical-level 타입 검증을 수행한다."""
        self._validate_page()
        self._validate_page_size()
        self._validate_cursor()
        self._validate_dates()
        self._validate_fields()
        self._validate_sort()
        self._validate_dict_type(self.filters, "filters")
        self._validate_dict_type(self.extra, "extra")

    def _validate_page(self) -> None:
        """page 필드가 유효한 정수인지 검증한다."""
        if self.page is None:
            return
        if isinstance(self.page, bool):
            raise InvalidRequestError("page must be an integer, not bool")
        if not isinstance(self.page, int):
            raise InvalidRequestError(
                f"page must be an integer or None, got {type(self.page).__name__}"
            )
        if self.page < 1:
            raise InvalidRequestError("page must be a positive integer (>= 1)")

    def _validate_page_size(self) -> None:
        """page_size 필드가 유효한 정수인지 검증한다."""
        if self.page_size is None:
            return
        if isinstance(self.page_size, bool):
            raise InvalidRequestError("page_size must be an integer, not bool")
        if not isinstance(self.page_size, int):
            raise InvalidRequestError(
                f"page_size must be an integer or None, got {type(self.page_size).__name__}"
            )
        if self.page_size < 1:
            raise InvalidRequestError("page_size must be a positive integer (>= 1)")

    def _validate_cursor(self) -> None:
        """cursor 필드가 문자열인지 검증한다."""
        if self.cursor is None:
            return
        if not isinstance(self.cursor, str):
            raise InvalidRequestError(
                f"cursor must be a string or None, got {type(self.cursor).__name__}"
            )
        if self.cursor == "":
            raise InvalidRequestError("cursor must be a non-empty string")

    def _validate_dates(self) -> None:
        """날짜 필드가 문자열이고 비어있지 않은지 검증한다."""
        for field_name, value in (("start_date", self.start_date), ("end_date", self.end_date)):
            if value is None:
                continue
            if not isinstance(value, str):
                raise InvalidRequestError(
                    f"{field_name} must be a string or None, got {type(value).__name__}"
                )
            if value == "" or value.isspace():
                raise InvalidRequestError(f"{field_name} must be a non-empty string")

    def _validate_fields(self) -> None:
        """fields 필드가 문자열 리스트인지 검증한다."""
        if self.fields is None:
            return
        if not isinstance(self.fields, list):
            raise InvalidRequestError(
                f"fields must be a list of strings or None, got {type(self.fields).__name__}"
            )
        for i, item in enumerate(self.fields):
            if not isinstance(item, str):
                raise InvalidRequestError(
                    f"fields must contain only strings, got {type(item).__name__} at index {i}"
                )

    def _validate_sort(self) -> None:
        """sort 필드가 문자열 리스트인지 검증한다."""
        if self.sort is None:
            return
        if not isinstance(self.sort, list):
            raise InvalidRequestError(
                f"sort must be a list of strings or None, got {type(self.sort).__name__}"
            )
        for i, item in enumerate(self.sort):
            if not isinstance(item, str):
                raise InvalidRequestError(
                    f"sort must contain only strings, got {type(item).__name__} at index {i}"
                )

    def _validate_dict_type(self, value: dict[str, object], field_name: str) -> None:
        """dict 필드의 키가 문자열인지 검증한다."""
        if not isinstance(value, dict):
            raise InvalidRequestError(f"{field_name} must be a dict, got {type(value).__name__}")
        for key in value:
            if not isinstance(key, str):
                raise InvalidRequestError(
                    f"{field_name} keys must be strings, got {type(key).__name__}"
                )


@_dataclass(slots=True)
class RecordBatch:
    """데이터셋 질의에서 반환된 정규화 레코드 배치.

    속성:
        next_page: 오프셋 페이지네이션을 위한 다음 페이지 번호.
        next_cursor: 커서 페이지네이션을 위한 불투명 커서 토큰.
        raw: 이 배치를 도출하는 데 사용한 Provider 고유 응답 페이로드.
        meta: 정규 필드에 맞지 않는 추가 어댑터 메타데이터.
    """

    items: list[dict[str, object]]
    dataset: DatasetRef
    total_count: int | None = None
    next_page: int | None = None
    next_cursor: str | None = None
    raw: object | None = None
    meta: dict[str, object] = field(default_factory=dict)

    def __len__(self) -> int:
        """배치에 담긴 레코드 수를 반환한다."""
        return len(self.items)

    def __iter__(self) -> Iterator[dict[str, object]]:
        """배치의 레코드를 순회하는 이터레이터를 반환한다."""
        return iter(self.items)

    def __bool__(self) -> bool:
        """배치에 레코드가 하나라도 있으면 True를 반환한다."""
        return bool(self.items)

    def to_pandas(self) -> object:
        """items를 pandas ``DataFrame``으로 변환한다."""
        try:
            pd = import_module("pandas")
        except ImportError:
            raise ImportError(
                "pandas is required for to_pandas(). Install with: pip install kpubdata[pandas]"
            ) from None
        return pd.DataFrame(self.items)


@_dataclass(slots=True)
class FieldConstraints:
    """데이터셋 필드의 구조화된 제약 조건.

    모든 속성은 선택 사항이다. Provider 카탈로그가 실제로 선언한 값만 채운다.

    속성:
        max_length: 최대 문자 길이(문자열 필드).
        min_value: 최소 숫자 값(숫자 필드).
        max_value: 최대 숫자 값(숫자 필드).
        pattern: 값이 일치해야 하는 정규식 패턴(예: ``"^\\\\d{6}$"``).
        allowed_values: 허용되는 값의 닫힌 집합.
        format: 의미론적 형식 힌트(예: ``"YYYYMM"``, ``"date"``, ``"url"``).
    """

    max_length: int | None = None
    min_value: float | None = None
    max_value: float | None = None
    pattern: str | None = None
    allowed_values: tuple[str, ...] | None = None
    format: str | None = None


@_dataclass(slots=True)
class FieldDescriptor:
    """데이터셋 스키마의 단일 필드를 설명한다.

    속성:
        constraints: 필드에 대한 선택적 구조화 제약 조건.
        raw: 고급 사용을 위해 보존한 Provider 고유 필드 메타데이터.
    """

    name: str
    title: str | None = None
    type: str | None = None
    description: str | None = None
    nullable: bool | None = None
    raw: MappingProxyType[str, object] = field(default_factory=_empty_object_proxy)
    constraints: FieldConstraints | None = None


@_dataclass(slots=True)
class SchemaDescriptor:
    """데이터셋에 대해 노출되는 스키마 메타데이터를 설명한다.

    속성:
        raw: 정규화하지 않고 보존한 Provider 고유 스키마 메타데이터.
    """

    dataset: DatasetRef
    fields: list[FieldDescriptor]
    raw: MappingProxyType[str, object] = field(default_factory=_empty_object_proxy)


__all__ = [
    "DatasetRef",
    "FieldConstraints",
    "FieldDescriptor",
    "Query",
    "RecordBatch",
    "SchemaDescriptor",
]
