"""데이터셋 작업과 질의 지원을 설명하는 capability 메타데이터."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass as _stdlib_dataclass
from enum import Enum
from typing import TypeVar

from typing_extensions import dataclass_transform

_T = TypeVar("_T")


@dataclass_transform()
def _dataclass(
    *,
    slots: bool = False,
    frozen: bool = False,
) -> Callable[[type[_T]], type[_T]]:
    """
    내부 헬퍼로서 dataclass 처리를 담당한다.

    매개변수:
        slots (bool): 호출자가 제공하는 입력 값이다.
        frozen (bool): 호출자가 제공하는 입력 값이다.

    반환값:
        Callable[[type[_T]], type[_T]]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    def _decorate(cls: type[_T]) -> type[_T]:
        """
        내부 헬퍼로서 decorate 처리를 담당한다.

        반환값:
            type[_T]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return _stdlib_dataclass(slots=slots, frozen=frozen)(cls)

    return _decorate


class Operation(str, Enum):
    """데이터셋이 지원할 수 있는 주요 작업."""

    LIST = "list"
    GET = "get"
    SCHEMA = "schema"
    RAW = "raw"
    DOWNLOAD = "download"


class PaginationMode(str, Enum):
    """데이터셋이 페이지네이션을 지원하는 방식."""

    OFFSET = "offset"
    INDEX = "index"
    CURSOR = "cursor"
    NONE = "none"


@_dataclass(slots=True, frozen=True)
class QuerySupport:
    """데이터셋이 지원하는 목록 질의 기능에 대한 구조화된 메타데이터."""

    pagination: PaginationMode = PaginationMode.NONE
    filterable_fields: frozenset[str] = frozenset()
    sortable_fields: frozenset[str] = frozenset()
    time_range: bool = False
    max_page_size: int | None = None


__all__ = ["Operation", "PaginationMode", "QuerySupport"]
