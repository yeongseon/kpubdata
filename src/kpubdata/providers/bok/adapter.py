"""KPubData Python 모듈.

이 파일은 ``src/kpubdata/providers/bok/adapter.py`` 경로의 구현을 담는다.
주요 클래스와 함수는 공개 API, 전송 계층, Provider 어댑터 중 하나의 역할을 담당한다.
"""

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
from kpubdata.transport.decode import decode_json
from kpubdata.transport.http import HttpTransport, TransportConfig

logger = logging.getLogger("kpubdata.provider.bok")


class BokAdapter:
    """한국은행 경제통계시스템(BOK ECOS) API 어댑터.

    BOK ECOS(Economic Statistics System)에서 제공하는 100대 통계지표와
    경제 시계열 데이터를 조회하고 정규화한다.
    """

    requires_api_key: bool = True

    def __init__(
        self,
        *,
        config: KPubDataConfig | None = None,
        transport: HttpTransport | None = None,
        catalogue: Sequence[DatasetRef] | None = None,
    ) -> None:
        """인스턴스가 사용할 내부 상태를 초기화한다.

        매개변수:
            config: KPubData 설정. None이면 기본값 사용.
            transport: HTTP 전송 계층. None이면 새 인스턴스 생성.
            catalogue: 데이터셋 목록. None이면 기본 카탈로그 로드.
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
        """Provider 이름을 반환한다.

        반환값:
            항상 "bok" 문자열.
        """
        return "bok"

    def list_datasets(self) -> list[DatasetRef]:
        """이 어댑터가 제공하는 모든 데이터셋 목록을 반환한다.

        반환값:
            DatasetRef 리스트. 각 항목은 BOK ECOS 통계 지표를 나타낸다.
        """
        return list(self._datasets)

    def search_datasets(self, text: str) -> list[DatasetRef]:
        """데이터셋을 검색한다.

        매개변수:
            text: 검색어. 데이터셋 ID 또는 이름에서 대소문자 무시하고 부분 매칭.

        반환값:
            검색 조건에 일치하는 DatasetRef 리스트.
        """
        needle = text.casefold()
        return [
            dataset
            for dataset in self._datasets
            if needle in dataset.id.casefold() or needle in dataset.name.casefold()
        ]

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        """주어진 키에 해당하는 데이터셋을 반환한다.

        매개변수:
            dataset_key: 데이터셋 고유 키 (예: "901Y009").

        반환값:
            DatasetRef 인스턴스.

        예외:
            DatasetNotFoundError: 해당 키의 데이터셋이 존재하지 않을 때.
        """
        dataset = self._datasets_by_key.get(dataset_key)
        if dataset is not None:
            return dataset

        logger.debug(
            "BOK dataset not found",
            extra={"dataset_id": f"bok.{dataset_key}", "provider": "bok"},
        )
        raise DatasetNotFoundError(
            f"Dataset not found: bok.{dataset_key}",
            provider="bok",
            dataset_id=f"bok.{dataset_key}",
        )

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        """BOK ECOS API를 호출하여 레코드를 조회한다.

        매개변수:
            dataset: 대상 데이터셋.
            query: 조회 쿼리. start_date, end_date 필수. 주기(frequency)는 선택.

        반환값:
            RecordBatch. items에 조회된 레코드, total_count와 next_page 포함.

        예외:
            InvalidRequestError: start_date 또는 end_date 누락 시.
            AuthError: API 키 인증 실패 시.
            RateLimitError: 호출 한도 초과 시.
            ServiceUnavailableError: BOK ECOS 서비스 점검 중일 때.
        """
        page = query.page or 1
        page_size = query.page_size or 100
        frequency = self._resolve_frequency(query)
        start_date = query.start_date or self._resolve_string_param(query, "start_date")
        end_date = query.end_date or self._resolve_string_param(query, "end_date")
        logger.debug(
            "bok query_records",
            extra={
                "dataset_id": dataset.id,
                "page": page,
                "page_size": page_size,
                "frequency": frequency,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

        if start_date is None or end_date is None:
            logger.debug(
                "BOK ECOS invalid query: missing start/end date",
                extra={"dataset_id": dataset.id},
            )
            raise InvalidRequestError(
                "BOK ECOS queries require start_date and end_date",
                provider="bok",
                dataset_id=dataset.id,
            )

        start_index = (page - 1) * page_size + 1
        end_index = page * page_size
        url = self._build_request_url(
            dataset,
            operation=None,
            start_index=start_index,
            end_index=end_index,
            frequency=frequency,
            start_date=start_date,
            end_date=end_date,
        )

        payload = self._request_and_decode(url, dataset.id)
        body, items = self._validate_envelope(payload, dataset.id)

        total_count = coerce_int(body.get("list_total_count"), 0)
        if (total_count and page * page_size < total_count) or (
            not total_count and len(items) == page_size
        ):
            computed_next = page + 1
        else:
            computed_next = None

        if not items:
            logger.debug(
                "BOK envelope: zero items",
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
        """데이터셋의 스키마 정보를 반환한다.

        매개변수:
            dataset: 대상 데이터셋.

        반환값:
            SchemaDescriptor 또는 None. 메타데이터에서 스키마를 구성할 수 없으면 None.
        """
        return build_schema_from_metadata(dataset)

    def call_raw(self, dataset: DatasetRef, operation: str, params: dict[str, object]) -> object:
        """BOK ECOS API를 직접 호출하고 원본 응답을 반환한다 (비상구).

        매개변수:
            dataset: 대상 데이터셋.
            operation: ECOS API 작업명 (예: "StatisticSearch"). 비어 있으면 기본 작업 사용.
            params: API 파라미터. frequency, start_date, end_date, start_index, end_index 등.

        반환값:
            BOK ECOS API 원본 JSON 응답 (dict).

        예외:
            InvalidRequestError: 필수 파라미터 누락 시.
            AuthError, RateLimitError, ServiceUnavailableError: API 오류 시.
        """
        logger.debug(
            "bok call_raw",
            extra={
                "dataset_id": dataset.id,
                "operation": operation,
                "param_keys": sorted(params.keys()),
            },
        )
        frequency = self._string_param(params, "frequency") or "M"
        start_date = self._require_param(params, "start_date", dataset.id)
        end_date = self._require_param(params, "end_date", dataset.id)
        start_index = self._int_param(params, "start_index", 1)
        end_index = self._int_param(params, "end_index", 10)

        url = self._build_request_url(
            dataset,
            operation=operation,
            start_index=start_index,
            end_index=end_index,
            frequency=frequency,
            start_date=start_date,
            end_date=end_date,
        )
        payload = self._request_and_decode(url, dataset.id)
        _ = self._validate_envelope(payload, dataset.id)
        return payload

    def _require_api_key(self) -> str:
        """필수 API 키를 읽고 없으면 예외를 발생시킨다.

        반환값:
            BOK ECOS API 키 (config에서 읽음).

        예외:
            AuthError: API 키가 설정되지 않았을 때.
        """
        return self._config.require_provider_key("bok")

    def _build_request_url(
        self,
        dataset: DatasetRef,
        *,
        operation: str | None,
        start_index: int,
        end_index: int,
        frequency: str,
        start_date: str,
        end_date: str,
    ) -> str:
        """BOK ECOS API 요청 URL을 구성한다.

        매개변수:
            dataset: 대상 데이터셋.
            operation: API 작업명. None이면 메타데이터의 default_operation 사용.
            start_index: 조회 시작 인덱스 (1부터 시작).
            end_index: 조회 종료 인덱스.
            frequency: 주기 코드 (예: "M"=월, "Q"=분기, "A"=연).
            start_date: 조회 시작 날짜 (YYYYMMDD 또는 YYYYMM 형식).
            end_date: 조회 종료 날짜 (YYYYMMDD 또는 YYYYMM 형식).

        반환값:
            BOK ECOS API 호출용 전체 URL 문자열.

        예외:
            ProviderResponseError: 메타데이터에 필수 필드 누락 시.
        """
        base_url_raw = dataset.raw_metadata.get("base_url")
        if not isinstance(base_url_raw, str) or not base_url_raw:
            logger.debug(
                "BOK ECOS dataset metadata missing base_url",
                extra={"dataset_id": dataset.id},
            )
            raise ProviderResponseError(
                "Dataset metadata missing base_url",
                provider="bok",
                dataset_id=dataset.id,
            )

        selected_operation = operation or dataset.raw_metadata.get("default_operation")
        if not isinstance(selected_operation, str) or not selected_operation:
            logger.debug(
                "BOK ECOS dataset metadata missing default_operation",
                extra={"dataset_id": dataset.id},
            )
            raise ProviderResponseError(
                "Dataset metadata missing default_operation",
                provider="bok",
                dataset_id=dataset.id,
            )

        stat_code = self._require_dataset_metadata(dataset, "stat_code")
        item_code1 = self._require_dataset_metadata(dataset, "item_code1")
        api_key = self._require_api_key()
        return (
            f"{base_url_raw}/{api_key}/json/{selected_operation}/"
            f"{start_index}/{end_index}/{stat_code}/{frequency}/{start_date}/{end_date}/{item_code1}"
        )

    def _request_and_decode(self, url: str, dataset_id: str) -> dict[str, object]:
        """BOK ECOS API에 HTTP GET 요청을 보내고 JSON 응답을 디코딩한다.

        매개변수:
            url: 요청할 전체 URL.
            dataset_id: 데이터셋 ID (로깅용).

        반환값:
            파싱된 JSON 응답 (dict).

        예외:
            ParseError: 응답 파싱 실패 또는 응답이 JSON object가 아닐 때.
        """
        response = self._transport.request("GET", url, dataset_id=dataset_id, provider="bok")

        try:
            decoded_obj: object = decode_json(response.content)
        except ParseError as exc:
            exc.provider = "bok"
            logger.debug("BOK ECOS response parsing failed", extra={"dataset_id": dataset_id})
            raise

        if isinstance(decoded_obj, dict):
            return cast(dict[str, object], decoded_obj)

        logger.debug("BOK ECOS decoded payload invalid type", extra={"dataset_id": dataset_id})
        raise ParseError("Decoded payload is not an object", provider="bok")

    def _validate_envelope(
        self, payload: dict[str, object], dataset_id: str = ""
    ) -> tuple[dict[str, object], list[dict[str, object]]]:
        """BOK ECOS API 응답 envelope의 형식을 검증하고 필요한 값을 추출한다.

        매개변수:
            payload: 디코딩된 API 응답 (dict).
            dataset_id: 데이터셋 ID (로깅/예외용).

        반환값:
            (body_dict, items) 튜플.
            body_dict는 StatisticSearch 본문, items는 레코드 리스트.

        예외:
            ProviderResponseError: envelope에 StatisticSearch가 없거나 형식 오류 시.
            AuthError, RateLimitError, ServiceUnavailableError: RESULT 필드에 오류 코드 있을 때.
        """
        self._raise_for_result(payload, dataset_id)

        body_obj = payload.get("StatisticSearch")
        if not isinstance(body_obj, dict):
            raise ProviderResponseError(
                "Malformed response envelope: missing StatisticSearch",
                provider="bok",
                dataset_id=dataset_id or None,
            )

        body_dict = cast(dict[str, object], body_obj)
        items = self._normalize_rows(body_dict.get("row"))
        return body_dict, items

    def _raise_for_result(self, payload: Mapping[str, object], dataset_id: str) -> None:
        """BOK ECOS API 응답의 RESULT 필드를 확인하고 오류 시 예외를 발생시킨다.

        매개변수:
            payload: 디코딩된 API 응답.
            dataset_id: 데이터셋 ID (예외 메시지용).

        예외:
            AuthError: 인증키 오류 시.
            RateLimitError: 호출 한도 초과 시.
            ServiceUnavailableError: 서비스 점검 중일 때.
            InvalidRequestError: 잘못된 파라미터 사용 시.
            ProviderResponseError: 기타 오류 시.
        """
        result_obj = payload.get("RESULT")
        if not isinstance(result_obj, dict):
            return

        result_dict = cast(dict[str, object], result_obj)
        code_raw = result_dict.get("CODE")
        message_raw = result_dict.get("MESSAGE")
        code = code_raw if isinstance(code_raw, str) else "UNKNOWN"
        message = message_raw if isinstance(message_raw, str) else "Provider returned error"
        logger.debug(
            "BOK ECOS result",
            extra={"result_code": code, "result_msg": message, "dataset_id": dataset_id},
        )
        # RESULT 필드가 있으면 항상 오류 — BOK ECOS는 성공 시 RESULT 없이 응답
        self._raise_for_result_code(code, message, dataset_id)

    def _raise_for_result_code(self, code: str, msg: str, dataset_id: str) -> NoReturn:
        """BOK ECOS API 오류 코드를 분석하여 적절한 예외를 발생시킨다.

        매개변수:
            code: RESULT.CODE 값.
            msg: RESULT.MESSAGE 값.
            dataset_id: 데이터셋 ID (예외 메시지용).

        예외:
            AuthError, RateLimitError, ServiceUnavailableError, InvalidRequestError,
            또는 ProviderResponseError 중 하나. (항상 예외를 던지므로 반환하지 않음)
        """
        normalized_msg = msg.casefold()
        if "인증키" in msg or "api key" in normalized_msg or "auth" in normalized_msg:
            raise AuthError(msg, provider="bok", provider_code=code, dataset_id=dataset_id or None)
        if "호출한도" in msg or "too many" in normalized_msg or "rate limit" in normalized_msg:
            raise RateLimitError(
                msg, provider="bok", provider_code=code, dataset_id=dataset_id or None
            )
        if (
            "점검" in msg
            or "service unavailable" in normalized_msg
            or "temporarily unavailable" in normalized_msg
        ):
            raise ServiceUnavailableError(
                msg,
                provider="bok",
                provider_code=code,
                dataset_id=dataset_id or None,
            )
        if "필수" in msg or "invalid" in normalized_msg or "잘못" in msg:
            raise InvalidRequestError(
                msg, provider="bok", provider_code=code, dataset_id=dataset_id or None
            )
        raise ProviderResponseError(
            msg, provider="bok", provider_code=code, dataset_id=dataset_id or None
        )

    def _resolve_frequency(self, query: Query) -> str:
        """쿼리에서 주기(frequency) 파라미터를 추출하거나 기본값을 반환한다.

        매개변수:
            query: Query 인스턴스.

        반환값:
            주기 코드 문자열 (예: "M"). 없으면 "M" (월간) 기본값.
        """
        return self._resolve_string_param(query, "frequency") or "M"

    def _resolve_string_param(self, query: Query, key: str) -> str | None:
        """쿼리의 extra 또는 filters에서 문자열 파라미터를 추출한다.

        매개변수:
            query: Query 인스턴스.
            key: 추출할 파라미터 키.

        반환값:
            파라미터 값 문자열 또는 None. extra 우선, 없으면 filters 확인.
        """
        if key in query.extra:
            extra_value = query.extra[key]
            if isinstance(extra_value, str) and extra_value:
                return extra_value
        if key in query.filters:
            filter_value = query.filters[key]
            if isinstance(filter_value, str) and filter_value:
                return filter_value
        return None

    def _require_dataset_metadata(self, dataset: DatasetRef, key: str) -> str:
        """데이터셋 메타데이터에서 필수 필드를 읽고 없으면 예외를 발생시킨다.

        매개변수:
            dataset: DatasetRef 인스턴스.
            key: 메타데이터 키 (예: "stat_code", "item_code1").

        반환값:
            메타데이터 값 문자열.

        예외:
            ProviderResponseError: 메타데이터에 해당 키가 없거나 값이 비어 있을 때.
        """
        value = dataset.raw_metadata.get(key)
        if isinstance(value, str) and value:
            return value
        raise ProviderResponseError(
            f"Dataset metadata missing {key}",
            provider="bok",
            dataset_id=dataset.id,
        )

    def _normalize_rows(self, rows_wrapper: object) -> list[dict[str, object]]:
        """BOK ECOS API 응답의 row 필드를 정규화하여 리스트로 반환한다.

        매개변수:
            rows_wrapper: API 응답의 row 값. None, dict, 또는 list일 수 있음.

        반환값:
            dict 리스트. row가 None이면 빈 리스트, dict 하나면 1개 항목 리스트,
            list면 그 중 dict만 필터링하여 반환.
        """
        if rows_wrapper is None:
            return []
        if isinstance(rows_wrapper, list):
            rows = cast(list[object], rows_wrapper)
            return [cast(dict[str, object], item) for item in rows if isinstance(item, dict)]
        if isinstance(rows_wrapper, dict):
            return [cast(dict[str, object], rows_wrapper)]
        return []

    @staticmethod
    def _string_param(params: Mapping[str, object], key: str) -> str | None:
        """call_raw params에서 문자열 파라미터를 추출한다.

        매개변수:
            params: 파라미터 dict.
            key: 추출할 키.

        반환값:
            문자열 값 또는 None. 값이 없거나 문자열이 아니거나 비어 있으면 None.
        """
        value = params.get(key)
        if isinstance(value, str) and value:
            return value
        return None

    @classmethod
    def _require_param(cls, params: Mapping[str, object], key: str, dataset_id: str) -> str:
        """call_raw params에서 필수 문자열 파라미터를 읽고 없으면 예외를 발생시킨다.

        매개변수:
            params: 파라미터 dict.
            key: 필수 파라미터 키.
            dataset_id: 데이터셋 ID (예외 메시지용).

        반환값:
            파라미터 값 문자열.

        예외:
            InvalidRequestError: 파라미터가 없거나 비어 있을 때.
        """
        value = cls._string_param(params, key)
        if value is not None:
            return value
        logger.debug(
            "BOK ECOS raw call missing required parameter",
            extra={"dataset_id": dataset_id},
        )
        raise InvalidRequestError(
            f"BOK ECOS raw calls require {key}", provider="bok", dataset_id=dataset_id
        )

    @classmethod
    def _int_param(cls, params: Mapping[str, object], key: str, default: int) -> int:
        """call_raw params에서 정수 파라미터를 추출하고 유효하지 않으면 기본값 반환.

        매개변수:
            params: 파라미터 dict.
            key: 추출할 키.
            default: 기본값 정수.

        반환값:
            정수 값. 변환 실패하거나 0 이하면 default 반환.
        """
        value = params.get(key)
        coerced = coerce_int(value, default)
        return coerced if coerced > 0 else default

    @staticmethod
    def _load_default_catalogue() -> tuple[DatasetRef, ...]:
        """기본 카탈로그를 로드하여 반환한다.

        반환값:
            kpubdata.providers.bok 패키지의 카탈로그에서 로드한 DatasetRef 튜플.
        """
        return load_catalogue("kpubdata.providers.bok", "bok")


__all__ = ["BokAdapter"]
