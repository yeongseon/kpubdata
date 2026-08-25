"""AirKorea(에어코리아) 대기오염 정보 어댑터."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import cast

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.exceptions import (
    DatasetNotFoundError,
    InvalidRequestError,
    ParseError,
    ProviderResponseError,
)
from kpubdata.providers._common import build_schema_from_metadata, coerce_int, load_catalogue
from kpubdata.transport.decode import decode_json
from kpubdata.transport.http import HttpTransport, TransportConfig


class AirKoreaAdapter:
    """AirKorea(에어코리아) 대기오염 정보 어댑터.

    실시간 측정소별 대기질 정보, 대기질 예보 정보, 통합대기환경지수(CAI)를 제공합니다.
    """

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
    def name(self) -> str:
        """name과 관련된 값을 계산하거나 조회한다."""
        return "airkorea"

    def list_datasets(self) -> list[DatasetRef]:
        """list datasets과 관련된 값을 계산하거나 조회한다."""
        return list(self._datasets)

    def search_datasets(self, text: str) -> list[DatasetRef]:
        """search datasets과 관련된 값을 계산하거나 조회한다."""
        needle = text.casefold()
        return [
            dataset
            for dataset in self._datasets
            if needle in dataset.id.casefold() or needle in dataset.name.casefold()
        ]

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        """dataset을 반환한다."""
        dataset = self._datasets_by_key.get(dataset_key)
        if dataset is not None:
            return dataset

        raise DatasetNotFoundError(
            f"Dataset not found: airkorea.{dataset_key}",
            provider="airkorea",
            dataset_id=f"airkorea.{dataset_key}",
        )

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        """records을 수행한다."""
        page_no = query.page or 1
        page_size = query.page_size or 100
        self._validate_pagination(page_no, page_size, dataset.id)

        start_index = (page_no - 1) * page_size + 1
        end_index = page_no * page_size
        url = self._build_request_url(
            dataset,
            start_index=start_index,
            end_index=end_index,
        )

        payload = self._request_and_decode(url, dataset.id)
        body, items = self._parse_response(payload, dataset)

        total_count = coerce_int(body.get("list_total_count"), len(items))
        next_page = page_no + 1 if total_count > 0 and end_index < total_count else None

        return RecordBatch(
            items=items,
            dataset=dataset,
            total_count=total_count if total_count > 0 else None,
            next_page=next_page,
            raw=payload,
        )

    def get_schema(self, dataset: DatasetRef) -> SchemaDescriptor | None:
        """schema을 반환한다."""
        return build_schema_from_metadata(dataset)

    def call_raw(self, dataset: DatasetRef, operation: str, params: dict[str, object]) -> object:
        """call raw과 관련된 값을 계산하거나 조회한다."""
        page_no = self._int_param(params, "page_no", 1)
        page_size = self._int_param(params, "page_size", 100)
        self._validate_pagination(page_no, page_size, dataset.id)

        start_index = (page_no - 1) * page_size + 1
        end_index = page_no * page_size
        url = self._build_request_url(dataset, start_index=start_index, end_index=end_index)

        payload = self._request_and_decode(url, dataset.id)
        self._parse_response(payload, dataset)
        return payload

    def _validate_pagination(self, page_no: int, page_size: int, dataset_id: str) -> None:
        """pagination의 형식을 검증하고 필요한 값을 추출한다."""
        if page_no < 1:
            raise InvalidRequestError(
                "AirKorea API page_no must be >= 1",
                provider="airkorea",
                dataset_id=dataset_id,
            )
        if page_size < 1:
            raise InvalidRequestError(
                "AirKorea API page_size must be >= 1",
                provider="airkorea",
                dataset_id=dataset_id,
            )
        if page_size > 1000:
            raise InvalidRequestError(
                "AirKorea API page_size must be <= 1000",
                provider="airkorea",
                dataset_id=dataset_id,
            )

    def _require_api_key(self) -> str:
        """필수 API 키을 읽고 없으면 예외를 발생시킨다."""
        return self._config.require_provider_key("airkorea")

    def _build_request_url(
        self,
        dataset: DatasetRef,
        *,
        start_index: int,
        end_index: int,
    ) -> str:
        """요청 URL을 구성해 반환한다."""
        base_url = self._require_dataset_metadata(dataset, "base_url")
        service_name = self._service_name(dataset)
        api_key = self._require_api_key()
        return f"{base_url}/{api_key}/json/{service_name}/{start_index}/{end_index}"

    def _service_name(self, dataset: DatasetRef) -> str:
        """service name과 관련된 값을 계산하거나 조회한다."""
        service_name = self._require_dataset_metadata(dataset, "service_name")
        if isinstance(service_name, str) and service_name:
            return service_name
        return dataset.dataset_key

    def _request_and_decode(self, url: str, dataset_id: str) -> dict[str, object]:
        """request and decode와 관련된 값을 계산하거나 조회한다."""
        api_key = self._require_api_key()
        response = self._transport.request(
            "GET", url, dataset_id=dataset_id, provider="airkorea", sensitive_values=(api_key,)
        )

        try:
            decoded: object = decode_json(response.content)
        except ParseError as exc:
            exc.provider = "airkorea"
            raise

        if isinstance(decoded, dict):
            return cast(dict[str, object], decoded)
        raise ParseError(
            "Decoded payload is not an object", provider="airkorea", dataset_id=dataset_id
        )

    def _parse_response(
        self, payload: dict[str, object], dataset: DatasetRef
    ) -> tuple[dict[str, object], list[dict[str, object]]]:
        """response를 파싱해 body와 items를 반환한다."""
        service_name = self._service_name(dataset)
        
        # AirKorea 응답 구조: {service_name: {total_count: N, row: [items]}}
        service_data = payload.get(service_name)
        if not isinstance(service_data, dict):
            raise ProviderResponseError(
                f"Service data not found in response",
                provider="airkorea",
                dataset_id=dataset.id,
            )

        total_count = service_data.get("total_count", 0)
        if not isinstance(total_count, int):
            total_count = 0

        row_data = service_data.get("row", [])
        if not isinstance(row_data, list):
            raise ProviderResponseError(
                f"Row data is not a list",
                provider="airkorea",
                dataset_id=dataset.id,
            )

        return service_data, cast(list[dict[str, object]], row_data)

    def _require_dataset_metadata(self, dataset: DatasetRef, key: str) -> str:
        """필수 dataset metadata을 읽고 없으면 예외를 발생시킨다."""
        value = dataset.raw_metadata.get(key)
        if isinstance(value, str) and value:
            return value
        raise ProviderResponseError(
            f"Dataset metadata missing {key}",
            provider="airkorea",
            dataset_id=dataset.id,
        )

    @staticmethod
    def _int_param(params: Mapping[str, object], key: str, default: int) -> int:
        """int param과 관련된 값을 계산하거나 조회한다."""
        coerced = coerce_int(params.get(key), default)
        return coerced if coerced > 0 else default

    def _load_default_catalogue(self) -> tuple[DatasetRef, ...]:
        """기본 카탈로그를 로드하고 반환한다."""
        from kpubdata.providers.airkorea import AIRKOREA_CATALOGUE

        return tuple(
            DatasetRef(
                id=f"airkorea.{ds['id']}",
                name=ds["name"],
                description=ds.get("description", ""),
                provider="airkorea",
                dataset_key=ds["id"],
                raw_metadata=ds.get("metadata", {}),
            )
            for ds in AIRKOREA_CATALOGUE
        )