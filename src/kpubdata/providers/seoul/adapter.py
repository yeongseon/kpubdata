"""KPubData Python 모듈.

이 파일은 ``src/kpubdata/providers/seoul/adapter.py`` 경로의 구현을 담는다.
주요 클래스와 함수는 공개 API, 전송 계층, Provider 어댑터 중 하나의 역할을 담당한다.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import NoReturn, cast
from urllib.parse import quote

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.exceptions import (
    AuthError,
    DatasetNotFoundError,
    InvalidRequestError,
    ParseError,
    ProviderResponseError,
)
from kpubdata.providers._common import build_schema_from_metadata, coerce_int, load_catalogue
from kpubdata.transport.decode import decode_json
from kpubdata.transport.http import HttpTransport, TransportConfig

_SUCCESS_CODE = "INFO-000"
_EMPTY_CODE = "INFO-200"


class SeoulAdapter:
    """
    SeoulAdapter 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``src/kpubdata/providers/seoul/adapter.py`` 모듈 안에서 SeoulAdapter의 상태와 동작을 함께 관리한다.
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
        return "seoul"

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

        raise DatasetNotFoundError(
            f"Dataset not found: seoul.{dataset_key}",
            provider="seoul",
            dataset_id=f"seoul.{dataset_key}",
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
        page_no = query.page or 1
        page_size = query.page_size or 100
        self._validate_pagination(page_no, page_size, dataset.id)

        path_params = self._require_path_params(dataset, query.filters)
        start_index = (page_no - 1) * page_size + 1
        end_index = page_no * page_size
        url = self._build_request_url(
            dataset,
            operation=None,
            start_index=start_index,
            end_index=end_index,
            path_params=path_params,
        )

        payload = self._request_and_decode(url, dataset.id)
        service_name = self._service_name(dataset, operation=None)
        body, items = self._validate_envelope(payload, service_name, dataset.id)
        total_count = coerce_int(body.get("list_total_count"), 0)
        next_page = page_no + 1 if total_count > 0 and end_index < total_count else None

        return RecordBatch(
            items=items,
            dataset=dataset,
            total_count=total_count if total_count > 0 else None,
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
        page_no = self._int_param(params, "page_no", 1)
        page_size = self._int_param(params, "page_size", 100)
        self._validate_pagination(page_no, page_size, dataset.id)

        start_index = self._int_param(params, "start_index", 0)
        end_index = self._int_param(params, "end_index", 0)
        if start_index <= 0 or end_index <= 0:
            start_index = (page_no - 1) * page_size + 1
            end_index = page_no * page_size

        path_params = self._require_path_params(dataset, params)
        url = self._build_request_url(
            dataset,
            operation=operation,
            start_index=start_index,
            end_index=end_index,
            path_params=path_params,
        )
        payload = self._request_and_decode(url, dataset.id)
        _ = self._validate_envelope(
            payload, self._service_name(dataset, operation=operation), dataset.id
        )
        return payload

    def _validate_pagination(self, page_no: int, page_size: int, dataset_id: str) -> None:
        """
        내부 헬퍼로서 validate pagination 처리를 담당한다.

        매개변수:
            page_no (int): 호출자가 제공하는 입력 값이다.
            page_size (int): 호출자가 제공하는 입력 값이다.
            dataset_id (str): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        if page_no < 1:
            raise InvalidRequestError(
                "Seoul API page_no must be >= 1",
                provider="seoul",
                dataset_id=dataset_id,
            )
        if page_size < 1:
            raise InvalidRequestError(
                "Seoul API page_size must be >= 1",
                provider="seoul",
                dataset_id=dataset_id,
            )
        if page_size > 1000:
            raise InvalidRequestError(
                "Seoul API page_size must be <= 1000",
                provider="seoul",
                dataset_id=dataset_id,
            )

    def _require_api_key(self) -> str:
        """
        내부 헬퍼로서 require api key 처리를 담당한다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return self._config.require_provider_key("seoul")

    def _build_request_url(
        self,
        dataset: DatasetRef,
        *,
        operation: str | None,
        start_index: int,
        end_index: int,
        path_params: Mapping[str, str],
    ) -> str:
        """
        내부 헬퍼로서 build request url 처리를 담당한다.

        매개변수:
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.
            operation (str | None): 호출자가 제공하는 입력 값이다.
            start_index (int): 호출자가 제공하는 입력 값이다.
            end_index (int): 호출자가 제공하는 입력 값이다.
            path_params (Mapping[str, str]): 호출자가 제공하는 입력 값이다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        base_url = self._require_dataset_metadata(dataset, "base_url")
        service_name = self._service_name(dataset, operation=operation)
        path_suffix = "/".join(quote(value, safe="") for value in path_params.values())
        base_path = (
            f"{base_url}/{self._require_api_key()}/json/{service_name}/{start_index}/{end_index}"
        )
        if path_suffix:
            return f"{base_path}/{path_suffix}"
        return base_path

    def _service_name(self, dataset: DatasetRef, operation: str | None) -> str:
        """
        내부 헬퍼로서 service name 처리를 담당한다.

        매개변수:
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.
            operation (str | None): 호출자가 제공하는 입력 값이다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        if operation is not None and operation:
            return operation
        return self._require_dataset_metadata(dataset, "default_operation")

    def _envelope_key(
        self,
        payload: dict[str, object],
        service_name: str,
        dataset_id: str,
    ) -> str:
        """서울 API 응답에 사용할 envelope 키를 해석한다.

        일부 서울 API는 서비스 이름과 다른 envelope 키를 사용한다
        (예: bikeList -> rentBikeStatus). 카탈로그 항목에 ``envelope_key``
        메타데이터 필드가 있으면 이를 먼저 시도하고,
        하위 호환성을 위해 실패 시 *service_name*으로 되돌아간다.
        """
        # 명시적인 envelope_key override가 있는지 확인하기 위해 데이터셋을 조회한다.
        ds = self._datasets_by_key.get(dataset_id.removeprefix("seoul."))
        if ds is not None:
            override = ds.raw_metadata.get("envelope_key")
            if isinstance(override, str) and override and override in payload:
                return override
        # 기본값: 서비스 이름 자체를 사용한다.
        return service_name

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
        response = self._transport.request("GET", url, dataset_id=dataset_id, provider="seoul")

        try:
            decoded: object = decode_json(response.content)
        except ParseError as exc:
            exc.provider = "seoul"
            raise

        if isinstance(decoded, dict):
            return cast(dict[str, object], decoded)
        raise ParseError(
            "Decoded payload is not an object", provider="seoul", dataset_id=dataset_id
        )

    def _validate_envelope(
        self,
        payload: dict[str, object],
        service_name: str,
        dataset_id: str,
    ) -> tuple[dict[str, object], list[dict[str, object]]]:
        """
        내부 헬퍼로서 validate envelope 처리를 담당한다.

        매개변수:
            payload (dict[str, object]): 호출자가 제공하는 입력 값이다.
            service_name (str): 호출자가 제공하는 입력 값이다.
            dataset_id (str): 호출자가 제공하는 입력 값이다.

        반환값:
            tuple[dict[str, object], list[dict[str, object]]]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        # 최상위 오류 응답(envelope wrapper 없음)을 감지한다.
        # 일부 서울 API는 {"status": 500, "code": "ERROR-...", "message": "..."}를 반환한다.
        if "code" in payload and "message" in payload and service_name not in payload:
            code_raw = payload.get("code")
            message_raw = payload.get("message")
            code = code_raw if isinstance(code_raw, str) else "ERROR-UNKNOWN"
            message = message_raw if isinstance(message_raw, str) else "Provider returned error"
            self._raise_for_result_code(code, message, dataset_id)

        envelope_key = self._envelope_key(payload, service_name, dataset_id)
        body_obj = payload.get(envelope_key)
        if not isinstance(body_obj, dict):
            raise ProviderResponseError(
                f"Malformed response envelope: missing {envelope_key}",
                provider="seoul",
                dataset_id=dataset_id,
            )

        body = cast(dict[str, object], body_obj)
        result_obj = body.get("RESULT")
        if not isinstance(result_obj, dict):
            raise ProviderResponseError(
                "Malformed response envelope: missing RESULT",
                provider="seoul",
                dataset_id=dataset_id,
            )

        result = cast(dict[str, object], result_obj)
        code_raw = result.get("CODE")
        message_raw = result.get("MESSAGE")
        code = code_raw if isinstance(code_raw, str) else "ERROR-UNKNOWN"
        message = message_raw if isinstance(message_raw, str) else "Provider returned error"

        if code == _SUCCESS_CODE:
            return body, self._normalize_rows(body.get("row"))
        if code == _EMPTY_CODE:
            return body, []

        self._raise_for_result_code(code, message, dataset_id)

    def _raise_for_result_code(self, code: str, message: str, dataset_id: str) -> NoReturn:
        """
        내부 헬퍼로서 raise for result code 처리를 담당한다.

        매개변수:
            code (str): 호출자가 제공하는 입력 값이다.
            message (str): 호출자가 제공하는 입력 값이다.
            dataset_id (str): 호출자가 제공하는 입력 값이다.

        반환값:
            NoReturn: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        if code in {"INFO-100", "INFO-300"}:
            raise AuthError(message, provider="seoul", provider_code=code, dataset_id=dataset_id)
        if code in {"INFO-400", "ERROR-300", "ERROR-301", "ERROR-310", "ERROR-336"}:
            raise InvalidRequestError(
                message,
                provider="seoul",
                provider_code=code,
                dataset_id=dataset_id,
            )
        if code in {"INFO-500", "ERROR-500", "ERROR-600", "ERROR-601"}:
            raise ProviderResponseError(
                message,
                provider="seoul",
                provider_code=code,
                dataset_id=dataset_id,
            )
        raise ProviderResponseError(
            message,
            provider="seoul",
            provider_code=code,
            dataset_id=dataset_id,
        )

    def _require_path_params(
        self,
        dataset: DatasetRef,
        params: Mapping[str, object],
    ) -> dict[str, str]:
        """
        내부 헬퍼로서 require path params 처리를 담당한다.

        매개변수:
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.
            params (Mapping[str, object]): 호출자가 제공하는 입력 값이다.

        반환값:
            dict[str, str]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        resolved: dict[str, str] = {}
        for param_name in self._required_path_param_names(dataset):
            value = params.get(param_name)
            if isinstance(value, str) and value:
                resolved[param_name] = value
                continue
            raise InvalidRequestError(
                f"Seoul API requires path parameter '{param_name}'",
                provider="seoul",
                dataset_id=dataset.id,
            )
        return resolved

    def _required_path_param_names(self, dataset: DatasetRef) -> tuple[str, ...]:
        """
        내부 헬퍼로서 required path param names 처리를 담당한다.

        매개변수:
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.

        반환값:
            tuple[str, ...]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        raw = dataset.raw_metadata.get("required_path_params")
        if not isinstance(raw, list):
            raise ProviderResponseError(
                "Dataset metadata missing required_path_params",
                provider="seoul",
                dataset_id=dataset.id,
            )

        names: list[str] = []
        for value in cast(list[object], raw):
            if isinstance(value, str) and value:
                names.append(value)
        return tuple(names)

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
            provider="seoul",
            dataset_id=dataset.id,
        )

    def _normalize_rows(self, rows: object) -> list[dict[str, object]]:
        """
        내부 헬퍼로서 normalize rows 처리를 담당한다.

        매개변수:
            rows (object): 호출자가 제공하는 입력 값이다.

        반환값:
            list[dict[str, object]]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        if rows is None:
            return []
        if isinstance(rows, list):
            row_items = cast(list[object], rows)
            return [cast(dict[str, object], item) for item in row_items if isinstance(item, dict)]
        if isinstance(rows, dict):
            return [cast(dict[str, object], rows)]
        return []

    @staticmethod
    def _int_param(params: Mapping[str, object], key: str, default: int) -> int:
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
        coerced = coerce_int(params.get(key), default)
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
        return load_catalogue("kpubdata.providers.seoul", "seoul")


__all__ = ["SeoulAdapter"]
