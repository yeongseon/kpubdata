"""Data.go.kr adapter stub."""

from __future__ import annotations

from ...core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor


class DataGoAdapter:
    """Adapter for data.go.kr (공공데이터포털)."""

    @property
    def name(self) -> str:
        """Return canonical provider key."""

        return "datago"

    def list_datasets(self) -> list[DatasetRef]:
        """List datasets available from data.go.kr."""

        raise NotImplementedError("TODO: implement datago list_datasets")

    def search_datasets(self, _text: str) -> list[DatasetRef]:
        """Search datasets available from data.go.kr."""

        raise NotImplementedError("TODO: implement datago search_datasets")

    def get_dataset(self, _dataset_key: str) -> DatasetRef:
        """Resolve provider-local dataset key for data.go.kr."""

        raise NotImplementedError("TODO: implement datago get_dataset")

    def query_records(self, _dataset: DatasetRef, _query: Query) -> RecordBatch:
        """Query records from a data.go.kr dataset."""

        raise NotImplementedError("TODO: implement datago query_records")

    def get_record(self, _dataset: DatasetRef, _key: dict[str, object]) -> dict[str, object] | None:
        """Get a single record from a data.go.kr dataset."""

        raise NotImplementedError("TODO: implement datago get_record")

    def get_schema(self, _dataset: DatasetRef) -> SchemaDescriptor | None:
        """Get schema metadata for a data.go.kr dataset."""

        raise NotImplementedError("TODO: implement datago get_schema")

    def call_raw(self, _dataset: DatasetRef, _operation: str, _params: dict[str, object]) -> object:
        """Call provider-native data.go.kr API operation."""

        raise NotImplementedError("TODO: implement datago call_raw")


__all__ = ["DataGoAdapter"]
