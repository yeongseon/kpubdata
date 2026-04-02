"""Core canonical models and capability metadata for KPubData."""

from __future__ import annotations

from kpubdata.core.capability import Operation, PaginationMode, QuerySupport
from kpubdata.core.models import (
    DatasetRef,
    FieldDescriptor,
    Query,
    RecordBatch,
    SchemaDescriptor,
)
from kpubdata.core.representation import Representation

__all__ = [
    "DatasetRef",
    "FieldDescriptor",
    "Operation",
    "PaginationMode",
    "Query",
    "QuerySupport",
    "RecordBatch",
    "Representation",
    "SchemaDescriptor",
]
