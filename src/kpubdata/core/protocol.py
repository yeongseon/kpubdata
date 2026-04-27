"""Provider adapter protocol — the extension point for KPubData."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor


@runtime_checkable
class ProviderAdapter(Protocol):
    """Protocol that every provider adapter must satisfy.

    Adapters are responsible for auth, discovery, translation, error mapping,
    raw access, and truthful capability declaration.
    """

    requires_api_key: bool

    @property
    def name(self) -> str:
        """Return provider identifier (for example ``datago`` or ``seoul``)."""

        ...

    def list_datasets(self) -> list[DatasetRef]:
        """Return discoverable datasets for this provider."""

        ...

    def search_datasets(self, text: str) -> list[DatasetRef]:
        """Return datasets matching free-text search for this provider."""

        ...

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        """Resolve a provider-local dataset key to a canonical dataset ref."""

        ...

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        """Execute a canonical list/query request for a dataset."""

        ...

    def get_schema(self, dataset: DatasetRef) -> SchemaDescriptor | None:
        """Return canonical schema metadata if supported."""

        ...

    def call_raw(self, dataset: DatasetRef, operation: str, params: dict[str, object]) -> object:
        """Execute provider-native operation and return unnormalized response."""

        ...


__all__ = ["ProviderAdapter"]
