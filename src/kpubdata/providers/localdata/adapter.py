from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import NoReturn, cast

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.exceptions import (
    AuthError,
    DatasetNotFoundError,
    ParseError,
    ProviderResponseError,
)
from kpubdata.providers._common import build_schema_from_metadata, coerce_int, load_catalogue
from kpubdata.transport.decode import decode_json
from kpubdata.transport.http import HttpTransport, TransportConfig

logger = logging.getLogger("kpubdata.provider.localdata")


class LocaldataAdapter:
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
        return "localdata"

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

        raise DatasetNotFoundError(
            f"Dataset not found: localdata.{dataset_key}",
            provider="localdata",
            dataset_id=f"localdata.{dataset_key}",
        )

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        page = query.page or 1
        page_size = query.page_size or 100
        logger.debug(
            "localdata query_records",
            extra={
                "dataset_id": dataset.id,
                "page": page,
                "page_size": page_size,
                "filter_keys": sorted(query.filters.keys()),
            },
        )

        url = self._build_request_url(
            dataset, page=page, page_size=page_size, filters=query.filters
        )
        payload = self._request_and_decode(url, dataset.id)

        paging, items = self._validate_envelope(payload, dataset.id)
        total_count = coerce_int(paging.get("totalCount"), 0)
        if (total_count and page * page_size < total_count) or (
            not total_count and len(items) == page_size
        ):
            computed_next = page + 1
        else:
            computed_next = None

        return RecordBatch(
            items=items,
            dataset=dataset,
            total_count=total_count if total_count else None,
            next_page=computed_next,
            raw=payload,
        )

    def get_schema(self, dataset: DatasetRef) -> SchemaDescriptor | None:
        return build_schema_from_metadata(dataset)

    def call_raw(self, dataset: DatasetRef, operation: str, params: dict[str, object]) -> object:
        _ = operation
        logger.debug(
            "localdata call_raw",
            extra={
                "dataset_id": dataset.id,
                "operation": operation,
                "param_keys": sorted(params.keys()),
            },
        )
        page = self._int_param(params, "pageIndex", self._int_param(params, "page", 1))
        page_size = self._int_param(
            params,
            "pageSize",
            self._int_param(params, "page_size", 100),
        )
        extra_keys = {"pageIndex", "page", "pageSize", "page_size"}
        filters = {k: v for k, v in params.items() if k not in extra_keys}

        url = self._build_request_url(dataset, page=page, page_size=page_size, filters=filters)
        payload = self._request_and_decode(url, dataset.id)
        _ = self._validate_envelope(payload, dataset.id)
        return payload

    def _require_api_key(self) -> str:
        return self._config.require_provider_key("localdata")

    def _build_request_url(
        self,
        dataset: DatasetRef,
        *,
        page: int,
        page_size: int,
        filters: dict[str, object] | None = None,
    ) -> str:
        base_url_raw = dataset.raw_metadata.get("base_url")
        if not isinstance(base_url_raw, str) or not base_url_raw:
            raise ProviderResponseError(
                "Dataset metadata missing base_url",
                provider="localdata",
                dataset_id=dataset.id,
            )

        opn_svc_id = self._require_dataset_metadata(dataset, "opn_svc_id")
        api_key = self._require_api_key()
        safe_page = page if page > 0 else 1
        safe_page_size = page_size if page_size > 0 else 100
        if safe_page_size > 500:
            safe_page_size = 500
        url = (
            f"{base_url_raw}"
            f"?authKey={api_key}&opnSvcId={opn_svc_id}&resultType=json"
            f"&pageIndex={safe_page}&pageSize={safe_page_size}"
        )
        if filters:
            for key, value in filters.items():
                if key in {"authKey", "opnSvcId", "resultType", "pageIndex", "pageSize"}:
                    continue
                url += f"&{key}={value}"
        return url

    def _request_and_decode(self, url: str, dataset_id: str = "") -> dict[str, object]:
        response = self._transport.request("GET", url)

        try:
            decoded_obj: object = decode_json(response.content)
        except ValueError as exc:
            raise ParseError("Failed to parse Localdata response", provider="localdata") from exc

        if isinstance(decoded_obj, dict):
            payload = cast(dict[str, object], decoded_obj)
            self._raise_for_process(payload, dataset_id)
            return payload

        raise ParseError("Decoded payload is not an object", provider="localdata")

    def _validate_envelope(
        self, payload: dict[str, object], dataset_id: str
    ) -> tuple[dict[str, object], list[dict[str, object]]]:
        result_obj = payload.get("result")
        if not isinstance(result_obj, dict):
            raise ProviderResponseError(
                "Malformed response envelope: missing result",
                provider="localdata",
                dataset_id=dataset_id or None,
            )

        result_dict = cast(dict[str, object], result_obj)
        header_obj = result_dict.get("header")
        if not isinstance(header_obj, dict):
            raise ProviderResponseError(
                "Malformed response envelope: missing header",
                provider="localdata",
                dataset_id=dataset_id or None,
            )

        header_dict = cast(dict[str, object], header_obj)
        process_obj = header_dict.get("process")
        if not isinstance(process_obj, Mapping):
            raise ProviderResponseError(
                "Malformed response envelope: missing process",
                provider="localdata",
                dataset_id=dataset_id or None,
            )
        self._raise_for_process_code(cast(Mapping[str, object], process_obj), dataset_id)

        paging_obj = header_dict.get("paging")
        paging = cast(dict[str, object], paging_obj) if isinstance(paging_obj, dict) else {}

        body_obj = result_dict.get("body")
        body_dict = cast(dict[str, object], body_obj) if isinstance(body_obj, dict) else {}
        rows_obj = body_dict.get("rows")
        rows_dict = cast(dict[str, object], rows_obj) if isinstance(rows_obj, dict) else {}
        items = self._normalize_rows(rows_dict.get("row"))
        return paging, items

    def _raise_for_process(self, payload: Mapping[str, object], dataset_id: str) -> None:
        result_obj = payload.get("result")
        if not isinstance(result_obj, Mapping):
            return

        result_dict = cast(Mapping[str, object], result_obj)
        header_obj = result_dict.get("header")
        if not isinstance(header_obj, Mapping):
            return

        header_dict = cast(Mapping[str, object], header_obj)
        process_obj = header_dict.get("process")
        if not isinstance(process_obj, Mapping):
            return

        self._raise_for_process_code(cast(Mapping[str, object], process_obj), dataset_id)

    def _raise_for_process_code(self, process_obj: Mapping[str, object], dataset_id: str) -> None:
        code_raw = process_obj.get("code")
        message_raw = process_obj.get("message")
        code = code_raw if isinstance(code_raw, str) else "ERROR"
        message = message_raw if isinstance(message_raw, str) else "Provider returned error"
        logger.debug(
            "localdata process",
            extra={"result_code": code, "result_msg": message, "dataset_id": dataset_id},
        )
        if code == "00":
            return
        self._raise_for_result_code(code, message, dataset_id)

    def _raise_for_result_code(self, code: str, msg: str, dataset_id: str) -> NoReturn:
        if code in {"30", "99"}:
            raise AuthError(
                msg,
                provider="localdata",
                provider_code=code,
                dataset_id=dataset_id or None,
            )
        raise ProviderResponseError(
            msg,
            provider="localdata",
            provider_code=code,
            dataset_id=dataset_id or None,
        )

    def _require_dataset_metadata(self, dataset: DatasetRef, key: str) -> str:
        value = dataset.raw_metadata.get(key)
        if isinstance(value, str) and value:
            return value
        raise ProviderResponseError(
            f"Dataset metadata missing {key}",
            provider="localdata",
            dataset_id=dataset.id,
        )

    def _normalize_rows(self, rows_wrapper: object) -> list[dict[str, object]]:
        if rows_wrapper is None:
            return []
        if isinstance(rows_wrapper, list):
            rows = cast(list[object], rows_wrapper)
            return [cast(dict[str, object], item) for item in rows if isinstance(item, dict)]
        if isinstance(rows_wrapper, dict):
            return [cast(dict[str, object], rows_wrapper)]
        return []

    @classmethod
    def _int_param(cls, params: Mapping[str, object], key: str, default: int) -> int:
        value = params.get(key)
        coerced = coerce_int(value, default)
        return coerced if coerced > 0 else default

    @staticmethod
    def _load_default_catalogue() -> tuple[DatasetRef, ...]:
        return load_catalogue("kpubdata.providers.localdata", "localdata")


__all__ = ["LocaldataAdapter"]
