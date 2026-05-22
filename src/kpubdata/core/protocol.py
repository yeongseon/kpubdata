"""Provider 어댑터 프로토콜 — KPubData의 확장 지점."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor


@runtime_checkable
class ProviderAdapter(Protocol):
    """모든 Provider 어댑터가 만족해야 하는 프로토콜.

    어댑터는 인증, 탐색, 변환, 오류 매핑, raw 접근,
    그리고 정직한 capability 선언을 책임진다.
    """

    requires_api_key: bool

    @property
    def name(self) -> str:
        """Provider 식별자(예: ``datago`` 또는 ``seoul``)를 반환한다."""

        ...

    def list_datasets(self) -> list[DatasetRef]:
        """이 Provider에서 탐색 가능한 데이터셋을 반환한다."""

        ...

    def search_datasets(self, text: str) -> list[DatasetRef]:
        """이 Provider에서 자유 텍스트 검색과 일치하는 데이터셋을 반환한다."""

        ...

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        """Provider 로컬 데이터셋 키를 정규 데이터셋 참조로 해석한다."""

        ...

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        """데이터셋에 대한 정규 목록/질의 요청을 실행한다."""

        ...

    def get_schema(self, dataset: DatasetRef) -> SchemaDescriptor | None:
        """지원되는 경우 정규 스키마 메타데이터를 반환한다."""

        ...

    def call_raw(self, dataset: DatasetRef, operation: str, params: dict[str, object]) -> object:
        """Provider 고유 작업을 실행하고 비정규화 응답을 반환한다."""

        ...


__all__ = ["ProviderAdapter"]
