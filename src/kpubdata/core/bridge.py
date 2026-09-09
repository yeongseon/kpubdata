"""Composite Provider 브릿지 — 기존 어댑터와 spec 실행기를 한 Provider로 병합한다.

spec 시스템(#378)의 통합 계층이다. 같은 Provider 이름으로 등록된 두 세계
(카탈로그 기반 내장 어댑터 / 선언적 spec 실행기)를 하나의
``ProviderAdapter`` 표면으로 합친다.

병합 규칙:
- 같은 ``dataset_key``가 양쪽에 있으면 **spec이 이긴다**(컷오버 진행 중 해당
  데이터셋의 단일 진실 원천이 spec이 된다).
- spec 전용 키는 목록 끝에 추가한다.
- 카탈로그 전용 키는 기존 어댑터가 그대로 담당한다(공존).

컷오버가 완료된 Provider는 카탈로그 항목 제거 후 이 브릿지만 남게 된다.
"""

from __future__ import annotations

import logging

from kpubdata.core.executor import SpecDatasetAdapter
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.core.protocol import ProviderAdapter

logger = logging.getLogger("kpubdata.core.bridge")


class CompositeProviderAdapter:
    """내장 어댑터와 spec 어댑터를 spec-우선으로 병합한 Provider 어댑터."""

    def __init__(self, inner: ProviderAdapter, spec_adapter: SpecDatasetAdapter) -> None:
        """두 어댑터를 받아 병합 어댑터를 초기화한다.

        예외:
            ValueError: 두 어댑터의 Provider 이름이 다른 경우.
        """
        if inner.name != spec_adapter.name:
            msg = (
                f"CompositeProviderAdapter는 같은 Provider만 병합할 수 있습니다: "
                f"{inner.name!r} vs {spec_adapter.name!r}"
            )
            raise ValueError(msg)
        self._inner = inner
        self._spec = spec_adapter
        self.requires_api_key: bool = bool(
            getattr(inner, "requires_api_key", False) or spec_adapter.requires_api_key
        )

    @property
    def name(self) -> str:
        """Provider 식별자(두 어댑터가 공유)를 반환한다."""
        return self._inner.name

    def _spec_owns(self, dataset_key: str) -> bool:
        """해당 키가 spec 소유인지 반환한다."""
        try:
            self._spec.get_dataset(dataset_key)
        except Exception:
            return False
        return True

    def list_datasets(self) -> list[DatasetRef]:
        """카탈로그 + spec 데이터셋을 키 중복 없이 반환한다(spec 우선)."""
        spec_refs = {ref.dataset_key: ref for ref in self._spec.list_datasets()}
        merged: list[DatasetRef] = []
        seen: set[str] = set()
        for ref in self._inner.list_datasets():
            if ref.dataset_key in spec_refs:
                merged.append(spec_refs[ref.dataset_key])
                seen.add(ref.dataset_key)
            else:
                merged.append(ref)
        for key, ref in spec_refs.items():
            if key not in seen:
                merged.append(ref)
        return merged

    def search_datasets(self, text: str) -> list[DatasetRef]:
        """양쪽 검색 결과를 병합해 키 중복 없이 반환한다(spec 우선)."""
        spec_matches = {ref.dataset_key: ref for ref in self._spec.search_datasets(text)}
        merged: list[DatasetRef] = []
        seen: set[str] = set()
        for ref in self._inner.search_datasets(text):
            if ref.dataset_key in spec_matches:
                merged.append(spec_matches[ref.dataset_key])
                seen.add(ref.dataset_key)
            else:
                merged.append(ref)
        for key, ref in spec_matches.items():
            if key not in seen:
                merged.append(ref)
        return merged

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        """데이터셋 키를 해석한다(spec 우선, 없으면 내장 어댑터)."""
        if self._spec_owns(dataset_key):
            return self._spec.get_dataset(dataset_key)
        return self._inner.get_dataset(dataset_key)

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        """소유자에 따라 spec 실행기 또는 내장 어댑터로 질의를 위임한다."""
        if self._spec_owns(dataset.dataset_key):
            logger.debug(
                "Routing dataset query to spec executor",
                extra={"dataset_id": dataset.id, "provider": self.name},
            )
            return self._spec.query_records(dataset, query)
        return self._inner.query_records(dataset, query)

    def get_schema(self, dataset: DatasetRef) -> SchemaDescriptor | None:
        """소유자에 따라 스키마 메타데이터 조회를 위임한다."""
        if self._spec_owns(dataset.dataset_key):
            return self._spec.get_schema(dataset)
        return self._inner.get_schema(dataset)

    def call_raw(self, dataset: DatasetRef, operation: str, params: dict[str, object]) -> object:
        """소유자에 따라 raw 작업을 위임한다(비상구 보장)."""
        if self._spec_owns(dataset.dataset_key):
            return self._spec.call_raw(dataset, operation, params)
        return self._inner.call_raw(dataset, operation, params)

    @property
    def inner(self) -> ProviderAdapter:
        """래핑된 내장 어댑터를 반환한다(디버깅·테스트용)."""
        return self._inner

    @property
    def spec_adapter(self) -> SpecDatasetAdapter:
        """래핑된 spec 어댑터를 반환한다(디버깅·테스트용)."""
        return self._spec


__all__ = ["CompositeProviderAdapter"]
