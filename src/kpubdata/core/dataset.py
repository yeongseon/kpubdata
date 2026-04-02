"""Bound Dataset — the user-facing object for dataset operations."""

from __future__ import annotations

from typing import Any

from kpubdata.core.capability import Operation
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.exceptions import UnsupportedCapabilityError
from kpubdata.transport.http import HttpTransport


class Dataset:
    """Bound dataset that routes operations to a provider adapter."""

    def __init__(self, ref: DatasetRef, adapter: ProviderAdapter, transport: HttpTransport) -> None:
        """Initialize a dataset bound to its canonical ref and adapter."""

        self._ref = ref
        self._adapter = adapter
        self._transport = transport

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

    def list(self, **filters: Any) -> RecordBatch:
        """Query records from this dataset using canonical list semantics.

        Pass provider-specific query parameters as keyword arguments.

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
        query = Query(filters=filters)
        return self._adapter.query_records(self._ref, query)

    def get(self, **key: Any) -> dict[str, object] | None:
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

    def call_raw(self, operation: str, **params: Any) -> object:
        """Execute a provider-native operation without canonical normalization.

        Use this escape hatch for provider features not represented in the
        canonical model.
        """

        payload: dict[str, object] = {k: v for k, v in params.items()}
        return self._adapter.call_raw(self._ref, operation, payload)

    def __repr__(self) -> str:
        """Return concise debug representation."""

        return f"Dataset({self._ref.id!r})"


__all__ = ["Dataset"]
