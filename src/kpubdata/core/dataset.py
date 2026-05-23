"""바인딩된 Dataset — 데이터셋 작업을 위한 사용자 대상 객체."""

from __future__ import annotations

import logging
from collections.abc import Generator
from typing import cast

from typing_extensions import override

from kpubdata.core.capability import Operation
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.exceptions import UnsupportedCapabilityError

logger = logging.getLogger("kpubdata.dataset")

_CANONICAL_QUERY_KEYS = frozenset(
    {"page", "page_size", "cursor", "start_date", "end_date", "fields", "sort"}
)


class Dataset:
    """작업을 Provider 어댑터로 라우팅하는 바인딩된 데이터셋."""

    def __init__(self, ref: DatasetRef, adapter: ProviderAdapter) -> None:
        """정규 참조와 어댑터에 바인딩된 데이터셋을 초기화한다."""

        self._ref: DatasetRef = ref
        self._adapter: ProviderAdapter = adapter

    @property
    def ref(self) -> DatasetRef:
        """불변 정규 데이터셋 참조를 반환한다."""

        return self._ref

    @property
    def id(self) -> str:
        """정규 데이터셋 식별자를 반환한다."""

        return self._ref.id

    @property
    def name(self) -> str:
        """사람이 읽기 쉬운 데이터셋 이름을 반환한다."""

        return self._ref.name

    @property
    def provider(self) -> str:
        """이 데이터셋을 제공하는 Provider 식별자를 반환한다."""

        return self._ref.provider

    @property
    def operations(self) -> frozenset[Operation]:
        """이 데이터셋에 선언된 작업 capability를 반환한다."""

        return self._ref.operations

    def list(self, **kwargs: object) -> RecordBatch:
        """정규 list 의미론으로 이 데이터셋의 레코드를 조회한다.

        정규 질의 파라미터(``page``, ``page_size``, ``cursor``,
        ``start_date``, ``end_date``, ``fields``, ``sort``)는 해당 ``Query`` 필드로
        추출된다. 나머지 kwargs는 Provider별 ``filters``로 전달된다.

        예외:
            UnsupportedCapabilityError: 이 데이터셋이 ``list``를 지원하지 않을 때.
        """

        if Operation.LIST not in self._ref.operations:
            logger.debug(
                "Dataset does not support LIST",
                extra={
                    "dataset_id": self._ref.id,
                    "provider": self._ref.provider,
                    "operation": "list",
                },
            )
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
        logger.debug(
            "Dataset.list dispatching",
            extra={
                "dataset_id": self._ref.id,
                "provider": self._ref.provider,
                "page": page,
                "page_size": page_size,
                "cursor": cursor,
                "start_date": start_date,
                "end_date": end_date,
                "fields": fields_list,
                "sort": sort_list,
                "filter_keys": sorted(filters.keys()),
            },
        )
        batch = self._adapter.query_records(self._ref, query)
        logger.debug(
            "Dataset.list completed",
            extra={
                "dataset_id": self._ref.id,
                "provider": self._ref.provider,
                "item_count": len(batch.items),
                "total_count": batch.total_count,
                "next_page": batch.next_page,
                "next_cursor": batch.next_cursor,
            },
        )
        return batch

    def list_all(self, **kwargs: object) -> Generator[RecordBatch, None, None]:
        """다음 페이지나 커서가 있는 동안 RecordBatch를 연속으로 반환한다."""
        if Operation.LIST not in self._ref.operations:
            raise UnsupportedCapabilityError(
                f"Dataset does not support list: {self._ref.id}",
                provider=self._ref.provider,
                dataset_id=self._ref.id,
                operation=Operation.LIST.value,
            )

        logger.debug(
            "Dataset.list_all starting",
            extra={
                "dataset_id": self._ref.id,
                "provider": self._ref.provider,
                "filter_keys": sorted(kwargs.keys()),
            },
        )
        page_kwargs = dict(kwargs)
        batch = self.list(**page_kwargs)
        yield batch
        page_index = 1
        while batch.next_page is not None or batch.next_cursor is not None:
            page_index += 1
            if batch.next_cursor is not None:
                page_kwargs["cursor"] = batch.next_cursor
                _ = page_kwargs.pop("page", None)
            else:
                page_kwargs["page"] = batch.next_page
                _ = page_kwargs.pop("cursor", None)
            logger.debug(
                "Dataset.list_all advancing",
                extra={
                    "dataset_id": self._ref.id,
                    "iteration": page_index,
                    "next_page": page_kwargs.get("page"),
                    "next_cursor": page_kwargs.get("cursor"),
                },
            )
            batch = self.list(**page_kwargs)
            yield batch
        logger.debug(
            "Dataset.list_all completed",
            extra={
                "dataset_id": self._ref.id,
                "iterations": page_index,
            },
        )

    def schema(self) -> SchemaDescriptor | None:
        """Provider가 제공하는 경우 정규 스키마 메타데이터를 반환한다."""

        logger.debug(
            "Dataset.schema requested",
            extra={"dataset_id": self._ref.id, "provider": self._ref.provider},
        )
        return self._adapter.get_schema(self._ref)

    def call_raw(self, operation: str, **params: object) -> object:
        """정규 정규화 없이 Provider 고유 작업을 실행한다.

        정규 모델에 표현되지 않은 Provider 기능에는 이 비상구를 사용한다.
        """

        payload: dict[str, object] = {k: v for k, v in params.items()}
        logger.debug(
            "Dataset.call_raw dispatching",
            extra={
                "dataset_id": self._ref.id,
                "provider": self._ref.provider,
                "operation": operation,
                "param_keys": sorted(payload.keys()),
            },
        )
        return self._adapter.call_raw(self._ref, operation, payload)

    @override
    def __repr__(self) -> str:
        """간결한 디버그 표현을 반환한다."""

        return f"Dataset({self._ref.id!r})"


__all__ = ["Dataset"]
