"""KPubData Python 모듈.

이 파일은 ``src/kpubdata/providers/kipris/adapter.py`` 경로의 구현을 담는다.
주요 클래스와 함수는 공개 API, 전송 계층, Provider 어댑터 중 하나의 역할을 담당한다.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, cast

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.exceptions import (
    DatasetNotFoundError,
    InvalidRequestError,
    ParseError,
    ProviderResponseError,
)
from kpubdata.providers._common import build_schema_from_metadata, coerce_int, load_catalogue
from kpubdata.providers.kipris.envelope import extract_items, parse_xml_response, validate_envelope
from kpubdata.transport.http import HttpTransport, TransportConfig


class KiprisAdapter:
    """KiprisAdapter과 관련된 값을 계산하거나 조회한다."""

    requires_api_key: bool = True

    def __init__(
        self,
        *,
        config: KPubDataConfig | None = None,
        transport: HttpTransport | None = None,
        catalogue: Sequence[DatasetRef] | None = None,
    ) -> None:
        """인스턴스가 사용할 내부 상태를 초기화한다."""
        self._config: KPubDataConfig = config or KPubDataConfig()
        transport_config = TransportConfig(
            timeout=self._config.timeout,
            max_retries=self._config.max_retries,
        )
        self._transport: HttpTransport = transport or HttpTransport(transport_config)

        datasets = tuple(catalogue) if catalogue is not None else self._load_default_catalogue()
        self._datasets: tuple[DatasetRef, ...] = datasets
        self._datasets_by_key: dict[str, DatasetRef] = {
            dataset.dataset_key: dataset for dataset in self._datasets
        }

    @property
    def provider_id(self) -> str:
        """provider_id를 반환한다."""
        return "kipris"

    @property
    def name(self) -> str:
        """name을 반환한다."""
        return "KIPRIS(특허청)"

    def list_datasets(self) -> tuple[DatasetRef, ...]:
        """list_datasets를 반환한다."""
        return self._datasets

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        """get_dataset을 반환한다."""
        if dataset_key not in self._datasets_by_key:
            raise DatasetNotFoundError(
                dataset_id=f"kipris.{dataset_key}",
                provider_id=self.provider_id,
                available_keys=list(self._datasets_by_key.keys()),
            )
        return self._datasets_by_key[dataset_key]

    def query_records(
        self,
        dataset: DatasetRef,
        query: Query,
    ) -> RecordBatch:
        """query_records를 반환한다."""
        self._validate_dataset(dataset)
        self._validate_query(query)

        start_index = ((query.page - 1) * query.page_size) + 1
        end_index = query.page * query.page_size

        params: dict[str, str] = {
            "serviceKey": cast(str, self._config.api_key),
            "numOfRows": str(query.page_size),
            "pageNo": str(query.page),
            "startIndex": str(start_index),
            "endIndex": str(end_index),
        }

        if query.filters:
            params.update(query.filters)

        try:
            response = self._transport.request(
                method="GET",
                url=self._get_base_url(dataset),
                params=params,
                sensitive_values=(cast(str, self._config.api_key),),
            )
        except Exception as e:
            raise ProviderResponseError(
                provider_id=self.provider_id,
                dataset_id=dataset.id,
                message=f"HTTP request failed: {e}",
            ) from e

        try:
            response_data = parse_xml_response(response.content)
        except Exception as e:
            raise ParseError(
                dataset_id=dataset.id,
                message=f"Failed to parse XML response: {e}",
            ) from e

        try:
            items = extract_items(response_data)
        except Exception as e:
            raise ParseError(
                dataset_id=dataset.id,
                message=f"Failed to extract items: {e}",
            ) from e

        total_count = response_data.get("response", {}).get("body", {}).get("totalCount", 0)
        if isinstance(total_count, str):
            total_count = coerce_int(total_count)

        has_more = total_count > end_index

        return RecordBatch(
            dataset=dataset,
            total_count=total_count if total_count else len(items),
            items=items,
            has_more=has_more,
            next_page=query.page + 1 if has_more else None,
            raw=response_data,
        )

    def call_raw(
        self,
        dataset: DatasetRef,
        operation: str,
        params: dict[str, str],
    ) -> dict[str, Any]:
        """call_raw를 반환한다."""
        self._validate_dataset(dataset)

        request_params: dict[str, str] = {
            "serviceKey": cast(str, self._config.api_key),
            **params,
        }

        try:
            response = self._transport.request(
                method="GET",
                url=self._get_base_url(dataset),
                params=request_params,
                sensitive_values=(cast(str, self._config.api_key),),
            )
        except Exception as e:
            raise ProviderResponseError(
                provider_id=self.provider_id,
                dataset_id=dataset.id,
                message=f"HTTP request failed: {e}",
            ) from e

        return parse_xml_response(response.content)

    def get_schema(self, dataset: DatasetRef) -> SchemaDescriptor | None:
        """get_schema를 반환한다."""
        self._validate_dataset(dataset)

        try:
            response = self._transport.request(
                method="GET",
                url=self._get_base_url(dataset),
                params={"serviceKey": cast(str, self._config.api_key), "numOfRows": "1", "pageNo": "1"},
                sensitive_values=(cast(str, self._config.api_key),),
            )
        except Exception:
            return None

        try:
            response_data = parse_xml_response(response.content)
            items = extract_items(response_data)
        except Exception:
            return None

        if not items:
            return None

        first_item = items[0] if isinstance(items, list) else items
        return build_schema_from_metadata(first_item)

    def search_datasets(self, query: str) -> tuple[DatasetRef, ...]:
        """search_datasets를 반환한다."""
        query_lower = query.lower()

        exact_matches = [
            dataset
            for dataset in self._datasets
            if dataset.dataset_key == query
            or dataset.dataset_key == query_lower
            or dataset.id == f"kipris.{query}"
            or dataset.id == f"kipris.{query_lower}"
        ]

        if exact_matches:
            return tuple(exact_matches)

        filtered = [
            dataset
            for dataset in self._datasets
            if query_lower in dataset.dataset_key.lower()
            or query_lower in dataset.name.lower()
            or query_lower in dataset.description.lower()
        ]

        return tuple(filtered)

    def _validate_dataset(self, dataset: DatasetRef) -> None:
        """_validate_dataset 역할을 수행한다."""
        if dataset.dataset_key not in self._datasets_by_key:
            raise DatasetNotFoundError(
                dataset_id=dataset.id,
                provider_id=self.provider_id,
                available_keys=list(self._datasets_by_key.keys()),
            )

    def _validate_query(self, query: Query) -> None:
        """_validate_query 역할을 수행한다."""
        if query.page < 1:
            raise InvalidRequestError(
                dataset_id="kipris",
                message=f"Invalid page number: {query.page}",
            )
        if query.page_size < 1:
            raise InvalidRequestError(
                dataset_id="kipris",
                message=f"Invalid page size: {query.page_size}",
            )

    def _get_base_url(self, dataset: DatasetRef) -> str:
        """_get_base_url를 반환한다."""
        metadata = dataset.raw_metadata or {}
        base_url = metadata.get("base_url")
        if not base_url:
            raise ValueError(f"No base_url found in dataset metadata: {dataset.id}")
        return cast(str, base_url)

    def _load_default_catalogue(self) -> tuple[DatasetRef, ...]:
        """_load_default_catalogue를 반환한다."""
        from kpubdata.core.representation import Representation
        from kpubdata.providers.kipris import KIPRIS_CATALOGUE

        return tuple(
            DatasetRef(
                id=f"kipris.{ds['id']}",
                name=ds["name"],
                description=ds.get("description", ""),
                provider="kipris",
                dataset_key=ds["id"],
                representation=Representation.API_XML,
                raw_metadata=ds.get("metadata", {}),
            )
            for ds in KIPRIS_CATALOGUE
        )