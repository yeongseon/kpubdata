"""바인딩된 Dataset — 데이터셋 작업을 위한 사용자 대상 객체."""

from __future__ import annotations

import logging
from collections.abc import Generator, Mapping
from typing import cast

from typing_extensions import override

from kpubdata.core.capability import Operation
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.exceptions import InvalidRequestError, UnsupportedCapabilityError

logger = logging.getLogger("kpubdata.dataset")


def _build_query(kwargs: Mapping[str, object]) -> Query:
    """
    Build a Query from kwargs, separating canonical fields from provider-specific filters.

    Canonical query parameters (extracted as direct Query fields):
        page, page_size, cursor, start_date, end_date, fields, sort

    All other kwargs are preserved in Query.filters for provider-specific handling.

    Args:
        kwargs: Raw keyword arguments from Dataset.list()

    Returns:
        Query with canonical fields populated and remaining kwargs in filters.
    """
    page: object = None
    page_size: object = None
    cursor: object = None
    start_date: object = None
    end_date: object = None
    fields: object = None
    sort: object = None
    filters: dict[str, object] = {}

    for key, value in kwargs.items():
        if key == "page":
            page = value
        elif key == "page_size":
            page_size = value
        elif key == "cursor":
            cursor = value
        elif key == "start_date":
            start_date = value
        elif key == "end_date":
            end_date = value
        elif key == "fields":
            fields = value
        elif key == "sort":
            sort = value
        else:
            filters[key] = value

    return Query(
        filters=filters,
        page=cast(int | None, page),
        page_size=cast(int | None, page_size),
        cursor=cast(str | None, cursor),
        start_date=cast(str | None, start_date),
        end_date=cast(str | None, end_date),
        fields=cast(list[str] | None, fields),
        sort=cast(list[str] | None, sort),
    )


_DEFAULT_MAX_PAGES = 1000


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

        query = _build_query(kwargs)

        logger.debug(
            "Dataset.list dispatching",
            extra={
                "dataset_id": self._ref.id,
                "provider": self._ref.provider,
                "page": query.page,
                "page_size": query.page_size,
                "cursor": query.cursor,
                "start_date": query.start_date,
                "end_date": query.end_date,
                "fields": query.fields,
                "sort": query.sort,
                "filter_keys": sorted(query.filters.keys()),
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

    def list_all(
        self,
        *,
        max_pages: int | None = None,
        **kwargs: object,
    ) -> Generator[RecordBatch, None, None]:
        """다음 페이지나 커서가 있는 동안 RecordBatch를 연속으로 반환한다.

        매개변수:
            max_pages: 가져올 최대 페이지 수. 기본값은 1000입니다.
                제한에 도달하면 InvalidRequestError를 발생시킵니다.
            **kwargs: Provider 어댑터로 전달되는 필터 매개변수.

        예외:
            UnsupportedCapabilityError: 이 데이터셋이 ``list``를 지원하지 않을 때.
            InvalidRequestError: max_pages 제한에 도달했거나 무한 루프가 감지되었을 때.
        """
        if Operation.LIST not in self._ref.operations:
            raise UnsupportedCapabilityError(
                f"Dataset does not support list: {self._ref.id}",
                provider=self._ref.provider,
                dataset_id=self._ref.id,
                operation=Operation.LIST.value,
            )

        # Validate max_pages parameter
        if max_pages is not None:
            if isinstance(max_pages, bool):
                raise InvalidRequestError(
                    f"max_pages must be None or a positive integer, got bool: {max_pages}",
                    provider=self._ref.provider,
                    dataset_id=self._ref.id,
                )
            if not isinstance(max_pages, int):
                raise InvalidRequestError(
                    f"max_pages must be None or a positive integer, "
                    f"got {type(max_pages).__name__}: {max_pages}",
                    provider=self._ref.provider,
                    dataset_id=self._ref.id,
                )
            if max_pages <= 0:
                raise InvalidRequestError(
                    f"max_pages must be None or a positive integer, got {max_pages}",
                    provider=self._ref.provider,
                    dataset_id=self._ref.id,
                )

        effective_max_pages = max_pages if max_pages is not None else _DEFAULT_MAX_PAGES
        seen_pages: set[int] = set()
        seen_cursors: set[str] = set()
        consecutive_empty_batches = 0
        MAX_CONSECUTIVE_EMPTY = 3

        logger.debug(
            "Dataset.list_all starting",
            extra={
                "dataset_id": self._ref.id,
                "provider": self._ref.provider,
                "filter_keys": sorted(kwargs.keys()),
                "max_pages": effective_max_pages,
            },
        )
        page_kwargs = dict(kwargs)
        batch = self.list(**page_kwargs)
        yield batch
        page_index = 1

        # Mark the first request as seen to detect immediate cycles
        # The first request always uses default pagination (page 1 or no cursor)
        if page_kwargs.get("page") is None and page_kwargs.get("cursor") is None:
            seen_pages.add(1)  # We implicitly requested page 1
            seen_cursors.add("")  # We implicitly requested with no cursor

        # Check for empty batch
        if not batch.items:
            consecutive_empty_batches += 1
        else:
            consecutive_empty_batches = 0

        while batch.next_page is not None or batch.next_cursor is not None:
            page_index += 1

            # Max pages check
            if page_index > effective_max_pages:
                raise InvalidRequestError(
                    f"Pagination limit exceeded: reached {page_index} pages "
                    f"(max: {effective_max_pages}). "
                    "This may indicate a bug in the provider API or an infinite pagination loop.",
                    provider=self._ref.provider,
                    dataset_id=self._ref.id,
                )

            # Cycle detection - check BEFORE making the request
            next_continuation: object = None
            if batch.next_cursor is not None:
                next_continuation = batch.next_cursor
                page_kwargs["cursor"] = batch.next_cursor
                _ = page_kwargs.pop("page", None)
                # Check if we've already used this cursor
                if batch.next_cursor in seen_cursors:
                    raise InvalidRequestError(
                        f"Detected pagination cycle: cursor '{batch.next_cursor}' "
                        "was already requested. "
                        "This may indicate a bug in the provider API pagination logic.",
                        provider=self._ref.provider,
                        dataset_id=self._ref.id,
                    )
                seen_cursors.add(batch.next_cursor)
            else:
                next_continuation = batch.next_page
                page_kwargs["page"] = batch.next_page
                _ = page_kwargs.pop("cursor", None)
                # Check if we've already used this page
                if batch.next_page is not None and batch.next_page in seen_pages:
                    raise InvalidRequestError(
                        f"Detected pagination cycle: page {batch.next_page} was already requested. "
                        f"This may indicate a bug in the provider API pagination logic.",
                        provider=self._ref.provider,
                        dataset_id=self._ref.id,
                    )
                if batch.next_page is not None:
                    seen_pages.add(batch.next_page)

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

            # Check for consecutive empty batches
            if not batch.items:
                consecutive_empty_batches += 1
                if consecutive_empty_batches >= MAX_CONSECUTIVE_EMPTY:
                    raise InvalidRequestError(
                        f"Received {MAX_CONSECUTIVE_EMPTY} consecutive empty batches "
                        f"with continuation token. "
                        f"Last continuation: {next_continuation}. "
                        "This may indicate a bug in the provider API pagination logic.",
                        provider=self._ref.provider,
                        dataset_id=self._ref.id,
                    )
            else:
                consecutive_empty_batches = 0

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
