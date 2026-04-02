"""Canonical domain models shared across providers and adapters."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass as _stdlib_dataclass
from dataclasses import field
from types import MappingProxyType
from typing import Any, TypeVar

from typing_extensions import dataclass_transform

from kpubdata.core.capability import Operation, QuerySupport
from kpubdata.core.representation import Representation

_T = TypeVar("_T")


@dataclass_transform()
def _dataclass(
    *,
    slots: bool = False,
    frozen: bool = False,
) -> Callable[[type[_T]], type[_T]]:
    def _decorate(cls: type[_T]) -> type[_T]:
        return _stdlib_dataclass(slots=slots, frozen=frozen)(cls)  # pyright: ignore[reportCallIssue]

    return _decorate


def _empty_proxy() -> MappingProxyType[str, Any]:
    return MappingProxyType({})


def _empty_object_proxy() -> MappingProxyType[str, object]:
    return MappingProxyType({})


@_dataclass(slots=True, frozen=True)
class DatasetRef:
    """Canonical immutable reference to a provider dataset.

    Attributes:
        query_support: Structured list-query feature metadata, if known.
        raw_metadata: Provider-native discovery metadata for debugging.
    """

    id: str
    provider: str
    dataset_key: str
    name: str
    representation: Representation
    operations: frozenset[Operation] = frozenset()
    query_support: QuerySupport | None = None
    raw_metadata: MappingProxyType[str, Any] = field(default_factory=_empty_proxy)

    def supports(self, op: Operation) -> bool:
        """Return whether this dataset supports the requested operation."""

        return op in self.operations

    def __repr__(self) -> str:
        ops = ", ".join(sorted(operation.value for operation in self.operations))
        return f"DatasetRef(id={self.id!r}, provider={self.provider!r}, ops=[{ops}])"


@_dataclass(slots=True)
class Query:
    """Provider-agnostic query object for listing records.

    Attributes:
        filters: Provider-specific filter payload merged into query translation.
        extra: Additional provider-native parameters not covered canonically.
    """

    filters: dict[str, Any] = field(default_factory=dict)
    page: int | None = None
    page_size: int | None = None
    cursor: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    fields: list[str] | None = None
    sort: list[str] | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@_dataclass(slots=True)
class RecordBatch:
    """Batch of normalized records returned from a dataset query.

    Attributes:
        next_page: Next offset page number for offset pagination.
        next_cursor: Opaque cursor token for cursor pagination.
        raw: Provider-native response payload used to derive this batch.
        meta: Additional adapter metadata that does not fit canonical fields.
    """

    items: list[dict[str, Any]]
    dataset: DatasetRef
    total_count: int | None = None
    next_page: int | None = None
    next_cursor: str | None = None
    raw: Any | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(self.items)

    def __bool__(self) -> bool:
        return bool(self.items)


@_dataclass(slots=True)
class FieldDescriptor:
    """Describe a single field in a dataset schema.

    Attributes:
        raw: Provider-native field metadata retained for advanced use.
    """

    name: str
    title: str | None = None
    type: str | None = None
    description: str | None = None
    nullable: bool | None = None
    raw: MappingProxyType[str, object] = field(default_factory=_empty_object_proxy)


@_dataclass(slots=True)
class SchemaDescriptor:
    """Describe schema metadata exposed for a dataset.

    Attributes:
        raw: Provider-native schema metadata retained without normalization.
    """

    dataset: DatasetRef
    fields: list[FieldDescriptor]
    raw: MappingProxyType[str, object] = field(default_factory=_empty_object_proxy)


__all__ = [
    "DatasetRef",
    "FieldDescriptor",
    "Query",
    "RecordBatch",
    "SchemaDescriptor",
]
