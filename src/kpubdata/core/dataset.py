"""Bound Dataset — the user-facing object for dataset operations."""

from __future__ import annotations

from collections.abc import Generator
from typing import cast

from typing_extensions import override

from kpubdata.core.capability import Operation
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.exceptions import UnsupportedCapabilityError

_CANONICAL_QUERY_KEYS = frozenset(
    {"page", "page_size", "cursor", "start_date", "end_date", "fields", "sort"}
)


class Dataset:
    """Bound dataset that routes operations to a provider adapter."""

    def __init__(self, ref: DatasetRef, adapter: ProviderAdapter) -> None:
        """Initialize a dataset bound to its canonical ref and adapter."""

        self._ref: DatasetRef = ref
        self._adapter: ProviderAdapter = adapter

    @property
    def ref(self) -> DatasetRef:
        """Return immutable canonical dataset reference."""

        return self._ref

    @property
    def id(self) -> str:
        """Return canonical dataset identifier."""

        return self._ref.id

    @property
    def name(self) -> str:
        """Return human-readable dataset name."""

        return self._ref.name

    @property
    def provider(self) -> str:
        """Return provider identifier serving this dataset."""

        return self._ref.provider

    @property
    def operations(self) -> frozenset[Operation]:
        """Return declared operation capabilities for this dataset."""

        return self._ref.operations

    def list(self, **kwargs: object) -> RecordBatch:
        """Query records from this dataset using canonical list semantics.

        Canonical query parameters (``page``, ``page_size``, ``cursor``,
        ``start_date``, ``end_date``, ``fields``, ``sort``) are extracted
        into the corresponding ``Query`` fields.  Remaining kwargs are
        passed as provider-specific ``filters``.

        Raises:
            UnsupportedCapabilityError: If this dataset does not support ``list``.
        """

        if Operation.LIST not in self._ref.operations:
            raise UnsupportedCapabilityError(
                f"Dataset does not support list: {self._ref.id}",
                provider=self._ref.provider,
                dataset_id=self._ref.id,
                operation=Operation.LIST.value,
            )

        page: int | None = None
        page_size: int | None = None
        cursor: str | None = None
        start_date: str | None = None
        end_date: str | None = None
        fields_list: list[str] | None = None
        sort_list: list[str] | None = None
        filters: dict[str, object] = {}

        for key, value in kwargs.items():
            if key == "page" and isinstance(value, int):
                page = value
            elif key == "page_size" and isinstance(value, int):
                page_size = value
            elif key == "cursor" and isinstance(value, str):
                cursor = value
            elif key == "start_date" and isinstance(value, str):
                start_date = value
            elif key == "end_date" and isinstance(value, str):
                end_date = value
            elif (
                key == "fields"
                and isinstance(value, list)
                and all(isinstance(item, str) for item in cast(list[object], value))
            ):
                fields_list = cast(list[str], value)
            elif (
                key == "sort"
                and isinstance(value, list)
                and all(isinstance(item, str) for item in cast(list[object], value))
            ):
                sort_list = cast(list[str], value)
            else:
                filters[key] = value

        query = Query(
            filters=filters,
            page=page,
            page_size=page_size,
            cursor=cursor,
            start_date=start_date,
            end_date=end_date,
            fields=fields_list,
            sort=sort_list,
        )
        return self._adapter.query_records(self._ref, query)

    def list_all(self, **kwargs: object) -> Generator[RecordBatch, None, None]:
        if Operation.LIST not in self._ref.operations:
            raise UnsupportedCapabilityError(
                f"Dataset does not support list: {self._ref.id}",
                provider=self._ref.provider,
                dataset_id=self._ref.id,
                operation=Operation.LIST.value,
            )

        page_kwargs = dict(kwargs)
        batch = self.list(**page_kwargs)
        yield batch
        while batch.next_page is not None:
            page_kwargs["page"] = batch.next_page
            batch = self.list(**page_kwargs)
            yield batch

    def get(self, **key: object) -> dict[str, object] | None:
        """Return a single record matching the provided key fields.

        Return ``None`` when no matching record is found.

        Raises:
            UnsupportedCapabilityError: If this dataset does not support ``get``.
        """

        if Operation.GET not in self._ref.operations:
            raise UnsupportedCapabilityError(
                f"Dataset does not support get: {self._ref.id}",
                provider=self._ref.provider,
                dataset_id=self._ref.id,
                operation=Operation.GET.value,
            )
        key_payload: dict[str, object] = {k: v for k, v in key.items()}
        return self._adapter.get_record(self._ref, key_payload)

    def schema(self) -> SchemaDescriptor | None:
        """Return canonical schema metadata when the provider exposes it."""

        return self._adapter.get_schema(self._ref)

    def call_raw(self, operation: str, **params: object) -> object:
        """Execute a provider-native operation without canonical normalization.

        Use this escape hatch for provider features not represented in the
        canonical model.
        """

        payload: dict[str, object] = {k: v for k, v in params.items()}
        return self._adapter.call_raw(self._ref, operation, payload)

    @override
    def __repr__(self) -> str:
        """Return concise debug representation."""

        return f"Dataset({self._ref.id!r})"


__all__ = ["Dataset"]
