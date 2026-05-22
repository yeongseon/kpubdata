"""KPubData의 핵심 정규 모델과 capability 메타데이터."""

from __future__ import annotations

from kpubdata.core.capability import Operation, PaginationMode, QuerySupport
from kpubdata.core.models import (
    DatasetRef,
    FieldConstraints,
    FieldDescriptor,
    Query,
    RecordBatch,
    SchemaDescriptor,
)
from kpubdata.core.representation import Representation

__all__ = [
    "DatasetRef",
    "FieldConstraints",
    "FieldDescriptor",
    "Operation",
    "PaginationMode",
    "Query",
    "QuerySupport",
    "RecordBatch",
    "Representation",
    "SchemaDescriptor",
]
