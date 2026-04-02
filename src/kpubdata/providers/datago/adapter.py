"""Data.go.kr adapter with curated dataset catalogue."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from importlib.resources import files
from types import MappingProxyType
from typing import NoReturn, cast

from kpubdata.config import KPubDataConfig
from kpubdata.core.capability import Operation, PaginationMode, QuerySupport
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.core.representation import Representation
from kpubdata.exceptions import (
    AuthError,
    DatasetNotFoundError,
    InvalidRequestError,
    ParseError,
    ProviderResponseError,
    RateLimitError,
    ServiceUnavailableError,
)
from kpubdata.transport.decode import decode_json, decode_xml, detect_content_type
from kpubdata.transport.http import HttpTransport, TransportConfig


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

            total_count = self._coerce_int(body.get("totalCount"), 0)
            current_num_of_rows = self._coerce_int(body.get("numOfRows"), page_size)

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

    def get_schema(self, _dataset: DatasetRef) -> SchemaDescriptor | None:
        """Get schema metadata for a data.go.kr dataset."""

        raise NotImplementedError("TODO: implement datago get_schema")

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
        except (ImportError, ValueError) as exc:
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
    def _coerce_int(value: object, default: int) -> int:
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return default
        return default

    @staticmethod
    def _load_default_catalogue() -> tuple[DatasetRef, ...]:
        package_files = files("kpubdata.providers.datago")
        catalogue_text = package_files.joinpath("catalogue.json").read_text(encoding="utf-8")
        parsed_catalogue = cast(object, json.loads(catalogue_text))
        if not isinstance(parsed_catalogue, list):
            msg = "datago catalogue.json must contain a top-level JSON array"
            raise ValueError(msg)

        catalogue_entries = cast(list[object], parsed_catalogue)
        datasets: list[DatasetRef] = []
        for entry_object in catalogue_entries:
            if not isinstance(entry_object, dict):
                msg = "datago catalogue entries must be JSON objects"
                raise ValueError(msg)
            typed_entry_object = cast(dict[object, object], entry_object)
            entry: dict[str, object] = {}
            for key, value in typed_entry_object.items():
                if not isinstance(key, str):
                    msg = "datago catalogue entry keys must be strings"
                    raise ValueError(msg)
                entry[key] = value
            datasets.append(DataGoAdapter._build_dataset_ref(entry))
        return tuple(datasets)

    @staticmethod
    def _build_dataset_ref(entry: dict[str, object]) -> DatasetRef:
        dataset_key = DataGoAdapter._require_string_field(entry, "dataset_key")
        name = DataGoAdapter._require_string_field(entry, "name")
        representation_value = DataGoAdapter._require_string_field(entry, "representation")
        representation = Representation(representation_value)
        ops_raw_obj = entry.get("operations", [])
        ops_raw = ops_raw_obj if isinstance(ops_raw_obj, list) else []
        operations = frozenset(
            Operation(op)
            for op in ops_raw
            if isinstance(op, str) and op in {member.value for member in Operation}
        )

        qs_raw_obj = entry.get("query_support")
        query_support = None
        if isinstance(qs_raw_obj, dict):
            qs_raw = cast(dict[str, object], qs_raw_obj)
            pagination_raw = qs_raw.get("pagination", "none")
            pagination = (
                PaginationMode(pagination_raw)
                if isinstance(pagination_raw, str)
                and pagination_raw in {member.value for member in PaginationMode}
                else PaginationMode.NONE
            )
            max_page_size = None
            if "max_page_size" in qs_raw:
                max_page_size_raw = qs_raw["max_page_size"]
                if isinstance(max_page_size_raw, int):
                    max_page_size = max_page_size_raw
                elif isinstance(max_page_size_raw, str):
                    max_page_size = int(max_page_size_raw)
                else:
                    msg = "datago query_support.max_page_size must be int-like"
                    raise ValueError(msg)
            query_support = QuerySupport(
                pagination=pagination,
                max_page_size=max_page_size,
            )

        raw_metadata = MappingProxyType(
            {
                key: value
                for key, value in entry.items()
                if key
                not in (
                    "dataset_key",
                    "name",
                    "representation",
                    "operations",
                    "query_support",
                )
            }
        )

        return DatasetRef(
            id=f"datago.{dataset_key}",
            provider="datago",
            dataset_key=dataset_key,
            name=name,
            representation=representation,
            operations=operations,
            query_support=query_support,
            raw_metadata=raw_metadata,
        )

    @staticmethod
    def _require_string_field(entry: Mapping[str, object], field_name: str) -> str:
        value = entry.get(field_name)
        if isinstance(value, str) and value:
            return value
        raise ValueError(f"datago catalogue entry missing non-empty string field: {field_name}")


__all__ = ["DataGoAdapter"]
