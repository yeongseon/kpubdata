"""Shared catalogue and schema utilities for provider adapters."""

from __future__ import annotations

import json
from collections.abc import Mapping
from importlib.resources import files
from types import MappingProxyType
from typing import cast

from kpubdata.core.capability import Operation, PaginationMode, QuerySupport
from kpubdata.core.models import (
    DatasetRef,
    FieldDescriptor,
    SchemaDescriptor,
)
from kpubdata.core.representation import Representation


def load_catalogue(package_name: str, provider: str) -> tuple[DatasetRef, ...]:
    """Load and parse a catalogue.json from a provider package."""
    package_files = files(package_name)
    catalogue_text = package_files.joinpath("catalogue.json").read_text(encoding="utf-8")
    parsed_catalogue = cast(object, json.loads(catalogue_text))
    if not isinstance(parsed_catalogue, list):
        msg = f"{provider} catalogue.json must contain a top-level JSON array"
        raise ValueError(msg)

    catalogue_entries = cast(list[object], parsed_catalogue)
    datasets: list[DatasetRef] = []
    for entry_object in catalogue_entries:
        if not isinstance(entry_object, dict):
            msg = f"{provider} catalogue entries must be JSON objects"
            raise ValueError(msg)
        typed_entry_object = cast(dict[object, object], entry_object)
        entry: dict[str, object] = {}
        for key, value in typed_entry_object.items():
            if not isinstance(key, str):
                msg = f"{provider} catalogue entry keys must be strings"
                raise ValueError(msg)
            entry[key] = value
        datasets.append(build_dataset_ref(provider, entry))
    return tuple(datasets)


def build_dataset_ref(provider: str, entry: dict[str, object]) -> DatasetRef:
    """Build a DatasetRef from a raw catalogue entry dict."""
    dataset_key = require_string_field(entry, "dataset_key", provider)
    name = require_string_field(entry, "name", provider)
    representation_value = require_string_field(entry, "representation", provider)
    representation = Representation(representation_value)

    ops_raw_obj = entry.get("operations", [])
    ops_raw = ops_raw_obj if isinstance(ops_raw_obj, list) else []
    valid_ops = {member.value for member in Operation}
    operations = frozenset(
        Operation(op) for op in ops_raw if isinstance(op, str) and op in valid_ops
    )

    query_support = _parse_query_support(entry, provider)

    raw_metadata = MappingProxyType(
        {
            key: value
            for key, value in entry.items()
            if key not in ("dataset_key", "name", "representation", "operations", "query_support")
        }
    )

    return DatasetRef(
        id=f"{provider}.{dataset_key}",
        provider=provider,
        dataset_key=dataset_key,
        name=name,
        representation=representation,
        operations=operations,
        query_support=query_support,
        raw_metadata=raw_metadata,
    )


def _parse_query_support(entry: dict[str, object], provider: str) -> QuerySupport | None:
    """Parse query_support from a catalogue entry."""
    qs_raw_obj = entry.get("query_support")
    if not isinstance(qs_raw_obj, dict):
        return None

    qs_raw = cast(dict[str, object], qs_raw_obj)
    pagination_raw = qs_raw.get("pagination", "none")
    valid_pagination = {member.value for member in PaginationMode}
    pagination = (
        PaginationMode(pagination_raw)
        if isinstance(pagination_raw, str) and pagination_raw in valid_pagination
        else PaginationMode.NONE
    )

    max_page_size = None
    if "max_page_size" in qs_raw:
        max_page_size_raw = qs_raw["max_page_size"]
        if isinstance(max_page_size_raw, int):
            max_page_size = max_page_size_raw
        elif isinstance(max_page_size_raw, str):
            max_page_size = int(max_page_size_raw)
        else:
            msg = f"{provider} query_support.max_page_size must be int-like"
            raise ValueError(msg)

    return QuerySupport(pagination=pagination, max_page_size=max_page_size)


def build_schema_from_metadata(dataset: DatasetRef) -> SchemaDescriptor | None:
    """Build SchemaDescriptor from catalogue metadata fields."""
    fields_raw = dataset.raw_metadata.get("fields")
    if not isinstance(fields_raw, list) or not fields_raw:
        return None

    entries = cast(list[object], fields_raw)
    field_descriptors: list[FieldDescriptor] = []
    for entry_obj in entries:
        if not isinstance(entry_obj, dict):
            continue
        entry = cast(dict[str, object], entry_obj)
        name_raw = entry.get("name")
        if not isinstance(name_raw, str) or not name_raw:
            continue
        title_raw = entry.get("title")
        type_raw = entry.get("type")
        desc_raw = entry.get("description")
        nullable_raw = entry.get("nullable")
        field_descriptors.append(
            FieldDescriptor(
                name=name_raw,
                title=title_raw if isinstance(title_raw, str) else None,
                type=type_raw if isinstance(type_raw, str) else None,
                description=desc_raw if isinstance(desc_raw, str) else None,
                nullable=nullable_raw if isinstance(nullable_raw, bool) else None,
                raw=MappingProxyType({k: v for k, v in entry.items() if k != "name"}),
            )
        )

    if not field_descriptors:
        return None

    return SchemaDescriptor(
        dataset=dataset,
        fields=field_descriptors,
        raw=MappingProxyType({"source": "catalogue"}),
    )


def coerce_int(value: object, default: int) -> int:
    """Coerce a value to int, returning default on failure."""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


def require_string_field(entry: Mapping[str, object], field_name: str, provider: str) -> str:
    """Extract a required non-empty string field from a catalogue entry."""
    value = entry.get(field_name)
    if isinstance(value, str) and value:
        return value
    raise ValueError(f"{provider} catalogue entry missing non-empty string field: {field_name}")


__all__ = [
    "build_dataset_ref",
    "build_schema_from_metadata",
    "coerce_int",
    "load_catalogue",
    "require_string_field",
]
