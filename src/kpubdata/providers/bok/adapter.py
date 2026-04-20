from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import NoReturn, cast

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import (
    DatasetRef,
    Query,
    RecordBatch,
    SchemaDescriptor,
)
from kpubdata.exceptions import (
    AuthError,
    DatasetNotFoundError,
    InvalidRequestError,
    ParseError,
    ProviderResponseError,
    RateLimitError,
    ServiceUnavailableError,
)
from kpubdata.providers._common import build_schema_from_metadata, coerce_int, load_catalogue
from kpubdata.transport.decode import decode_json
from kpubdata.transport.http import HttpTransport, TransportConfig

logger = logging.getLogger("kpubdata.provider.bok")


class BokAdapter:
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
        return "bok"

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

        logger.debug(
            "BOK dataset not found",
            extra={"dataset_id": f"bok.{dataset_key}", "provider": "bok"},
        )
        raise DatasetNotFoundError(
            f"Dataset not found: bok.{dataset_key}",
            provider="bok",
            dataset_id=f"bok.{dataset_key}",
        )

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        page = query.page or 1
        page_size = query.page_size or 100
        frequency = self._resolve_frequency(query)
        start_date = query.start_date or self._resolve_string_param(query, "start_date")
        end_date = query.end_date or self._resolve_string_param(query, "end_date")
        logger.debug(
            "bok query_records",
            extra={
                "dataset_id": dataset.id,
                "page": page,
                "page_size": page_size,
                "frequency": frequency,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

        if start_date is None or end_date is None:
            logger.debug(
                "BOK ECOS invalid query: missing start/end date",
                extra={"dataset_id": dataset.id},
            )
            raise InvalidRequestError(
                "BOK ECOS queries require start_date and end_date",
                provider="bok",
                dataset_id=dataset.id,
            )

        start_index = (page - 1) * page_size + 1
        end_index = page * page_size
        url = self._build_request_url(
            dataset,
            operation=None,
            start_index=start_index,
            end_index=end_index,
            frequency=frequency,
            start_date=start_date,
            end_date=end_date,
        )

        payload = self._request_and_decode(url, dataset.id)
        body, items = self._validate_envelope(payload, dataset.id)

        total_count = coerce_int(body.get("list_total_count"), 0)
        if (total_count and page * page_size < total_count) or (
            not total_count and len(items) == page_size
        ):
            computed_next = page + 1
        else:
            computed_next = None

        if not items:
            logger.debug(
                "BOK envelope: zero items",
                extra={
                    "dataset_id": dataset.id,
                    "page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                },
            )

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
        logger.debug(
            "bok call_raw",
            extra={
                "dataset_id": dataset.id,
                "operation": operation,
                "param_keys": sorted(params.keys()),
            },
        )
        frequency = self._string_param(params, "frequency") or "M"
        start_date = self._require_param(params, "start_date", dataset.id)
        end_date = self._require_param(params, "end_date", dataset.id)
        start_index = self._int_param(params, "start_index", 1)
        end_index = self._int_param(params, "end_index", 10)

        url = self._build_request_url(
            dataset,
            operation=operation,
            start_index=start_index,
            end_index=end_index,
            frequency=frequency,
            start_date=start_date,
            end_date=end_date,
        )
        payload = self._request_and_decode(url, dataset.id)
        _ = self._validate_envelope(payload, dataset.id)
        return payload

    def _require_api_key(self) -> str:
        return self._config.require_provider_key("bok")

    def _build_request_url(
        self,
        dataset: DatasetRef,
        *,
        operation: str | None,
        start_index: int,
        end_index: int,
        frequency: str,
        start_date: str,
        end_date: str,
    ) -> str:
        base_url_raw = dataset.raw_metadata.get("base_url")
        if not isinstance(base_url_raw, str) or not base_url_raw:
            logger.debug(
                "BOK ECOS dataset metadata missing base_url",
                extra={"dataset_id": dataset.id},
            )
            raise ProviderResponseError(
                "Dataset metadata missing base_url",
                provider="bok",
                dataset_id=dataset.id,
            )

        selected_operation = operation or dataset.raw_metadata.get("default_operation")
        if not isinstance(selected_operation, str) or not selected_operation:
            logger.debug(
                "BOK ECOS dataset metadata missing default_operation",
                extra={"dataset_id": dataset.id},
            )
            raise ProviderResponseError(
                "Dataset metadata missing default_operation",
                provider="bok",
                dataset_id=dataset.id,
            )

        stat_code = self._require_dataset_metadata(dataset, "stat_code")
        item_code1 = self._require_dataset_metadata(dataset, "item_code1")
        api_key = self._require_api_key()
        return (
            f"{base_url_raw}/{api_key}/json/{selected_operation}/"
            f"{start_index}/{end_index}/{stat_code}/{frequency}/{start_date}/{end_date}/{item_code1}"
        )

    def _request_and_decode(self, url: str, dataset_id: str) -> dict[str, object]:
        response = self._transport.request("GET", url, dataset_id=dataset_id, provider="bok")

        try:
            decoded_obj: object = decode_json(response.content)
        except ParseError as exc:
            exc.provider = "bok"
            logger.debug("BOK ECOS response parsing failed", extra={"dataset_id": dataset_id})
            raise

        if isinstance(decoded_obj, dict):
            return cast(dict[str, object], decoded_obj)

        logger.debug("BOK ECOS decoded payload invalid type", extra={"dataset_id": dataset_id})
        raise ParseError("Decoded payload is not an object", provider="bok")

    def _validate_envelope(
        self, payload: dict[str, object], dataset_id: str = ""
    ) -> tuple[dict[str, object], list[dict[str, object]]]:
        self._raise_for_result(payload, dataset_id)

        body_obj = payload.get("StatisticSearch")
        if not isinstance(body_obj, dict):
            raise ProviderResponseError(
                "Malformed response envelope: missing StatisticSearch",
                provider="bok",
                dataset_id=dataset_id or None,
            )

        body_dict = cast(dict[str, object], body_obj)
        items = self._normalize_rows(body_dict.get("row"))
        return body_dict, items

    def _raise_for_result(self, payload: Mapping[str, object], dataset_id: str) -> None:
        result_obj = payload.get("RESULT")
        if not isinstance(result_obj, dict):
            return

        result_dict = cast(dict[str, object], result_obj)
        code_raw = result_dict.get("CODE")
        message_raw = result_dict.get("MESSAGE")
        code = code_raw if isinstance(code_raw, str) else "ERROR"
        message = message_raw if isinstance(message_raw, str) else "Provider returned error"
        logger.debug(
            "BOK ECOS result",
            extra={"result_code": code, "result_msg": message, "dataset_id": dataset_id},
        )

        if code != "ERROR":
            return

        self._raise_for_result_code(code, message, dataset_id)

    def _raise_for_result_code(self, code: str, msg: str, dataset_id: str) -> NoReturn:
        normalized_msg = msg.casefold()
        if "인증키" in msg or "api key" in normalized_msg or "auth" in normalized_msg:
            raise AuthError(msg, provider="bok", provider_code=code, dataset_id=dataset_id or None)
        if "호출한도" in msg or "too many" in normalized_msg or "rate limit" in normalized_msg:
            raise RateLimitError(
                msg, provider="bok", provider_code=code, dataset_id=dataset_id or None
            )
        if (
            "점검" in msg
            or "service unavailable" in normalized_msg
            or "temporarily unavailable" in normalized_msg
        ):
            raise ServiceUnavailableError(
                msg,
                provider="bok",
                provider_code=code,
                dataset_id=dataset_id or None,
            )
        if "필수" in msg or "invalid" in normalized_msg or "잘못" in msg:
            raise InvalidRequestError(
                msg, provider="bok", provider_code=code, dataset_id=dataset_id or None
            )
        raise ProviderResponseError(
            msg, provider="bok", provider_code=code, dataset_id=dataset_id or None
        )

    def _resolve_frequency(self, query: Query) -> str:
        return self._resolve_string_param(query, "frequency") or "M"

    def _resolve_string_param(self, query: Query, key: str) -> str | None:
        if key in query.extra:
            extra_value = query.extra[key]
            if isinstance(extra_value, str) and extra_value:
                return extra_value
        if key in query.filters:
            filter_value = query.filters[key]
            if isinstance(filter_value, str) and filter_value:
                return filter_value
        return None

    def _require_dataset_metadata(self, dataset: DatasetRef, key: str) -> str:
        value = dataset.raw_metadata.get(key)
        if isinstance(value, str) and value:
            return value
        raise ProviderResponseError(
            f"Dataset metadata missing {key}",
            provider="bok",
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

    @staticmethod
    def _string_param(params: Mapping[str, object], key: str) -> str | None:
        value = params.get(key)
        if isinstance(value, str) and value:
            return value
        return None

    @classmethod
    def _require_param(cls, params: Mapping[str, object], key: str, dataset_id: str) -> str:
        value = cls._string_param(params, key)
        if value is not None:
            return value
        logger.debug(
            "BOK ECOS raw call missing required parameter",
            extra={"dataset_id": dataset_id},
        )
        raise InvalidRequestError(
            f"BOK ECOS raw calls require {key}", provider="bok", dataset_id=dataset_id
        )

    @classmethod
    def _int_param(cls, params: Mapping[str, object], key: str, default: int) -> int:
        value = params.get(key)
        coerced = coerce_int(value, default)
        return coerced if coerced > 0 else default

    @staticmethod
    def _load_default_catalogue() -> tuple[DatasetRef, ...]:
        return load_catalogue("kpubdata.providers.bok", "bok")


__all__ = ["BokAdapter"]
