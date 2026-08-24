"""식품의약품안전처(FDS) open API 어댑터 (#165).

식약처 open API(\`openapi.foodsafetykorea.go.kr\`)는 표준 data.go.kr 엔벨로프가
아닌 고유 경로 형상을 쓴다::

    http://openapi.foodsafetykorea.go.kr/api/{KEY}/{serviceId}/{dataType}/{startIdx}/{endIdx}

- 인증키가 **URL 경로 세그먼트**로 들어간다(#354 마스킹 대상)
- 페이지네이션은 1-based \`startIdx\`/\`endIdx\` 범위 조회
- 오류는 \`{"code": "INFO-100", "message": ...}\` 형태, \`code == "000"\`이 정상
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from urllib.parse import quote

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.exceptions import (
    AuthError,
    DatasetNotFoundError,
    InvalidRequestError,
    ProviderResponseError,
)
from kpubdata.providers._common import build_schema_from_metadata, load_catalogue
from kpubdata.transport.decode import decode_json
from kpubdata.transport.http import HttpTransport, TransportConfig

logger = logging.getLogger("kpubdata.provider.fds")

_MAX_PAGE_SIZE = 1000
_CATALOGUE_PACKAGE = "kpubdata.providers.fds"


class FdsAdapter:
    """식품의약품안전처 open API 어댑터."""

    requires_api_key: bool = True

    def __init__(
        self,
        *,
        config: KPubDataConfig | None = None,
        transport: HttpTransport | None = None,
        catalogue: Sequence[DatasetRef] | None = None,
    ) -> None:
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
        return "fds"

    def list_datasets(self) -> list[DatasetRef]:
        return list(self._datasets)

    def search_datasets(self, text: str) -> list[DatasetRef]:
        needle = text.casefold()
        return [
            dataset
            for dataset in self._datasets
            if needle in dataset.id.casefold() or needle in dataset.name.casefold()
        ]

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        dataset = self._datasets_by_key.get(dataset_key)
        if dataset is not None:
            return dataset
        logger.debug("FDS dataset not found", extra={"dataset_key": dataset_key})
        raise DatasetNotFoundError(
            f"Dataset not found: fds.{dataset_key}",
            provider="fds",
            dataset_id=f"fds.{dataset_key}",
        )

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        page = query.page or 1
        page_size = min(query.page_size or _MAX_PAGE_SIZE, _MAX_PAGE_SIZE)
        start_idx = (page - 1) * page_size + 1
        end_idx = page * page_size

        url = self._build_request_url(dataset, start_idx, end_idx, filters=query.filters)
        payload = self._request_and_decode(url, dataset.id)
        items, total_count = self._parse_fds_envelope(payload, dataset.id)

        next_page: int | None = None
        if total_count and end_idx < total_count or not total_count and len(items) == page_size:
            next_page = page + 1

        return RecordBatch(
            items=items,
            dataset=dataset,
            total_count=total_count if total_count else None,
            next_page=next_page,
            raw=payload,
        )

    def get_schema(self, dataset: DatasetRef) -> SchemaDescriptor | None:
        return build_schema_from_metadata(dataset)

    def call_raw(self, dataset: DatasetRef, operation: str, params: dict[str, object]) -> object:
        logger.debug(
            "fds call_raw",
            extra={"dataset_id": dataset.id, "operation": operation, "param_keys": sorted(params)},
        )
        service = operation or str(dataset.raw_metadata.get("default_operation", ""))
        if not service:
            raise InvalidRequestError(
                "FDS call_raw requires a non-empty service name",
                provider="fds",
                dataset_id=dataset.id,
            )
        start_idx = self._int_param(params, "start_idx", 1)
        end_idx = self._int_param(params, "end_idx", 10)
        filters = {
            k: v for k, v in params.items() if k not in ("start_idx", "end_idx") and str(v).strip()
        }
        url = self._build_request_url(dataset, start_idx, end_idx, service=service, filters=filters)
        payload = self._request_and_decode(url, dataset.id)
        _ = self._parse_fds_envelope(payload, dataset.id)
        return payload

    def _require_api_key(self) -> str:
        return self._config.require_provider_key("fds")

    def _build_request_url(
        self,
        dataset: DatasetRef,
        start_idx: int,
        end_idx: int,
        *,
        service: str | None = None,
        filters: Mapping[str, object] | None = None,
    ) -> str:
        base_url = str(
            dataset.raw_metadata.get("base_url", "http://openapi.foodsafetykorea.go.kr/api")
        )
        service_id = service or str(dataset.raw_metadata.get("default_operation", ""))
        key = quote(self._require_api_key(), safe="")
        url = f"{base_url.rstrip('/')}/{key}/{service_id}/json/{start_idx}/{end_idx}"
        extra = {k: str(v) for k, v in (filters or {}).items() if str(v).strip()}
        if extra:
            from urllib.parse import urlencode

            url = f"{url}?{urlencode(extra)}"
        return url

    def _request_and_decode(self, url: str, dataset_id: str) -> dict[str, object]:
        # 인증키가 URL 경로에 있으므로 로그 마스킹에 실제 키를 넘긴다(#354).
        response = self._transport.request(
            "GET",
            url,
            dataset_id=dataset_id,
            provider="fds",
            secret_values=(self._require_api_key(),),
        )
        decoded: object = decode_json(response.content)
        if not isinstance(decoded, dict):
            raise ProviderResponseError(
                "FDS response is not a JSON object",
                provider="fds",
                dataset_id=dataset_id,
            )
        return decoded

    def _parse_fds_envelope(
        self, payload: Mapping[str, object], dataset_id: str
    ) -> tuple[list[dict[str, object]], int]:
        """FDS 응답에서 (items, total_count)를 추출한다.

        FDS는 목록 최상위 키(예: \`body\`) 아래 리스트를 내려주고, 오류는
        \`code\`/\`message\`로 알린다(\`"000"\` 정상, \`INFO-100\` 인증 오류).
        """
        code = payload.get("code")
        if isinstance(code, str) and code != "000":
            message = str(payload.get("message", ""))
            if code == "INFO-100":
                raise AuthError(
                    f"FDS authentication failed: {message}",
                    provider="fds",
                    dataset_id=dataset_id,
                )
            raise ProviderResponseError(
                f"FDS API error {code}: {message}",
                provider="fds",
                dataset_id=dataset_id,
            )

        body = payload.get("body")
        items: list[dict[str, object]] = []
        if isinstance(body, list):
            items.extend(item for item in body if isinstance(item, dict))
        return items, 0

    @staticmethod
    def _int_param(params: Mapping[str, object], name: str, default: int) -> int:
        raw = params.get(name, default)
        if isinstance(raw, (str, int)) and not isinstance(raw, bool):
            try:
                return int(raw)
            except ValueError:
                return default
        return default

    def _load_default_catalogue(self) -> tuple[DatasetRef, ...]:
        return tuple(load_catalogue(_CATALOGUE_PACKAGE, "fds"))


__all__ = ["FdsAdapter"]
