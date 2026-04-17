"""Data.go.kr adapter with curated dataset catalogue."""

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
from kpubdata.transport.decode import decode_json, decode_xml, detect_content_type
from kpubdata.transport.http import HttpTransport, TransportConfig

logger = logging.getLogger("kpubdata.provider.datago")


class DataGoAdapter:
    """Adapter for data.go.kr (공공데이터포털).

    Provides a curated catalogue of supported datasets from the
    apis.data.go.kr endpoint family.
    """

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
        """Return canonical provider key."""

        return "datago"

    def list_datasets(self) -> list[DatasetRef]:
        """List datasets available from data.go.kr."""

        return list(self._datasets)

    def search_datasets(self, text: str) -> list[DatasetRef]:
        """Search datasets available from data.go.kr."""

        needle = text.casefold()
        return [
            dataset
            for dataset in self._datasets
            if needle in dataset.id.casefold() or needle in dataset.name.casefold()
        ]

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        """Resolve provider-local dataset key for data.go.kr."""

        dataset = self._datasets_by_key.get(dataset_key)
        if dataset is not None:
            return dataset

        raise DatasetNotFoundError(
            f"Dataset not found: datago.{dataset_key}",
            provider="datago",
            dataset_id=f"datago.{dataset_key}",
        )

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        """Query records from a data.go.kr dataset."""

        page = query.page or 1
        page_size = query.page_size or 10

        all_items: list[dict[str, object]] = []
        raw_pages: list[dict[str, object]] = []
        total_count: int | None = None

        while True:
            url = self._build_request_url(dataset)
            params = self._build_base_params(dataset)
            params["pageNo"] = str(page)
            params["numOfRows"] = str(page_size)

            reserved = {params_key.lower() for params_key in params}
            reserved.update({"pageno", "numofrows"})
            for key, raw_value in query.filters.items():
                if key.lower() not in reserved:
                    value: object = raw_value
                    params[key] = str(value)

            payload = self._request_and_decode(url, params)
            raw_pages.append(payload)

            body, items = self._validate_envelope(payload, dataset.id)
            all_items.extend(items)

            total_count = coerce_int(body.get("totalCount"), 0)
            current_num_of_rows = coerce_int(body.get("numOfRows"), page_size)

            if not items:
                break
            if len(items) < current_num_of_rows:
                break
            if page * page_size >= total_count:
                break

            page += 1

        return RecordBatch(
            items=all_items,
            dataset=dataset,
            total_count=total_count,
            next_page=None,
            raw=raw_pages,
        )

    def get_record(self, _dataset: DatasetRef, _key: dict[str, object]) -> dict[str, object] | None:
        """Get a single record from a data.go.kr dataset."""

        raise NotImplementedError("TODO: implement datago get_record")

    def get_schema(self, dataset: DatasetRef) -> SchemaDescriptor | None:
        """Get schema metadata for a data.go.kr dataset.

        Returns schema from curated catalogue metadata when available.
        data.go.kr has no live schema discovery endpoint, so this
        returns ``None`` for datasets without explicitly curated field
        definitions in the catalogue.
        """
        return build_schema_from_metadata(dataset)

    def call_raw(self, dataset: DatasetRef, operation: str, params: dict[str, object]) -> object:
        """Call provider-native data.go.kr API operation."""

        url = self._build_request_url(dataset, operation)
        request_params = self._build_base_params(dataset)

        service_key_param = str(dataset.raw_metadata.get("service_key_param", "serviceKey"))
        for key, value in params.items():
            if key != service_key_param:
                request_params[key] = str(value)

        payload = self._request_and_decode(url, request_params)
        _ = self._validate_envelope(payload, dataset.id)
        return payload

    def _require_api_key(self) -> str:
        return self._config.require_provider_key("datago")

    def _build_request_url(self, dataset: DatasetRef, operation: str | None = None) -> str:
        base_url_raw = dataset.raw_metadata.get("base_url")
        if not isinstance(base_url_raw, str) or not base_url_raw:
            raise ProviderResponseError(
                "Dataset metadata missing base_url",
                provider="datago",
                dataset_id=dataset.id,
            )
        selected_operation = operation or dataset.raw_metadata.get("default_operation")
        if isinstance(selected_operation, str) and selected_operation:
            return f"{base_url_raw}/{selected_operation}"
        return base_url_raw

    def _build_base_params(self, dataset: DatasetRef) -> dict[str, str]:
        api_key = self._require_api_key()
        service_key_param_raw = dataset.raw_metadata.get("service_key_param", "serviceKey")
        format_param_raw = dataset.raw_metadata.get("format_param", "resultType")
        service_key_param = (
            service_key_param_raw
            if isinstance(service_key_param_raw, str) and service_key_param_raw
            else "serviceKey"
        )
        format_param = (
            format_param_raw
            if isinstance(format_param_raw, str) and format_param_raw
            else "resultType"
        )
        return {service_key_param: api_key, format_param: "json"}

    def _request_and_decode(self, url: str, params: Mapping[str, object]) -> dict[str, object]:
        string_params = {key: str(value) for key, value in params.items()}
        response = self._transport.request("GET", url, params=string_params)

        try:
            content_type = detect_content_type(response)
            if content_type == "json":
                decoded = decode_json(response.content)
            elif content_type == "xml":
                decoded = decode_xml(response.content)
            else:
                decoded = decode_json(response.content)
        except ParseError as exc:
            exc.provider = "datago"
            raise
        except ImportError as exc:
            raise ParseError("Failed to parse data.go.kr response", provider="datago") from exc

        if isinstance(decoded, dict):
            return cast(dict[str, object], decoded)

        raise ParseError("Decoded payload is not an object", provider="datago")

    def _validate_envelope(
        self, payload: dict[str, object], dataset_id: str = ""
    ) -> tuple[dict[str, object], list[dict[str, object]]]:
        response_obj = payload.get("response")
        if not isinstance(response_obj, dict):
            raise ProviderResponseError(
                "Malformed response envelope: missing response",
                provider="datago",
                dataset_id=dataset_id or None,
            )

        header_obj = response_obj.get("header")
        if not isinstance(header_obj, dict):
            raise ProviderResponseError(
                "Malformed response envelope: missing header",
                provider="datago",
                dataset_id=dataset_id or None,
            )

        header_dict = cast(dict[str, object], header_obj)
        result_code = header_dict.get("resultCode")
        if not isinstance(result_code, str):
            raise ProviderResponseError(
                "Malformed response envelope: missing resultCode",
                provider="datago",
                dataset_id=dataset_id or None,
            )

        result_msg_raw = header_dict.get("resultMsg")
        result_msg = (
            result_msg_raw if isinstance(result_msg_raw, str) else "Provider returned error"
        )
        logger.debug(
            "data.go.kr result",
            extra={"result_code": result_code, "result_msg": result_msg, "dataset_id": dataset_id},
        )
        if result_code != "00":
            self._raise_for_result_code(result_code, result_msg, dataset_id)

        body_obj = response_obj.get("body")
        body_dict: dict[str, object] = (
            cast(dict[str, object], body_obj) if isinstance(body_obj, dict) else {}
        )
        items = self._normalize_items(body_dict.get("items"))
        return body_dict, items

    def _raise_for_result_code(self, code: str, msg: str, dataset_id: str) -> NoReturn:
        if code in {"30", "31", "20", "32"}:
            raise AuthError(msg, provider="datago", provider_code=code)
        if code == "22":
            raise RateLimitError(msg, provider="datago", provider_code=code, retryable=False)
        if code == "10":
            raise InvalidRequestError(msg, provider="datago", provider_code=code)
        if code == "12":
            raise DatasetNotFoundError(
                msg,
                provider="datago",
                provider_code=code,
                dataset_id=dataset_id,
            )
        if code in {"01", "02"}:
            raise ServiceUnavailableError(msg, provider="datago", provider_code=code)
        raise ProviderResponseError(msg, provider="datago", provider_code=code)

    def _normalize_items(self, items_wrapper: object) -> list[dict[str, object]]:
        if items_wrapper is None:
            return []

        if isinstance(items_wrapper, dict):
            item_value = items_wrapper.get("item")
            if isinstance(item_value, list):
                return [item for item in item_value if isinstance(item, dict)]
            if isinstance(item_value, dict):
                return [item_value]
            return []

        if isinstance(items_wrapper, list):
            return [item for item in items_wrapper if isinstance(item, dict)]

        return []

    @staticmethod
    def _load_default_catalogue() -> tuple[DatasetRef, ...]:
        return load_catalogue("kpubdata.providers.datago", "datago")


__all__ = ["DataGoAdapter"]
