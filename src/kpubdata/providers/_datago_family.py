"""data.go.kr 계열 provider 어댑터의 공용 구현.

``localdata`` 와 ``semas`` 는 같은 data.go.kr 인증·envelope·페이지네이션 규약을
쓴다. 두 어댑터가 375줄짜리 사본 두 벌로 존재했고, 이름 문자열을 맞춰 놓고 비교하면
**코드 차이가 0줄**이었다 — 다른 것은 주석과 포매팅뿐이었다.

그 중복이 실제로 회귀를 만들었다. data.go.kr 의 ``"03"``(NODATA_ERROR)을 정상
응답으로 다루는 분기가 semas 에는 있고 localdata 에는 없어서, 필터를 걸어 조회했는데
결과가 없는 흔한 경우가 localdata 에서만 예외로 올라왔다 (#470). 한쪽을 고치면
다른 쪽도 고쳐야 한다는 사실이 코드 어디에도 적혀 있지 않았다.

새 provider 가 같은 규약을 쓰면 ``provider_name`` 과 catalogue 패키지만 지정해
상속한다.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import ClassVar, NoReturn, cast

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

logger = logging.getLogger("kpubdata.provider.datago_family")


def _is_success_code(code: str) -> bool:
    """success code인지 반환한다."""
    try:
        return int(code) == 0
    except ValueError:
        return False


class DataGoFamilyAdapter:
    """data.go.kr 계열 어댑터의 공통 동작.

    하위 클래스는 ``provider_name`` 과 ``catalogue_package`` 만 지정한다.
    """

    #: provider 식별자. 로그·예외·credential 해석에 모두 이 값을 쓴다.
    provider_name: ClassVar[str]
    #: 기본 catalogue.json 을 담은 패키지 경로.
    catalogue_package: ClassVar[str]

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
        """name과 관련된 값을 계산하거나 조회한다."""
        return self.provider_name

    def list_datasets(self) -> list[DatasetRef]:
        """list datasets과 관련된 값을 계산하거나 조회한다."""
        return list(self._datasets)

    def search_datasets(self, text: str) -> list[DatasetRef]:
        """search datasets과 관련된 값을 계산하거나 조회한다."""
        needle = text.casefold()
        return [
            dataset
            for dataset in self._datasets
            if needle in dataset.id.casefold() or needle in dataset.name.casefold()
        ]

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        """dataset을 반환한다."""
        dataset = self._datasets_by_key.get(dataset_key)
        if dataset is not None:
            return dataset

        logger.debug(
            "Localdata dataset not found",
            extra={
                "dataset_id": f"{self.provider_name}.{dataset_key}",
                "provider": self.provider_name,
            },
        )
        raise DatasetNotFoundError(
            f"Dataset not found: {self.provider_name}.{dataset_key}",
            provider=self.provider_name,
            dataset_id=f"{self.provider_name}.{dataset_key}",
        )

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        """records을 수행한다."""
        page = query.page or 1
        page_size = query.page_size or 100
        logger.debug(
            f"{self.provider_name} query_records",
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
        """schema을 반환한다."""
        return build_schema_from_metadata(dataset)

    def call_raw(self, dataset: DatasetRef, operation: str, params: dict[str, object]) -> object:
        """call raw과 관련된 값을 계산하거나 조회한다."""
        logger.debug(
            f"{self.provider_name} call_raw",
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
        """공공데이터포털(data.go.kr) API 키를 읽고 없으면 예외를 발생시킨다.
        localdata · semas · lofin 어댓터는 모두 data.go.kr 인증 시스템을 공유하며
        단일 provider_key("datago")로 관리하는 것이 의도된 설계다.
        """
        # 자기 이름을 먼저 본다. 이 계열은 data.go.kr 서비스라 datago 와 같은 키를
        # 쓰지만, 곧바로 "datago" 를 요구하면 README 가 안내하는
        # KPUBDATA_<PROVIDER>_API_KEY 가 조용히 무시된다.
        return self._config.require_provider_key(self.provider_name, fallback_to="datago")

    def _build_request_url(self, dataset: DatasetRef, operation: str | None = None) -> str:
        """요청 URL을 구성해 반환한다."""
        base_url_raw = dataset.raw_metadata.get("base_url")
        if not isinstance(base_url_raw, str) or not base_url_raw:
            logger.debug(
                "Localdata dataset metadata missing base_url",
                extra={"dataset_id": dataset.id},
            )
            raise ProviderResponseError(
                "Dataset metadata missing base_url",
                provider=self.provider_name,
                dataset_id=dataset.id,
            )

        selected_operation = operation or dataset.raw_metadata.get("default_operation")
        if isinstance(selected_operation, str) and selected_operation:
            return f"{base_url_raw.rstrip('/')}/{selected_operation}"
        return base_url_raw

    def _build_base_params(self, dataset: DatasetRef) -> dict[str, str]:
        """기본 파라미터을 구성해 반환한다."""
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
        """request and decode과 관련된 값을 계산하거나 조회한다."""
        string_params = {key: str(value) for key, value in params.items()}
        response = self._transport.request(
            "GET",
            url,
            params=string_params,
            dataset_id=dataset_id,
            provider=self.provider_name,
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
            exc.provider = self.provider_name
            logger.debug("Localdata response parsing failed", extra={"dataset_id": dataset_id})
            raise
        except ImportError as exc:
            raise ParseError(
                f"Failed to parse {self.provider_name} response", provider=self.provider_name
            ) from exc

        if isinstance(decoded, dict):
            return cast(dict[str, object], decoded)

        logger.debug("Localdata decoded payload invalid type", extra={"dataset_id": dataset_id})
        raise ParseError("Decoded payload is not an object", provider=self.provider_name)

    def _validate_envelope(
        self, payload: dict[str, object], dataset_id: str = ""
    ) -> tuple[dict[str, object], list[dict[str, object]]]:
        """envelope의 형식을 검증하고 필요한 값을 추출한다."""
        response_obj = payload.get("response")
        if not isinstance(response_obj, dict):
            raise ProviderResponseError(
                "Malformed response envelope: missing response",
                provider=self.provider_name,
                dataset_id=dataset_id or None,
            )

        response_dict = cast(dict[str, object], response_obj)

        header_obj = response_dict.get("header")
        if not isinstance(header_obj, dict):
            raise ProviderResponseError(
                "Malformed response envelope: missing header",
                provider=self.provider_name,
                dataset_id=dataset_id or None,
            )

        header_dict = cast(dict[str, object], header_obj)
        result_code = header_dict.get("resultCode")
        if not isinstance(result_code, str):
            raise ProviderResponseError(
                "Malformed response envelope: missing resultCode",
                provider=self.provider_name,
                dataset_id=dataset_id or None,
            )

        result_msg_raw = header_dict.get("resultMsg")
        result_msg = (
            result_msg_raw if isinstance(result_msg_raw, str) else "Provider returned error"
        )
        logger.debug(
            f"{self.provider_name} result",
            extra={"result_code": result_code, "result_msg": result_msg, "dataset_id": dataset_id},
        )
        body_obj = response_dict.get("body")
        body_dict: dict[str, object] = (
            cast(dict[str, object], body_obj) if isinstance(body_obj, dict) else {}
        )

        # data.go.kr 의 "03"(NODATA_ERROR)은 정상 응답이다 — 조건에 맞는 데이터가
        # 없다는 뜻이지 호출이 실패한 것이 아니다. 이 분기가 없으면 필터를 걸어
        # 조회했는데 결과가 없는 흔한 경우가 예외로 올라온다. semas 는 처음부터
        # 이렇게 처리했고 localdata 만 빠져 있었다 (#470).
        if result_code == "03":
            return body_dict, []
        if not _is_success_code(result_code):
            self._raise_for_result_code(result_code, result_msg, dataset_id)

        items = self._normalize_items(body_dict.get("items"))
        return body_dict, items

    def _raise_for_result_code(self, code: str, msg: str, dataset_id: str) -> NoReturn:
        """raise for 결과 코드과 관련된 값을 계산하거나 조회한다."""
        if code in {"30", "31", "20", "32"}:
            raise AuthError(msg, provider=self.provider_name, provider_code=code)
        if code == "22":
            raise RateLimitError(
                msg, provider=self.provider_name, provider_code=code, retryable=False
            )
        if code == "10":
            raise InvalidRequestError(msg, provider=self.provider_name, provider_code=code)
        if code == "12":
            raise DatasetNotFoundError(
                msg,
                provider=self.provider_name,
                provider_code=code,
                dataset_id=dataset_id,
            )
        if code in {"01", "02"}:
            raise ServiceUnavailableError(msg, provider=self.provider_name, provider_code=code)
        raise ProviderResponseError(msg, provider=self.provider_name, provider_code=code)

    def _normalize_items(self, items_wrapper: object) -> list[dict[str, object]]:
        """items을 정규화해 반환한다."""
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
            if "item" in items_wrapper or not items_wrapper:
                # ``item`` 키가 있는데 list 도 dict 도 아니면 비어 있다는 뜻이다
                # (XML ``<items><item/></items>`` 는 ``{"item": None}`` 이 된다).
                # 빈 dict 도 마찬가지다. 이 둘을 단건으로 승격하면 **유령 1행** 이
                # 생긴다 — #470 에서 그렇게 만들었고, 그것이 회귀였다.
                return []
            # 그 밖의 비어 있지 않은 dict 는 래핑 없이 온 단건이다. []로
            # 떨어뜨리면 같은 모양의 응답이 provider 에 따라 0건과 1건으로
            # 갈린다 (#470).
            return [cast(dict[str, object], items_wrapper)]

        if isinstance(items_wrapper, list):
            normalized_items = cast(list[object], items_wrapper)
            return [
                cast(dict[str, object], item) for item in normalized_items if isinstance(item, dict)
            ]

        return []

    def _load_default_catalogue(self) -> tuple[DatasetRef, ...]:
        """하위 클래스가 지정한 패키지에서 기본 카탈로그를 로드한다."""
        return load_catalogue(self.catalogue_package, self.provider_name)


__all__ = ["DataGoFamilyAdapter"]
