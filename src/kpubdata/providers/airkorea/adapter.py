"""AirKorea adapter stub."""

from __future__ import annotations

from ...core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor


class AirKoreaAdapter:
    """Adapter for 한국환경공단 에어코리아 (AirKorea)."""

    @property
    def name(self) -> str:
        """Return canonical provider key."""

        return "airkorea"

    def list_datasets(self) -> list[DatasetRef]:
        """List datasets available from AirKorea."""

        raise NotImplementedError("TODO: implement airkorea list_datasets")

    def search_datasets(self, _text: str) -> list[DatasetRef]:
        """Search datasets available from AirKorea."""

        raise NotImplementedError("TODO: implement airkorea search_datasets")

    def get_dataset(self, _dataset_key: str) -> DatasetRef:
        """Resolve provider-local dataset key for AirKorea."""

        raise NotImplementedError("TODO: implement airkorea get_dataset")

    def query_records(self, _dataset: DatasetRef, _query: Query) -> RecordBatch:
        """Query records from an AirKorea dataset."""

        raise NotImplementedError("TODO: implement airkorea query_records")

    def get_record(self, _dataset: DatasetRef, _key: dict[str, object]) -> dict[str, object] | None:
        """Get a single record from an AirKorea dataset."""

        raise NotImplementedError("TODO: implement airkorea get_record")

    def get_schema(self, _dataset: DatasetRef) -> SchemaDescriptor | None:
        """Get schema metadata for an AirKorea dataset."""

        raise NotImplementedError("TODO: implement airkorea get_schema")

    def call_raw(self, _dataset: DatasetRef, _operation: str, _params: dict[str, object]) -> object:
        """Call provider-native AirKorea API operation."""

        raise NotImplementedError("TODO: implement airkorea call_raw")


__all__ = ["AirKoreaAdapter"]
