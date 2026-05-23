"""선별된 데이터셋 카탈로그를 포함한 data.go.kr 어댑터."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import NoReturn, cast
from urllib.parse import urlparse

import httpx

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
    TransportError,
)
from kpubdata.providers._common import build_schema_from_metadata, coerce_int, load_catalogue
from kpubdata.transport.decode import decode_json, decode_xml, detect_content_type
from kpubdata.transport.http import HttpTransport, TransportConfig

logger = logging.getLogger("kpubdata.provider.datago")

_DATAGO_403_HINT = (
    "data.go.kr returned 403. This usually means the specific API has not been activated "
    "(활용신청) for your key. Visit the dataset's page on https://www.data.go.kr and "
    "click '활용신청'. Approval is usually automatic and becomes active within a few minutes."
)


def _is_success_code(code: str) -> bool:
    """성공을 나타내는 모든 data.go.kr resultCode에 대해 True를 반환한다.

    서로 다른 엔드포인트 계열은 "오류 없음" 코드를 다른 자릿수로 사용한다:
    "00"(대부분의 API)와 "000"(apis.data.go.kr/1613000 하위 RTMS 계열)이다.
    둘 다, 그리고 0 값을 나타내는 모든 숫자 변형은 성공으로 처리해야 한다.
    """
    try:
        return int(code) == 0
    except ValueError:
        return False


class DataGoAdapter:
    """data.go.kr(공공데이터포털)용 어댑터.

    apis.data.go.kr 엔드포인트 계열에서 지원하는 데이터셋의 선별된 카탈로그를 제공한다.
    """

    requires_api_key: bool = True

    def __init__(
        self,
        *,
        config: KPubDataConfig | None = None,
        transport: HttpTransport | None = None,
        catalogue: Sequence[DatasetRef] | None = None,
    ) -> None:
        """인스턴스가 사용할 내부 상태를 초기화한다."""
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
        """정규 Provider 키를 반환한다."""

        return "datago"

    def list_datasets(self) -> list[DatasetRef]:
        """data.go.kr에서 사용 가능한 데이터셋 목록을 반환한다."""

        return list(self._datasets)

    def search_datasets(self, text: str) -> list[DatasetRef]:
        """data.go.kr에서 사용 가능한 데이터셋을 검색한다."""

        needle = text.casefold()
        return [
            dataset
            for dataset in self._datasets
            if needle in dataset.id.casefold() or needle in dataset.name.casefold()
        ]

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        """data.go.kr용 Provider 로컬 데이터셋 키를 해석한다."""

        dataset = self._datasets_by_key.get(dataset_key)
        if dataset is not None:
            return dataset

        logger.debug(
            "Datago dataset not found",
            extra={"dataset_id": f"datago.{dataset_key}", "provider": "datago"},
        )
        raise DatasetNotFoundError(
            f"Dataset not found: datago.{dataset_key}",
            provider="datago",
            dataset_id=f"datago.{dataset_key}",
        )

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        """data.go.kr 데이터셋에서 레코드를 조회한다."""

        if self._is_generic(dataset):
            logger.debug(
                "Datago list called with unsupported operation (generic)",
                extra={"dataset_id": dataset.id},
            )
            raise InvalidRequestError(
                "datago.generic does not support list(); use call_raw with _base_url instead",
                provider="datago",
                dataset_id=dataset.id,
            )

        page = query.page or 1
        page_size = query.page_size or 100
        is_odcloud = self._is_odcloud(dataset)
        logger.debug(
            "datago query_records",
            extra={
                "dataset_id": dataset.id,
                "page": page,
                "page_size": page_size,
                "filter_keys": sorted(query.filters.keys()),
            },
        )

        url = self._build_request_url(dataset)
        params = self._build_base_params(dataset)
        page_param = "pageNo"
        page_size_param = "numOfRows"
        if is_odcloud:
            # odcloud 계열은 pageNo/numOfRows 대신 메타데이터에 정의된 페이지 파라미터 이름을 쓴다.
            pagination_params = dataset.raw_metadata.get("pagination_params")
            if isinstance(pagination_params, Mapping):
                pagination_params_dict = cast(Mapping[str, object], pagination_params)
                page_param_raw = pagination_params_dict.get("page")
                page_size_param_raw = pagination_params_dict.get("page_size")
                if isinstance(page_param_raw, str) and page_param_raw:
                    page_param = page_param_raw
                if isinstance(page_size_param_raw, str) and page_size_param_raw:
                    page_size_param = page_size_param_raw

        params[page_param] = str(page)
        params[page_size_param] = str(page_size)

        reserved = {params_key.lower() for params_key in params}
        reserved.update({page_param.lower(), page_size_param.lower()})
        for key, raw_value in query.filters.items():
            # 인증키·포맷·페이지 파라미터는 이미 채웠으므로 사용자 필터로 덮어쓰지 않는다.
            if key.lower() not in reserved:
                value: object = raw_value
                params[key] = str(value)

        payload = self._request_and_decode(url, params, dataset.id)
        if is_odcloud:
            body, items = self._parse_odcloud_response(payload, dataset)
        else:
            body, items = self._validate_envelope(payload, dataset)

        total_count = coerce_int(body.get("totalCount"), 0)
        if (total_count and page * page_size < total_count) or (
            not total_count and len(items) == page_size
        ):
            # totalCount가 없을 때는 현재 페이지가 꽉 찼는지를 다음 페이지 존재 신호로 사용한다.
            computed_next = page + 1
        else:
            computed_next = None

        if not items:
            logger.debug(
                "Datago envelope: zero items",
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
        """data.go.kr 데이터셋의 스키마 메타데이터를 반환한다.

        가능하면 선별된 카탈로그 메타데이터에서 스키마를 반환한다.
        data.go.kr에는 실시간 스키마 탐색 엔드포인트가 없으므로, 카탈로그에
        명시적으로 선별된 필드 정의가 없는 데이터셋은 ``None``을 반환한다.
        """
        return build_schema_from_metadata(dataset)

    def call_raw(self, dataset: DatasetRef, operation: str, params: dict[str, object]) -> object:
        """data.go.kr 고유 API 작업을 호출한다.

        ``datago.generic``는 선별된 카탈로그에 없는 data.go.kr 엔드포인트를 위한
        raw 전용 비상구다. 정규화, 페이지네이션, 스키마 처리 없이 디코딩된 원시
        응답(dict)을 그대로 반환한다. 호출자는 다음을 전달해야 한다:
          * ``_base_url`` (str, 필수): 작업 이름을 제외한 엔드포인트 기본 URL.
          * ``_envelope`` (bool, 기본값 True): True이면 표준
            ``response.header.resultCode`` 엔벌로프를 검증한다. 실제 bool 값이어야 하며
            문자열/정수는 허용되지 않는다.
          * ``_service_key_param`` (str): service key 파라미터 이름을 재정의한다.
          * ``_format_param`` (str): 응답 형식 파라미터 이름을 재정의한다.

        ``_base_url``이 ``*.data.go.kr`` 호스트를 가리키지 않으면 경고를 기록한다.
        호출은 계속 진행되며, 이는 완화된 점검이다.
        """

        logger.debug(
            "datago call_raw",
            extra={
                "dataset_id": dataset.id,
                "operation": operation,
                "param_keys": sorted(params.keys()),
            },
        )

        is_generic = self._is_generic(dataset)
        if is_generic:
            base_url_override = params.get("_base_url")
            if not isinstance(base_url_override, str) or not base_url_override:
                logger.debug(
                    "Datago.generic missing _base_url in call_raw params",
                    extra={"dataset_id": dataset.id},
                )
                raise InvalidRequestError(
                    "datago.generic requires '_base_url' to be passed in params",
                    provider="datago",
                    dataset_id=dataset.id,
                )
            envelope_flag = params.get("_envelope", True)
            if not isinstance(envelope_flag, bool):
                logger.debug(
                    "Datago.generic '_envelope' must be a bool",
                    extra={"dataset_id": dataset.id},
                )
                raise InvalidRequestError(
                    "datago.generic '_envelope' must be a bool (True or False)",
                    provider="datago",
                    dataset_id=dataset.id,
                )
            validate_envelope = envelope_flag
            service_key_param_override = params.get("_service_key_param")
            format_param_override = params.get("_format_param")

            host = urlparse(base_url_override).hostname or ""
            if not host.endswith(".data.go.kr") and host != "data.go.kr":
                logger.warning(
                    "datago.generic called with non-data.go.kr host",
                    extra={
                        "dataset_id": dataset.id,
                        "operation": operation,
                        "base_url": base_url_override,
                        "host": host,
                    },
                )

            url = f"{base_url_override.rstrip('/')}/{operation}"
            logger.debug(
                "datago.generic dispatch",
                extra={
                    "dataset_id": dataset.id,
                    "operation": operation,
                    "base_url": base_url_override,
                    "envelope": validate_envelope,
                },
            )
            request_params = self._build_base_params(
                dataset,
                service_key_param_override=(
                    service_key_param_override
                    if isinstance(service_key_param_override, str)
                    else None
                ),
                format_param_override=(
                    format_param_override if isinstance(format_param_override, str) else None
                ),
            )
            service_key_param = (
                service_key_param_override
                if isinstance(service_key_param_override, str) and service_key_param_override
                else str(dataset.raw_metadata.get("service_key_param", "serviceKey"))
            )
            # 제어용 magic key는 소비하고, 실제 Provider 파라미터만 원격 엔드포인트로 전달한다.
            magic_keys = {
                "_base_url",
                "_envelope",
                "_service_key_param",
                "_format_param",
            }
            for key, value in params.items():
                if key in magic_keys or key == service_key_param:
                    continue
                request_params[key] = str(value)

            payload = self._request_and_decode(url, request_params, dataset.id)
            if validate_envelope:
                _ = self._validate_envelope(payload, dataset)
            return payload

        url = self._build_request_url(dataset, operation)
        request_params = self._build_base_params(dataset)

        service_key_param = str(dataset.raw_metadata.get("service_key_param", "serviceKey"))
        for key, value in params.items():
            if key != service_key_param:
                request_params[key] = str(value)

        payload = self._request_and_decode(url, request_params, dataset.id)
        if self._is_odcloud(dataset):
            return payload

        _ = self._validate_envelope(payload, dataset)
        return payload

    @staticmethod
    def _is_generic(dataset: DatasetRef) -> bool:
        """데이터셋이 datago.generic 비상구인지 반환한다."""
        return bool(dataset.raw_metadata.get("generic"))

    @staticmethod
    def _is_odcloud(dataset: DatasetRef) -> bool:
        """데이터셋이 odcloud 계열 응답 형식을 쓰는지 반환한다."""
        return dataset.raw_metadata.get("provider_family") == "odcloud"

    def _require_api_key(self) -> str:
        """data.go.kr 호출에 사용할 API 키를 설정에서 읽는다."""
        return self._config.require_provider_key("datago")

    def _build_request_url(self, dataset: DatasetRef, operation: str | None = None) -> str:
        """데이터셋 메타데이터와 operation 값으로 호출 URL을 구성한다."""
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

    def _build_base_params(
        self,
        dataset: DatasetRef,
        *,
        service_key_param_override: str | None = None,
        format_param_override: str | None = None,
    ) -> dict[str, str]:
        """서비스 키와 응답 형식 파라미터를 포함한 기본 쿼리를 만든다."""
        api_key = self._require_api_key()
        service_key_param_raw = (
            service_key_param_override
            if service_key_param_override
            else dataset.raw_metadata.get("service_key_param", "serviceKey")
        )
        format_param_raw = (
            format_param_override
            if format_param_override
            else dataset.raw_metadata.get("format_param", "resultType")
        )
        service_key_param = (
            service_key_param_raw
            if isinstance(service_key_param_raw, str) and service_key_param_raw
            else "serviceKey"
        )
        params: dict[str, str] = {service_key_param: api_key}

        if not self._is_odcloud(dataset):
            format_param = (
                format_param_raw
                if isinstance(format_param_raw, str) and format_param_raw
                else "resultType"
            )
            params[format_param] = "json"

        return params

    def _request_and_decode(
        self, url: str, params: Mapping[str, object], dataset_id: str = ""
    ) -> dict[str, object]:
        """data.go.kr API를 호출하고 응답 본문을 dict로 디코딩한다."""
        string_params = {key: str(value) for key, value in params.items()}
        try:
            response = self._transport.request(
                "GET",
                url,
                params=string_params,
                dataset_id=dataset_id,
                provider="datago",
            )
        except TransportError as exc:
            if self._is_http_403(exc):
                raise AuthError(
                    _DATAGO_403_HINT,
                    provider="datago",
                    dataset_id=dataset_id or None,
                    status_code=403,
                ) from exc
            raise

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
            logger.debug("Datago response parsing failed", extra={"dataset_id": dataset_id})
            raise
        except ImportError as exc:
            raise ParseError("Failed to parse data.go.kr response", provider="datago") from exc

        if isinstance(decoded, dict):
            return cast(dict[str, object], decoded)

        logger.debug(
            "Datago decoded payload invalid type",
            extra={"dataset_id": dataset_id},
        )
        raise ParseError("Decoded payload is not an object", provider="datago")

    @staticmethod
    def _is_http_403(exc: TransportError) -> bool:
        """TransportError의 원인이 HTTP 403 응답인지 확인한다."""
        cause = exc.__cause__
        return isinstance(cause, httpx.HTTPStatusError) and cause.response.status_code == 403

    def _validate_envelope(
        self, payload: dict[str, object], dataset: DatasetRef | None = None
    ) -> tuple[dict[str, object], list[dict[str, object]]]:
        """데이터셋 유형에 맞는 엔벌로프 검증 함수를 선택해 body/items를 추출한다."""
        dataset_id = dataset.id if dataset is not None else ""
        envelope_style = dataset.raw_metadata.get("envelope_style") if dataset is not None else None

        if envelope_style == "its_flat":
            return self._validate_its_flat_envelope(payload, dataset_id)

        response_obj = payload.get("response")
        if not isinstance(response_obj, dict):
            logger.debug(
                "Datago envelope missing response/body",
                extra={"dataset_id": dataset_id},
            )
            raise ProviderResponseError(
                "Malformed response envelope: missing response",
                provider="datago",
                dataset_id=dataset_id or None,
            )

        response_dict = cast(dict[str, object], response_obj)

        if envelope_style == "gyeonggi_msg":
            return self._validate_gyeonggi_msg_envelope(response_dict, dataset_id)
        return self._validate_standard_envelope(response_dict, dataset_id)

    def _validate_its_flat_envelope(
        self, payload: dict[str, object], dataset_id: str
    ) -> tuple[dict[str, object], list[dict[str, object]]]:
        """ITS 평면 응답에서 resultCode와 items 목록을 검증한다."""
        result_code = self._coerce_result_code(payload.get("resultCode"), dataset_id)
        result_msg_raw = payload.get("resultMsg")
        result_msg = (
            result_msg_raw if isinstance(result_msg_raw, str) else "Provider returned error"
        )
        logger.debug(
            "data.go.kr result",
            extra={"result_code": result_code, "result_msg": result_msg, "dataset_id": dataset_id},
        )
        if not _is_success_code(result_code):
            self._raise_for_result_code(result_code, result_msg, dataset_id)

        items = self._normalize_items(payload.get("items"))
        return payload, items

    def _parse_odcloud_response(
        self, payload: dict[str, object], dataset: DatasetRef
    ) -> tuple[dict[str, object], list[dict[str, object]]]:
        """odcloud 응답의 data 배열을 레코드 목록으로 정리한다."""
        data_obj = payload.get("data")
        if data_obj is None:
            return payload, []

        if not isinstance(data_obj, list):
            raise ProviderResponseError(
                "Malformed odcloud response: data must be an array",
                provider="datago",
                dataset_id=dataset.id,
            )

        normalized_items = cast(list[object], data_obj)
        items = [
            cast(dict[str, object], item) for item in normalized_items if isinstance(item, dict)
        ]
        return payload, items

    def _validate_standard_envelope(
        self, response_dict: dict[str, object], dataset_id: str
    ) -> tuple[dict[str, object], list[dict[str, object]]]:
        """표준 data.go.kr response.header/body 구조를 검증한다."""
        header_obj = response_dict.get("header")
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
        if not _is_success_code(result_code):
            self._raise_for_result_code(result_code, result_msg, dataset_id)

        body_obj = response_dict.get("body")
        body_dict: dict[str, object] = (
            cast(dict[str, object], body_obj) if isinstance(body_obj, dict) else {}
        )
        items = self._normalize_items(body_dict.get("items"))
        return body_dict, items

    def _validate_gyeonggi_msg_envelope(
        self, response_dict: dict[str, object], dataset_id: str
    ) -> tuple[dict[str, object], list[dict[str, object]]]:
        """경기형 msgHeader/msgBody 응답 구조를 검증한다."""
        header_obj = response_dict.get("msgHeader")
        if not isinstance(header_obj, dict):
            raise ProviderResponseError(
                "Malformed response envelope: missing msgHeader",
                provider="datago",
                dataset_id=dataset_id or None,
            )

        header_dict = cast(dict[str, object], header_obj)
        result_code = self._coerce_result_code(header_dict.get("resultCode"), dataset_id)
        result_msg_raw = header_dict.get("resultMessage")
        result_msg = (
            result_msg_raw if isinstance(result_msg_raw, str) else "Provider returned error"
        )
        logger.debug(
            "data.go.kr result",
            extra={"result_code": result_code, "result_msg": result_msg, "dataset_id": dataset_id},
        )
        if not _is_success_code(result_code):
            self._raise_for_result_code(result_code, result_msg, dataset_id)

        body_obj = response_dict.get("msgBody")
        body_dict: dict[str, object] = (
            cast(dict[str, object], body_obj) if isinstance(body_obj, dict) else {}
        )
        items_wrapper = self._extract_gyeonggi_msg_items_wrapper(body_dict)
        items = self._normalize_items(items_wrapper)
        return body_dict, items

    def _coerce_result_code(self, result_code: object, dataset_id: str) -> str:
        """문자열이나 정수 resultCode를 문자열로 정규화한다."""
        if isinstance(result_code, str):
            return result_code
        if isinstance(result_code, int):
            return str(result_code)
        raise ProviderResponseError(
            "Malformed response envelope: missing resultCode",
            provider="datago",
            dataset_id=dataset_id or None,
        )

    def _extract_gyeonggi_msg_items_wrapper(self, body_dict: dict[str, object]) -> object:
        """msgBody에서 실제 목록 래퍼로 보이는 값을 골라낸다."""
        list_values: list[object] = [
            value for value in body_dict.values() if isinstance(value, list)
        ]
        if len(list_values) == 1:
            return list_values[0]
        return body_dict

    def _raise_for_result_code(self, code: str, msg: str, dataset_id: str) -> NoReturn:
        """data.go.kr 결과 코드를 정규 예외로 변환해 발생시킨다."""
        extra = {"dataset_id": dataset_id, "result_code": code, "result_msg": msg}
        if code in {"30", "31", "20", "32"}:
            logger.debug("Datago API envelope error", extra=extra)
            raise AuthError(msg, provider="datago", provider_code=code)
        if code == "22":
            logger.debug("Datago API envelope error", extra=extra)
            raise RateLimitError(msg, provider="datago", provider_code=code, retryable=False)
        if code == "10":
            logger.debug("Datago API envelope error", extra=extra)
            raise InvalidRequestError(msg, provider="datago", provider_code=code)
        if code == "12":
            logger.debug("Datago API envelope error", extra=extra)
            raise DatasetNotFoundError(
                msg,
                provider="datago",
                provider_code=code,
                dataset_id=dataset_id,
            )
        if code in {"01", "02"}:
            logger.debug("Datago API envelope error", extra=extra)
            raise ServiceUnavailableError(msg, provider="datago", provider_code=code)
        logger.debug("Datago API envelope error", extra=extra)
        raise ProviderResponseError(msg, provider="datago", provider_code=code)

    def _normalize_items(self, items_wrapper: object) -> list[dict[str, object]]:
        """items 또는 item 래퍼를 레코드 딕셔너리 목록으로 정규화한다."""
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
        """패키지에 포함된 data.go.kr 기본 카탈로그를 로드한다."""
        return load_catalogue("kpubdata.providers.datago", "datago")


__all__ = ["DataGoAdapter"]
