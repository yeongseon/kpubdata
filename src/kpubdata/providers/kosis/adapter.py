from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import NoReturn, cast
from urllib.parse import urlencode

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
)
from kpubdata.providers._common import build_schema_from_metadata, load_catalogue
from kpubdata.transport.decode import decode_json
from kpubdata.transport.http import HttpTransport, TransportConfig

logger = logging.getLogger("kpubdata.provider.kosis")


class KosisAdapter:
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
        return "kosis"

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
            f"Dataset not found: kosis.{dataset_key}",
            provider="kosis",
            dataset_id=f"kosis.{dataset_key}",
        )

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        url = self._build_request_url(dataset, query)
        payload = self._request_and_decode(url)
        items = self._extract_items(payload, dataset.id)

        return RecordBatch(
            items=items,
            dataset=dataset,
            total_count=len(items),
            next_page=None,
            raw=payload,
        )

    def get_record(self, _dataset: DatasetRef, _key: dict[str, object]) -> dict[str, object] | None:
        raise NotImplementedError("TODO: implement kosis get_record")

    def get_schema(self, dataset: DatasetRef) -> SchemaDescriptor | None:
        return build_schema_from_metadata(dataset)

    def call_raw(self, dataset: DatasetRef, operation: str, params: dict[str, object]) -> object:
        url = self._build_raw_url(dataset, operation, params)
        payload = self._request_and_decode(url)
        if isinstance(payload, dict):
            self._raise_for_error_payload(cast(dict[str, object], payload), dataset.id)
        return payload

    def _require_api_key(self) -> str:
        return self._config.require_provider_key("kosis")

    def _build_request_url(self, dataset: DatasetRef, query: Query) -> str:
        start_date = query.start_date
        end_date = query.end_date
        if not isinstance(start_date, str) or not start_date:
            raise InvalidRequestError(
                "KOSIS queries require start_date",
                provider="kosis",
                dataset_id=dataset.id,
            )
        if not isinstance(end_date, str) or not end_date:
            raise InvalidRequestError(
                "KOSIS queries require end_date",
                provider="kosis",
                dataset_id=dataset.id,
            )

        filters: dict[str, object] = dict(query.filters)
        params = self._build_base_params(dataset)
        params["startPrdDe"] = start_date
        params["endPrdDe"] = end_date

        reserved = {key.casefold() for key in params}
        for key in ("objL1", "objL2", "itmId", "prdSe"):
            if key in filters:
                params[key] = str(filters.pop(key))

        for key, value in filters.items():
            if key.casefold() not in reserved:
                params[key] = str(value)

        return self._compose_url(dataset, params)

    def _build_raw_url(
        self,
        dataset: DatasetRef,
        operation: str,
        params: Mapping[str, object],
    ) -> str:
        request_params = self._build_base_params(dataset)
        selected_operation = operation.strip()
        if selected_operation and selected_operation != "statisticsParameterData":
            request_params["operation"] = selected_operation
        for key, value in params.items():
            if key != "apiKey":
                request_params[key] = str(value)
        return self._compose_url(dataset, request_params)

    def _build_base_params(self, dataset: DatasetRef) -> dict[str, str]:
        api_key = self._require_api_key()
        org_id = self._require_dataset_metadata(dataset, "org_id")
        tbl_id = self._require_dataset_metadata(dataset, "tbl_id")
        return {
            "apiKey": api_key,
            "format": "json",
            "jsonVD": "Y",
            "orgId": org_id,
            "tblId": tbl_id,
            "objL1": "ALL",
            "objL2": "ALL",
            "itmId": "ALL",
            "prdSe": "M",
        }

    def _compose_url(self, dataset: DatasetRef, params: Mapping[str, str]) -> str:
        base_url = self._require_dataset_metadata(dataset, "base_url")
        query_string = urlencode(params)
        return f"{base_url}?{query_string}"

    def _request_and_decode(self, url: str) -> object:
        response = self._transport.request("GET", url)

        try:
            decoded: object = decode_json(response.content)
        except ParseError as exc:
            exc.provider = "kosis"
            raise

        if isinstance(decoded, list):
            return cast(list[object], decoded)
        if isinstance(decoded, dict):
            return cast(dict[str, object], decoded)

        raise ParseError("Decoded payload is neither an object nor an array", provider="kosis")

    def _extract_items(self, payload: object, dataset_id: str) -> list[dict[str, object]]:
        if isinstance(payload, dict):
            self._raise_for_error_payload(cast(dict[str, object], payload), dataset_id)

        if not isinstance(payload, list):
            raise ProviderResponseError(
                "Malformed KOSIS response: expected array payload",
                provider="kosis",
                dataset_id=dataset_id,
            )

        payload_items = cast(list[object], payload)
        return [cast(dict[str, object], item) for item in payload_items if isinstance(item, dict)]

    def _raise_for_error_payload(self, payload: Mapping[str, object], dataset_id: str) -> NoReturn:
        code_raw = payload.get("err")
        message_raw = payload.get("errMsg")
        code = code_raw if isinstance(code_raw, str) else None
        message = message_raw if isinstance(message_raw, str) else "KOSIS returned an error"

        logger.debug(
            "KOSIS error response",
            extra={"provider_code": code, "message": message, "dataset_id": dataset_id},
        )

        if code == "30":
            raise AuthError(
                message,
                provider="kosis",
                dataset_id=dataset_id,
                provider_code=code,
                detail=dict(payload),
            )
        if code == "10":
            raise InvalidRequestError(
                message,
                provider="kosis",
                dataset_id=dataset_id,
                provider_code=code,
                detail=dict(payload),
            )
        raise ProviderResponseError(
            message,
            provider="kosis",
            dataset_id=dataset_id,
            provider_code=code,
            detail=dict(payload),
        )

    @staticmethod
    def _require_dataset_metadata(dataset: DatasetRef, field_name: str) -> str:
        value = dataset.raw_metadata.get(field_name)
        if isinstance(value, str) and value:
            return value
        raise ProviderResponseError(
            f"Dataset metadata missing {field_name}",
            provider="kosis",
            dataset_id=dataset.id,
        )

    @staticmethod
    def _load_default_catalogue() -> tuple[DatasetRef, ...]:
        return load_catalogue("kpubdata.providers.kosis", "kosis")


__all__ = ["KosisAdapter"]
