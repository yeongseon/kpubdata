"""KPubData Python 모듈.

이 파일은 ``src/kpubdata/providers/lofin/adapter.py`` 경로의 구현을 담는다.
주요 클래스와 함수는 공개 API, 전송 계층, Provider 어댑터 중 하나의 역할을 담당한다.
"""

from __future__ import annotations

import logging
import ssl
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
from kpubdata.transport.http import HttpTransport, TransportConfig, TransportRequirements

logger = logging.getLogger("kpubdata.provider.lofin")


def _lofin_ssl_context() -> ssl.SSLContext:
    """LOFIN 서버와 호환되는 SSL 컨텍스트를 생성한다.

    LOFIN 서버(www.lofin365.go.kr)는 TLSv1.2와 AES256-SHA256을 사용하며,
    OpenSSL 3.x에서는 완화된 보안 수준이 필요하다.
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.set_ciphers("DEFAULT:@SECLEVEL=1")
    return ctx


class LofinAdapter:
    """
    LofinAdapter 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``src/kpubdata/providers/lofin/adapter.py`` 모듈 안에서 LofinAdapter의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__, name, list_datasets, search_datasets, get_dataset.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    requires_api_key: bool = True

    transport_requirements: TransportRequirements = TransportRequirements(
        ssl_context_factory=_lofin_ssl_context,
    )

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
        if transport is not None:
            self._transport: HttpTransport = transport
        else:
            ssl_ctx = _lofin_ssl_context()
            transport_config = TransportConfig(
                timeout=self._config.timeout,
                max_retries=self._config.max_retries,
                ssl_context=ssl_ctx,
            )
            self._transport = HttpTransport(transport_config)

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
        return "lofin"

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
            "LOFIN dataset not found",
            extra={"dataset_id": f"lofin.{dataset_key}", "provider": "lofin"},
        )
        raise DatasetNotFoundError(
            f"Dataset not found: lofin.{dataset_key}",
            provider="lofin",
            dataset_id=f"lofin.{dataset_key}",
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
            "lofin query_records",
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

        body, items = self._validate_envelope(payload, dataset)

        total_count = coerce_int(body.get("list_total_count"), 0)
        if (total_count and page * page_size < total_count) or (
            not total_count and len(items) == page_size
        ):
            computed_next = page + 1
        else:
            computed_next = None

        if not items:
            logger.debug(
                "LOFIN envelope: zero items",
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
        _ = operation
        logger.debug(
            "lofin call_raw",
            extra={
                "dataset_id": dataset.id,
                "operation": operation,
                "param_keys": sorted(params.keys()),
            },
        )
        page = self._int_param(params, "pIndex", self._int_param(params, "page", 1))
        page_size = self._int_param(params, "pSize", self._int_param(params, "page_size", 100))
        extra_keys = {"pIndex", "page", "pSize", "page_size"}
        filters = {k: v for k, v in params.items() if k not in extra_keys}

        url = self._build_request_url(dataset, page=page, page_size=page_size, filters=filters)
        payload = self._request_and_decode(url, dataset.id)
        _ = self._validate_envelope(payload, dataset)
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

    def _build_request_url(
        self,
        dataset: DatasetRef,
        *,
        page: int,
        page_size: int,
        filters: dict[str, object] | None = None,
    ) -> str:
        """
        내부 헬퍼로서 build request url 처리를 담당한다.

        매개변수:
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.
            page (int): 호출자가 제공하는 입력 값이다.
            page_size (int): 호출자가 제공하는 입력 값이다.
            filters (dict[str, object] | None): 호출자가 제공하는 입력 값이다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        base_url_raw = dataset.raw_metadata.get("base_url")
        if not isinstance(base_url_raw, str) or not base_url_raw:
            logger.debug(
                "LOFIN dataset metadata missing base_url",
                extra={"dataset_id": dataset.id},
            )
            raise ProviderResponseError(
                "Dataset metadata missing base_url",
                provider="lofin",
                dataset_id=dataset.id,
            )

        dataset_code = self._require_dataset_metadata(dataset, "api_code")
        api_key = self._require_api_key()
        safe_page = page if page > 0 else 1
        safe_page_size = page_size if page_size > 0 else 100
        url = (
            f"{base_url_raw}/{dataset_code}"
            f"?Key={api_key}&Type=json&pIndex={safe_page}&pSize={safe_page_size}"
        )
        if filters:
            for key, value in filters.items():
                url += f"&{key}={value}"
        return url

    def _request_and_decode(self, url: str, dataset_id: str = "") -> dict[str, object]:
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
        response = self._transport.request("GET", url, dataset_id=dataset_id, provider="lofin")

        try:
            decoded_obj: object = decode_json(response.content)
        except ValueError as exc:
            logger.debug("LOFIN response parsing failed", extra={"dataset_id": dataset_id})
            raise ParseError("Failed to parse LOFIN response", provider="lofin") from exc

        if isinstance(decoded_obj, dict):
            payload = cast(dict[str, object], decoded_obj)
            self._raise_for_top_level_result(payload, dataset_id)
            return payload

        logger.debug("LOFIN decoded payload invalid type", extra={"dataset_id": dataset_id})
        raise ParseError("Decoded payload is not an object", provider="lofin")

    def _validate_envelope(
        self, payload: dict[str, object], dataset: DatasetRef
    ) -> tuple[dict[str, object], list[dict[str, object]]]:
        """
        내부 헬퍼로서 validate envelope 처리를 담당한다.

        매개변수:
            payload (dict[str, object]): 호출자가 제공하는 입력 값이다.
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.

        반환값:
            tuple[dict[str, object], list[dict[str, object]]]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        dataset_code = self._require_dataset_metadata(dataset, "api_code")
        body_obj = payload.get(dataset_code)
        if not isinstance(body_obj, list) or not body_obj:
            raise ProviderResponseError(
                f"Malformed response envelope: missing {dataset_code}",
                provider="lofin",
                dataset_id=dataset.id,
            )

        body_list = cast(list[object], body_obj)
        first_entry = body_list[0]
        if not isinstance(first_entry, dict):
            raise ProviderResponseError(
                f"Malformed response envelope: invalid {dataset_code} body",
                provider="lofin",
                dataset_id=dataset.id,
            )

        head_entry = cast(dict[str, object], first_entry)
        head_obj = head_entry.get("head")
        if not isinstance(head_obj, list) or not head_obj:
            legacy_body = cast(dict[str, object], first_entry)
            self._raise_for_result(legacy_body, dataset.id)
            items = self._normalize_rows(legacy_body.get("row"))
            return legacy_body, items

        head_items = cast(list[object], head_obj)
        metadata: dict[str, object] = {}
        result_payload: Mapping[str, object] | None = None
        for head_item in head_items:
            if not isinstance(head_item, dict):
                continue
            head_dict = cast(dict[str, object], head_item)
            if "list_total_count" in head_dict:
                metadata["list_total_count"] = head_dict.get("list_total_count")
            if "RESULT" in head_dict:
                result_obj = head_dict.get("RESULT")
                if isinstance(result_obj, Mapping):
                    result_payload = cast(Mapping[str, object], result_obj)

        if result_payload is None:
            raise ProviderResponseError(
                f"Malformed response envelope: missing {dataset_code} RESULT",
                provider="lofin",
                dataset_id=dataset.id,
            )

        self._raise_for_result({"RESULT": dict(result_payload)}, dataset.id)

        rows_entry = body_list[1] if len(body_list) > 1 else None
        rows_wrapper: object = None
        if isinstance(rows_entry, dict):
            rows_dict = cast(dict[str, object], rows_entry)
            rows_wrapper = rows_dict.get("row")

        items = self._normalize_rows(rows_wrapper)
        return metadata, items

    def _raise_for_top_level_result(self, payload: Mapping[str, object], dataset_id: str) -> None:
        """
        내부 헬퍼로서 raise for top level result 처리를 담당한다.

        매개변수:
            payload (Mapping[str, object]): 호출자가 제공하는 입력 값이다.
            dataset_id (str): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        result_obj = payload.get("RESULT")
        if not isinstance(result_obj, list):
            return

        result_list = cast(list[object], result_obj)
        if not result_list:
            return

        first_result = result_list[0]
        if not isinstance(first_result, Mapping):
            return

        self._raise_for_result(
            {"RESULT": dict(cast(Mapping[str, object], first_result))}, dataset_id
        )

    def _raise_for_result(self, payload: Mapping[str, object], dataset_id: str) -> None:
        """
        내부 헬퍼로서 raise for result 처리를 담당한다.

        매개변수:
            payload (Mapping[str, object]): 호출자가 제공하는 입력 값이다.
            dataset_id (str): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        result_obj = payload.get("RESULT")
        if not isinstance(result_obj, dict):
            return

        result_dict = cast(dict[str, object], result_obj)
        code_raw = result_dict.get("CODE")
        message_raw = result_dict.get("MESSAGE")
        code = code_raw if isinstance(code_raw, str) else "ERROR-000"
        message = message_raw if isinstance(message_raw, str) else "Provider returned error"
        logger.debug(
            "LOFIN result",
            extra={"result_code": code, "result_msg": message, "dataset_id": dataset_id},
        )

        if code == "INFO-000":
            return
        if code == "INFO-200":
            return

        self._raise_for_result_code(code, message, dataset_id)

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
        if code in {"ERROR-290", "ERROR-300"}:
            raise AuthError(
                msg, provider="lofin", provider_code=code, dataset_id=dataset_id or None
            )
        if code.startswith("ERROR-"):
            raise ProviderResponseError(
                msg,
                provider="lofin",
                provider_code=code,
                dataset_id=dataset_id or None,
            )
        raise ProviderResponseError(
            msg,
            provider="lofin",
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
            provider="lofin",
            dataset_id=dataset.id,
        )

    def _normalize_rows(self, rows_wrapper: object) -> list[dict[str, object]]:
        """
        내부 헬퍼로서 normalize rows 처리를 담당한다.

        매개변수:
            rows_wrapper (object): 호출자가 제공하는 입력 값이다.

        반환값:
            list[dict[str, object]]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
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
        coerced = coerce_int(value, default)
        return coerced if coerced > 0 else default

    @staticmethod
    def _load_default_catalogue() -> tuple[DatasetRef, ...]:
        """
        내부 헬퍼로서 load default catalogue 처리를 담당한다.

        반환값:
            tuple[DatasetRef, ...]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return load_catalogue("kpubdata.providers.lofin", "lofin")


__all__ = ["LofinAdapter"]
