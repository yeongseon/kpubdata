"""KPubData Python 모듈.

이 파일은 ``src/kpubdata/providers/sgis/adapter.py`` 경로의 구현을 담는다.
주요 클래스와 함수는 공개 API, 전송 계층, Provider 어댑터 중 하나의 역할을 담당한다.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import NoReturn, Protocol, cast

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
from kpubdata.providers._common import build_schema_from_metadata, load_catalogue
from kpubdata.providers.sgis.auth import SgisAuthClient
from kpubdata.transport.decode import decode_json
from kpubdata.transport.http import HttpTransport, TransportConfig

_SGIS_PROVIDER = "sgis"
_BASE_URL = "https://sgisapi.kostat.go.kr/OpenAPI3"


class _AuthClient(Protocol):
    """
    _AuthClient 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``src/kpubdata/providers/sgis/adapter.py`` 모듈 안에서 _AuthClient의 상태와 동작을 함께 관리한다.
    주요 메서드: get_access_token, invalidate.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    def get_access_token(self, *, force_refresh: bool = False) -> str: ...

    def invalidate(self) -> None: ...


class SgisAdapter:
    """
    SgisAdapter 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``src/kpubdata/providers/sgis/adapter.py`` 모듈 안에서 SgisAdapter의 상태와 동작을 함께 관리한다.
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
        auth_client: _AuthClient | None = None,
    ) -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        매개변수:
            config (KPubDataConfig | None): 호출자가 제공하는 입력 값이다.
            transport (HttpTransport | None): 호출자가 제공하는 입력 값이다.
            catalogue (Sequence[DatasetRef] | None): 호출자가 제공하는 입력 값이다.
            auth_client (_AuthClient | None): 호출자가 제공하는 입력 값이다.

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
        self._auth: _AuthClient = auth_client or SgisAuthClient(
            config=self._config,
            transport=self._transport,
        )

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
        return _SGIS_PROVIDER

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
            f"Dataset not found: {_SGIS_PROVIDER}.{dataset_key}",
            provider=_SGIS_PROVIDER,
            dataset_id=f"{_SGIS_PROVIDER}.{dataset_key}",
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
        endpoint = self._dataset_endpoint(dataset)
        request_params = self._build_boundary_params(dataset, query.filters)
        payload = self._request_geojson(
            endpoint=endpoint, params=request_params, dataset_id=dataset.id
        )

        features_obj = payload.get("features")
        if not isinstance(features_obj, list):
            raise ProviderResponseError(
                "SGIS boundary response missing features list",
                provider=_SGIS_PROVIDER,
                dataset_id=dataset.id,
            )

        features = cast(list[object], features_obj)
        items = [
            self._normalize_feature(cast(dict[str, object], feature))
            for feature in features
            if isinstance(feature, dict)
        ]

        return RecordBatch(items=items, dataset=dataset, total_count=len(items), raw=payload)

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
        endpoint = self._resolve_raw_endpoint(dataset, operation)
        request_params: dict[str, str] = {}
        for key, value in params.items():
            request_params[key] = str(value)

        if "accessToken" not in request_params:
            request_params["accessToken"] = self._auth.get_access_token()

        return self._request_geojson(
            endpoint=endpoint, params=request_params, dataset_id=dataset.id
        )

    def _resolve_raw_endpoint(self, dataset: DatasetRef, operation: str) -> str:
        """
        내부 헬퍼로서 resolve raw endpoint 처리를 담당한다.

        매개변수:
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.
            operation (str): 호출자가 제공하는 입력 값이다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        if operation == "list":
            return self._dataset_endpoint(dataset)
        if operation.startswith("http://") or operation.startswith("https://"):
            raise InvalidRequestError(
                "SGIS call_raw operation must be an endpoint path, not a full URL",
                provider=_SGIS_PROVIDER,
                dataset_id=dataset.id,
                operation=operation,
            )
        return operation.lstrip("/")

    def _build_boundary_params(
        self, dataset: DatasetRef, filters: Mapping[str, object]
    ) -> dict[str, str]:
        """
        내부 헬퍼로서 build boundary params 처리를 담당한다.

        매개변수:
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.
            filters (Mapping[str, object]): 호출자가 제공하는 입력 값이다.

        반환값:
            dict[str, str]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        params: dict[str, str] = {
            "year": str(dataset.raw_metadata.get("default_year", "2023")),
        }
        adm_cd_default = dataset.raw_metadata.get("default_adm_cd")
        if isinstance(adm_cd_default, str):
            params["adm_cd"] = adm_cd_default

        low_search_default = dataset.raw_metadata.get("default_low_search")
        if isinstance(low_search_default, int):
            params["low_search"] = str(low_search_default)
        elif isinstance(low_search_default, str):
            params["low_search"] = low_search_default

        for key, value in filters.items():
            params[key] = str(value)

        params["accessToken"] = self._auth.get_access_token()
        return params

    def _request_geojson(
        self,
        *,
        endpoint: str,
        params: Mapping[str, str],
        dataset_id: str,
    ) -> dict[str, object]:
        """
        내부 헬퍼로서 request geojson 처리를 담당한다.

        매개변수:
            endpoint (str): 호출자가 제공하는 입력 값이다.
            params (Mapping[str, str]): 호출자가 제공하는 입력 값이다.
            dataset_id (str): 호출자가 제공하는 입력 값이다.

        반환값:
            dict[str, object]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        url = self._make_url(endpoint)
        response = self._transport.request(
            "GET",
            url,
            params=dict(params),
        )

        try:
            decoded = decode_json(response.content)
        except ParseError as exc:
            exc.provider = _SGIS_PROVIDER
            exc.dataset_id = dataset_id
            raise

        if not isinstance(decoded, dict):
            raise ProviderResponseError(
                "SGIS response must be a JSON object",
                provider=_SGIS_PROVIDER,
                dataset_id=dataset_id,
            )
        payload = cast(dict[str, object], decoded)

        try:
            self._raise_for_err_code(payload, dataset_id)
        except AuthError:
            self._auth.invalidate()
            refreshed = dict(params)
            refreshed["accessToken"] = self._auth.get_access_token(force_refresh=True)
            response_retry = self._transport.request(
                "GET",
                url,
                params=refreshed,
            )
            decoded_retry = decode_json(response_retry.content)
            if not isinstance(decoded_retry, dict):
                raise ProviderResponseError(
                    "SGIS response must be a JSON object",
                    provider=_SGIS_PROVIDER,
                    dataset_id=dataset_id,
                ) from None
            payload_retry = cast(dict[str, object], decoded_retry)
            self._raise_for_err_code(payload_retry, dataset_id)
            return payload_retry

        return payload

    def _normalize_feature(self, feature: Mapping[str, object]) -> dict[str, object]:
        """
        내부 헬퍼로서 normalize feature 처리를 담당한다.

        매개변수:
            feature (Mapping[str, object]): 호출자가 제공하는 입력 값이다.

        반환값:
            dict[str, object]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        properties_obj = feature.get("properties")
        properties = (
            cast(dict[str, object], properties_obj) if isinstance(properties_obj, dict) else {}
        )
        item: dict[str, object] = dict(properties)

        geometry_obj = feature.get("geometry")
        if isinstance(geometry_obj, dict):
            item["geometry"] = cast(dict[str, object], geometry_obj)

        feature_type = feature.get("type")
        if isinstance(feature_type, str):
            item["feature_type"] = feature_type
        return item

    def _raise_for_err_code(self, payload: Mapping[str, object], dataset_id: str) -> None:
        """
        내부 헬퍼로서 raise for err code 처리를 담당한다.

        매개변수:
            payload (Mapping[str, object]): 호출자가 제공하는 입력 값이다.
            dataset_id (str): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        err_code = _extract_err_code(payload)
        if err_code is None or err_code == 0:
            return

        message_obj = payload.get("errMsg")
        message = message_obj if isinstance(message_obj, str) and message_obj else "SGIS API error"
        self._raise_for_code(err_code, message, dataset_id)

    def _raise_for_code(self, err_code: int, message: str, dataset_id: str) -> NoReturn:
        """
        내부 헬퍼로서 raise for code 처리를 담당한다.

        매개변수:
            err_code (int): 호출자가 제공하는 입력 값이다.
            message (str): 호출자가 제공하는 입력 값이다.
            dataset_id (str): 호출자가 제공하는 입력 값이다.

        반환값:
            NoReturn: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        provider_code = str(err_code)
        if err_code in {-100}:
            raise ProviderResponseError(
                message,
                provider=_SGIS_PROVIDER,
                provider_code=provider_code,
                dataset_id=dataset_id,
            )
        if err_code in {-401, -402, -403}:
            raise AuthError(
                message,
                provider=_SGIS_PROVIDER,
                provider_code=provider_code,
                dataset_id=dataset_id,
            )
        if err_code in {-413, -414}:
            raise InvalidRequestError(
                message,
                provider=_SGIS_PROVIDER,
                provider_code=provider_code,
                dataset_id=dataset_id,
            )
        if err_code in {-429}:
            raise RateLimitError(
                message,
                provider=_SGIS_PROVIDER,
                provider_code=provider_code,
                dataset_id=dataset_id,
                retryable=False,
            )
        if err_code <= -500:
            raise ServiceUnavailableError(
                message,
                provider=_SGIS_PROVIDER,
                provider_code=provider_code,
                dataset_id=dataset_id,
            )
        raise ProviderResponseError(
            message,
            provider=_SGIS_PROVIDER,
            provider_code=provider_code,
            dataset_id=dataset_id,
        )

    def _dataset_endpoint(self, dataset: DatasetRef) -> str:
        """
        내부 헬퍼로서 dataset endpoint 처리를 담당한다.

        매개변수:
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        endpoint_obj = dataset.raw_metadata.get("endpoint")
        if isinstance(endpoint_obj, str) and endpoint_obj:
            return endpoint_obj
        raise ProviderResponseError(
            "Dataset metadata missing endpoint",
            provider=_SGIS_PROVIDER,
            dataset_id=dataset.id,
        )

    @staticmethod
    def _make_url(endpoint: str) -> str:
        """
        내부 헬퍼로서 make url 처리를 담당한다.

        매개변수:
            endpoint (str): 호출자가 제공하는 입력 값이다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return f"{_BASE_URL}/{endpoint.lstrip('/')}"

    @staticmethod
    def _load_default_catalogue() -> tuple[DatasetRef, ...]:
        """
        내부 헬퍼로서 load default catalogue 처리를 담당한다.

        반환값:
            tuple[DatasetRef, ...]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return load_catalogue("kpubdata.providers.sgis", _SGIS_PROVIDER)


def _extract_err_code(payload: Mapping[str, object]) -> int | None:
    """
    내부 헬퍼로서 extract err code 처리를 담당한다.

    매개변수:
        payload (Mapping[str, object]): 호출자가 제공하는 입력 값이다.

    반환값:
        int | None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    err_obj = payload.get("errCd")
    if isinstance(err_obj, int):
        return err_obj
    if isinstance(err_obj, str):
        try:
            return int(err_obj)
        except ValueError:
            return None
    return None


__all__ = ["SgisAdapter"]
