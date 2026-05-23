"""KPubData Python 모듈.

이 파일은 ``src/kpubdata/providers/localdata/adapter.py`` 경로의 구현을 담는다.
주요 클래스와 함수는 공개 API, 전송 계층, Provider 어댑터 중 하나의 역할을 담당한다.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import NoReturn, cast

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
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

logger = logging.getLogger("kpubdata.provider.localdata")


def _is_success_code(code: str) -> bool:
    """
    내부 헬퍼로서 is success code 처리를 담당한다.

    매개변수:
        code (str): 호출자가 제공하는 입력 값이다.

    반환값:
        bool: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    try:
        return int(code) == 0
    except ValueError:
        return False


class LocaldataAdapter:
    """
    LocaldataAdapter 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``src/kpubdata/providers/localdata/adapter.py`` 모듈 안에서 LocaldataAdapter의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__, name, list_datasets, search_datasets, get_dataset.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    requires_api_key: bool = True

    def __init__(
        self,
        *,
        config: KPubDataConfig | None = None,
        transport: HttpTransport | None = None,
        catalogue: Sequence[DatasetRef] | None = None,
    ) -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        매개변수:
            config (KPubDataConfig | None): 호출자가 제공하는 입력 값이다.
            transport (HttpTransport | None): 호출자가 제공하는 입력 값이다.
            catalogue (Sequence[DatasetRef] | None): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
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
        """
        name 동작을 수행한다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return "localdata"

    def list_datasets(self) -> list[DatasetRef]:
        """
        list datasets 동작을 수행한다.

        반환값:
            list[DatasetRef]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return list(self._datasets)

    def search_datasets(self, text: str) -> list[DatasetRef]:
        """
        search datasets 동작을 수행한다.

        매개변수:
            text (str): 호출자가 제공하는 입력 값이다.

        반환값:
            list[DatasetRef]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        needle = text.casefold()
        return [
            dataset
            for dataset in self._datasets
            if needle in dataset.id.casefold() or needle in dataset.name.casefold()
        ]

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        """
        get dataset 동작을 수행한다.

        매개변수:
            dataset_key (str): 호출자가 제공하는 입력 값이다.

        반환값:
            DatasetRef: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        dataset = self._datasets_by_key.get(dataset_key)
        if dataset is not None:
            return dataset

        logger.debug(
            "Localdata dataset not found",
            extra={"dataset_id": f"localdata.{dataset_key}", "provider": "localdata"},
        )
        raise DatasetNotFoundError(
            f"Dataset not found: localdata.{dataset_key}",
            provider="localdata",
            dataset_id=f"localdata.{dataset_key}",
        )

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        """
        query records 동작을 수행한다.

        매개변수:
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.
            query (Query): 호출자가 제공하는 입력 값이다.

        반환값:
            RecordBatch: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
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

        payload = self._request_and_decode(url, params, dataset.id)

        body, items = self._validate_envelope(payload, dataset.id)
        total_count = coerce_int(body.get("totalCount"), 0)
        if (total_count and page * page_size < total_count) or (
            not total_count and len(items) == page_size
        ):
            computed_next = page + 1
        else:
            computed_next = None

        if not items:
            logger.debug(
                "Localdata envelope: zero items",
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
        """
        get schema 동작을 수행한다.

        매개변수:
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.

        반환값:
            SchemaDescriptor | None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return build_schema_from_metadata(dataset)

    def call_raw(self, dataset: DatasetRef, operation: str, params: dict[str, object]) -> object:
        """
        call raw 동작을 수행한다.

        매개변수:
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.
            operation (str): 호출자가 제공하는 입력 값이다.
            params (dict[str, object]): 호출자가 제공하는 입력 값이다.

        반환값:
            object: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        logger.debug(
            "localdata call_raw",
            extra={
                "dataset_id": dataset.id,
                "operation": operation,
                "param_keys": sorted(params.keys()),
            },
        )
        url = self._build_request_url(dataset, operation)
        request_params = self._build_base_params(dataset)

        service_key_param = str(dataset.raw_metadata.get("service_key_param", "serviceKey"))
        for key, value in params.items():
            if key != service_key_param:
                request_params[key] = str(value)

        payload = self._request_and_decode(url, request_params, dataset.id)
        _ = self._validate_envelope(payload, dataset.id)
        return payload

    def _require_api_key(self) -> str:
        """
        내부 헬퍼로서 require api key 처리를 담당한다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return self._config.require_provider_key("datago")

    def _build_request_url(self, dataset: DatasetRef, operation: str | None = None) -> str:
        """
        내부 헬퍼로서 build request url 처리를 담당한다.

        매개변수:
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.
            operation (str | None): 호출자가 제공하는 입력 값이다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        base_url_raw = dataset.raw_metadata.get("base_url")
        if not isinstance(base_url_raw, str) or not base_url_raw:
            logger.debug(
                "Localdata dataset metadata missing base_url",
                extra={"dataset_id": dataset.id},
            )
            raise ProviderResponseError(
                "Dataset metadata missing base_url",
                provider="localdata",
                dataset_id=dataset.id,
            )

        selected_operation = operation or dataset.raw_metadata.get("default_operation")
        if isinstance(selected_operation, str) and selected_operation:
            return f"{base_url_raw}/{selected_operation}"
        return base_url_raw

    def _build_base_params(self, dataset: DatasetRef) -> dict[str, str]:
        """
        내부 헬퍼로서 build base params 처리를 담당한다.

        매개변수:
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.

        반환값:
            dict[str, str]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        api_key = self._require_api_key()
        service_key_param_raw = dataset.raw_metadata.get("service_key_param", "serviceKey")
        format_param_raw = dataset.raw_metadata.get("format_param", "type")
        service_key_param = (
            service_key_param_raw
            if isinstance(service_key_param_raw, str) and service_key_param_raw
            else "serviceKey"
        )
        format_param = (
            format_param_raw if isinstance(format_param_raw, str) and format_param_raw else "type"
        )
        return {service_key_param: api_key, format_param: "json"}

    def _request_and_decode(
        self, url: str, params: Mapping[str, object], dataset_id: str
    ) -> dict[str, object]:
        """
        내부 헬퍼로서 request and decode 처리를 담당한다.

        매개변수:
            url (str): 호출자가 제공하는 입력 값이다.
            params (Mapping[str, object]): 호출자가 제공하는 입력 값이다.
            dataset_id (str): 호출자가 제공하는 입력 값이다.

        반환값:
            dict[str, object]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        string_params = {key: str(value) for key, value in params.items()}
        response = self._transport.request(
            "GET",
            url,
            params=string_params,
            dataset_id=dataset_id,
            provider="localdata",
        )

        try:
            content_type = detect_content_type(response)
            if content_type == "json":
                decoded = decode_json(response.content)
            elif content_type == "xml":
                decoded = decode_xml(response.content)
            else:
                decoded = decode_json(response.content)
        except ParseError as exc:
            exc.provider = "localdata"
            logger.debug("Localdata response parsing failed", extra={"dataset_id": dataset_id})
            raise
        except ImportError as exc:
            raise ParseError("Failed to parse localdata response", provider="localdata") from exc

        if isinstance(decoded, dict):
            return cast(dict[str, object], decoded)

        logger.debug("Localdata decoded payload invalid type", extra={"dataset_id": dataset_id})
        raise ParseError("Decoded payload is not an object", provider="localdata")

    def _validate_envelope(
        self, payload: dict[str, object], dataset_id: str = ""
    ) -> tuple[dict[str, object], list[dict[str, object]]]:
        """
        내부 헬퍼로서 validate envelope 처리를 담당한다.

        매개변수:
            payload (dict[str, object]): 호출자가 제공하는 입력 값이다.
            dataset_id (str): 호출자가 제공하는 입력 값이다.

        반환값:
            tuple[dict[str, object], list[dict[str, object]]]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        response_obj = payload.get("response")
        if not isinstance(response_obj, dict):
            raise ProviderResponseError(
                "Malformed response envelope: missing response",
                provider="localdata",
                dataset_id=dataset_id or None,
            )

        response_dict = cast(dict[str, object], response_obj)

        header_obj = response_dict.get("header")
        if not isinstance(header_obj, dict):
            raise ProviderResponseError(
                "Malformed response envelope: missing header",
                provider="localdata",
                dataset_id=dataset_id or None,
            )

        header_dict = cast(dict[str, object], header_obj)
        result_code = header_dict.get("resultCode")
        if not isinstance(result_code, str):
            raise ProviderResponseError(
                "Malformed response envelope: missing resultCode",
                provider="localdata",
                dataset_id=dataset_id or None,
            )

        result_msg_raw = header_dict.get("resultMsg")
        result_msg = (
            result_msg_raw if isinstance(result_msg_raw, str) else "Provider returned error"
        )
        logger.debug(
            "localdata result",
            extra={"result_code": result_code, "result_msg": result_msg, "dataset_id": dataset_id},
        )
        if not _is_success_code(result_code):
            self._raise_for_result_code(result_code, result_msg, dataset_id)

        body_obj = response_dict.get("body")
        body_dict: dict[str, object] = (
            cast(dict[str, object], body_obj) if isinstance(body_obj, dict) else {}
        )
        items = self._normalize_items(body_dict.get("items"))
        return body_dict, items

    def _raise_for_result_code(self, code: str, msg: str, dataset_id: str) -> NoReturn:
        """
        내부 헬퍼로서 raise for result code 처리를 담당한다.

        매개변수:
            code (str): 호출자가 제공하는 입력 값이다.
            msg (str): 호출자가 제공하는 입력 값이다.
            dataset_id (str): 호출자가 제공하는 입력 값이다.

        반환값:
            NoReturn: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        if code in {"30", "31", "20", "32"}:
            raise AuthError(msg, provider="localdata", provider_code=code)
        if code == "22":
            raise RateLimitError(msg, provider="localdata", provider_code=code, retryable=False)
        if code == "10":
            raise InvalidRequestError(msg, provider="localdata", provider_code=code)
        if code == "12":
            raise DatasetNotFoundError(
                msg,
                provider="localdata",
                provider_code=code,
                dataset_id=dataset_id,
            )
        if code in {"01", "02"}:
            raise ServiceUnavailableError(msg, provider="localdata", provider_code=code)
        raise ProviderResponseError(msg, provider="localdata", provider_code=code)

    def _normalize_items(self, items_wrapper: object) -> list[dict[str, object]]:
        """
        내부 헬퍼로서 normalize items 처리를 담당한다.

        매개변수:
            items_wrapper (object): 호출자가 제공하는 입력 값이다.

        반환값:
            list[dict[str, object]]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        if items_wrapper is None:
            return []

        if isinstance(items_wrapper, dict):
            item_value = cast(dict[str, object], items_wrapper).get("item")
            if isinstance(item_value, list):
                normalized_items = cast(list[object], item_value)
                return [
                    cast(dict[str, object], item)
                    for item in normalized_items
                    if isinstance(item, dict)
                ]
            if isinstance(item_value, dict):
                return [cast(dict[str, object], item_value)]
            return []

        if isinstance(items_wrapper, list):
            normalized_items = cast(list[object], items_wrapper)
            return [
                cast(dict[str, object], item) for item in normalized_items if isinstance(item, dict)
            ]

        return []

    @staticmethod
    def _load_default_catalogue() -> tuple[DatasetRef, ...]:
        """
        내부 헬퍼로서 load default catalogue 처리를 담당한다.

        반환값:
            tuple[DatasetRef, ...]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return load_catalogue("kpubdata.providers.localdata", "localdata")


__all__ = ["LocaldataAdapter"]
