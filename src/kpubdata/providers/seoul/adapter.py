"""Seoul Open Data adapter stub."""

from __future__ import annotations

from ...core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor


class SeoulAdapter:
    """Adapter for 서울열린데이터광장 (Seoul Open Data Plaza)."""

    @property
    def name(self) -> str:
        """Return canonical provider key."""

        return "seoul"

    def list_datasets(self) -> list[DatasetRef]:
        """List datasets available from Seoul Open Data."""

        raise NotImplementedError("TODO: implement seoul list_datasets")

    def search_datasets(self, _text: str) -> list[DatasetRef]:
        """Search datasets available from Seoul Open Data."""

        raise NotImplementedError("TODO: implement seoul search_datasets")

    def get_dataset(self, _dataset_key: str) -> DatasetRef:
        """Resolve provider-local dataset key for Seoul Open Data."""

        raise NotImplementedError("TODO: implement seoul get_dataset")

    def query_records(self, _dataset: DatasetRef, _query: Query) -> RecordBatch:
        """Query records from a Seoul Open Data dataset."""

        raise NotImplementedError("TODO: implement seoul query_records")

    def get_record(self, _dataset: DatasetRef, _key: dict[str, object]) -> dict[str, object] | None:
        """Get a single record from a Seoul Open Data dataset."""

        raise NotImplementedError("TODO: implement seoul get_record")

    def get_schema(self, _dataset: DatasetRef) -> SchemaDescriptor | None:
        """Get schema metadata for a Seoul Open Data dataset."""

        raise NotImplementedError("TODO: implement seoul get_schema")

    def call_raw(self, _dataset: DatasetRef, _operation: str, _params: dict[str, object]) -> object:
        """Call provider-native Seoul Open Data API operation."""

        raise NotImplementedError("TODO: implement seoul call_raw")


__all__ = ["SeoulAdapter"]
