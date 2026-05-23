"""KPubData Python 모듈.

이 파일은 ``src/kpubdata/providers/law/adapter.py`` 경로의 구현을 담는다.
주요 클래스와 함수는 공개 API, 전송 계층, Provider 어댑터 중 하나의 역할을 담당한다.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import cast
from urllib.parse import urlencode

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.exceptions import AuthError, DatasetNotFoundError, ParseError, ProviderResponseError
from kpubdata.providers._common import build_schema_from_metadata, coerce_int, load_catalogue
from kpubdata.transport.decode import decode_json
from kpubdata.transport.http import HttpTransport, TransportConfig

logger = logging.getLogger("kpubdata.provider.law")


class LawAdapter:
    """
    LawAdapter 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``src/kpubdata/providers/law/adapter.py`` 모듈 안에서 LawAdapter의 상태와 동작을 함께 관리한다.
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
        return "law"

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
            "Law dataset not found",
            extra={"dataset_id": f"law.{dataset_key}", "provider": "law"},
        )
        raise DatasetNotFoundError(
            f"Dataset not found: law.{dataset_key}",
            provider="law",
            dataset_id=f"law.{dataset_key}",
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
        page_size = query.page_size or self._default_page_size(dataset)
        logger.debug(
            "law query_records",
            extra={
                "dataset_id": dataset.id,
                "page": page,
                "page_size": page_size,
                "filter_keys": sorted(query.filters.keys()),
            },
        )

        url = self._build_request_url(dataset, params=query.filters, page=page, page_size=page_size)
        payload = self._request_and_decode(url, dataset.id)
        items = self._extract_items(payload, dataset)
        total_count = coerce_int(payload.get("totalCnt"), 0)

        if (total_count and page * page_size < total_count) or (
            not total_count and len(items) == page_size and page_size > 0
        ):
            next_page = page + 1
        else:
            next_page = None

        if not items:
            logger.debug(
                "Law envelope: zero items",
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
            next_page=next_page,
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
            "law call_raw",
            extra={
                "dataset_id": dataset.id,
                "operation": operation,
                "param_keys": sorted(params.keys()),
            },
        )
        raw_params = dict(params)
        page = self._int_param(raw_params, "page", 1)
        page_size = self._int_param(
            raw_params, "display", self._int_param(raw_params, "page_size", 100)
        )
        _ = raw_params.pop("page_size", None)

        url = self._build_request_url(
            dataset,
            operation=operation,
            params=raw_params,
            page=page,
            page_size=page_size,
        )
        return self._request_and_decode(url, dataset.id)

    def _require_api_key(self) -> str:
        """
        내부 헬퍼로서 require api key 처리를 담당한다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return self._config.require_provider_key("law")

    def _build_request_url(
        self,
        dataset: DatasetRef,
        *,
        params: Mapping[str, object] | None,
        page: int,
        page_size: int,
        operation: str | None = None,
    ) -> str:
        """
        내부 헬퍼로서 build request url 처리를 담당한다.

        매개변수:
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.
            params (Mapping[str, object] | None): 호출자가 제공하는 입력 값이다.
            page (int): 호출자가 제공하는 입력 값이다.
            page_size (int): 호출자가 제공하는 입력 값이다.
            operation (str | None): 호출자가 제공하는 입력 값이다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        base_url = self._require_dataset_metadata(dataset, "base_url")
        request_params: dict[str, str] = {
            "OC": self._require_api_key(),
            "target": self._require_dataset_metadata(dataset, "target"),
            "type": "JSON",
        }

        selected_operation = operation or self._default_operation(dataset)
        if selected_operation in {"lawSearch", "ordinSearch", "list"}:
            request_params["display"] = str(
                page_size if page_size > 0 else self._default_page_size(dataset)
            )
            request_params["page"] = str(page if page > 0 else 1)

        if params:
            for key, value in params.items():
                if value is None or key in {"OC", "target", "type", "display", "page", "page_size"}:
                    continue
                request_params[key] = str(value)

        return f"{base_url}?{urlencode(request_params)}"

    def _request_and_decode(self, url: str, dataset_id: str) -> dict[str, object]:
        """
        내부 헬퍼로서 request and decode 처리를 담당한다.

        매개변수:
            url (str): 호출자가 제공하는 입력 값이다.
            dataset_id (str): 호출자가 제공하는 입력 값이다.

        반환값:
            dict[str, object]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        response = self._transport.request("GET", url, dataset_id=dataset_id, provider="law")

        try:
            decoded_obj: object = decode_json(response.content)
        except ParseError as exc:
            exc.provider = "law"
            logger.debug("Law response parsing failed", extra={"dataset_id": dataset_id})
            raise

        if not isinstance(decoded_obj, dict):
            logger.debug("Law decoded payload invalid type", extra={"dataset_id": dataset_id})
            raise ParseError("Decoded payload is not an object", provider="law")

        payload = cast(dict[str, object], decoded_obj)
        self._raise_for_error_payload(payload, dataset_id)
        return payload

    def _extract_items(
        self, payload: dict[str, object], dataset: DatasetRef
    ) -> list[dict[str, object]]:
        """
        내부 헬퍼로서 extract items 처리를 담당한다.

        매개변수:
            payload (dict[str, object]): 호출자가 제공하는 입력 값이다.
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.

        반환값:
            list[dict[str, object]]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        item_key = self._require_dataset_metadata(dataset, "item_key")
        items_obj = payload.get(item_key)
        if items_obj is None:
            return []
        if isinstance(items_obj, list):
            items = cast(list[object], items_obj)
            return [cast(dict[str, object], item) for item in items if isinstance(item, dict)]
        if isinstance(items_obj, dict):
            return [cast(dict[str, object], items_obj)]
        raise ProviderResponseError(
            f"Malformed response envelope: invalid {item_key}",
            provider="law",
            dataset_id=dataset.id,
        )

    def _raise_for_error_payload(self, payload: Mapping[str, object], dataset_id: str) -> None:
        """
        내부 헬퍼로서 raise for error payload 처리를 담당한다.

        매개변수:
            payload (Mapping[str, object]): 호출자가 제공하는 입력 값이다.
            dataset_id (str): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        result_code = payload.get("resultCode")
        result_msg = payload.get("resultMsg") or payload.get("message") or payload.get("error")

        if isinstance(result_code, str) and result_code and result_code not in {"00", "OK"}:
            self._raise_provider_error(result_code, result_msg, dataset_id)

        if isinstance(result_msg, str):
            lowered = result_msg.casefold()
            if "인증" in result_msg or "oc" in lowered or "api key" in lowered:
                self._raise_provider_error("AUTH", result_msg, dataset_id)

    def _raise_provider_error(self, code: str, message: object, dataset_id: str) -> None:
        """
        내부 헬퍼로서 raise provider error 처리를 담당한다.

        매개변수:
            code (str): 호출자가 제공하는 입력 값이다.
            message (object): 호출자가 제공하는 입력 값이다.
            dataset_id (str): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        resolved_message = (
            message if isinstance(message, str) and message else "Provider returned error"
        )
        lowered = resolved_message.casefold()
        if "인증" in resolved_message or "oc" in lowered or "api key" in lowered:
            raise AuthError(
                resolved_message,
                provider="law",
                provider_code=code,
                dataset_id=dataset_id or None,
            )
        raise ProviderResponseError(
            resolved_message,
            provider="law",
            provider_code=code,
            dataset_id=dataset_id or None,
        )

    def _require_dataset_metadata(self, dataset: DatasetRef, key: str) -> str:
        """
        내부 헬퍼로서 require dataset metadata 처리를 담당한다.

        매개변수:
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.
            key (str): 호출자가 제공하는 입력 값이다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        value = dataset.raw_metadata.get(key)
        if isinstance(value, str) and value:
            return value
        raise ProviderResponseError(
            f"Dataset metadata missing {key}",
            provider="law",
            dataset_id=dataset.id,
        )

    def _default_operation(self, dataset: DatasetRef) -> str:
        """
        내부 헬퍼로서 default operation 처리를 담당한다.

        매개변수:
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return self._require_dataset_metadata(dataset, "default_operation")

    def _default_page_size(self, dataset: DatasetRef) -> int:
        """
        내부 헬퍼로서 default page size 처리를 담당한다.

        매개변수:
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.

        반환값:
            int: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        max_page_size = (
            dataset.query_support.max_page_size if dataset.query_support is not None else None
        )
        return max_page_size or 100

    @classmethod
    def _int_param(cls, params: Mapping[str, object], key: str, default: int) -> int:
        """
        내부 헬퍼로서 int param 처리를 담당한다.

        매개변수:
            params (Mapping[str, object]): 호출자가 제공하는 입력 값이다.
            key (str): 호출자가 제공하는 입력 값이다.
            default (int): 호출자가 제공하는 입력 값이다.

        반환값:
            int: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        value = params.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            coerced = coerce_int(value, default)
            return coerced if coerced > 0 else default
        return default

    @staticmethod
    def _load_default_catalogue() -> tuple[DatasetRef, ...]:
        """
        내부 헬퍼로서 load default catalogue 처리를 담당한다.

        반환값:
            tuple[DatasetRef, ...]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return load_catalogue("kpubdata.providers.law", "law")
