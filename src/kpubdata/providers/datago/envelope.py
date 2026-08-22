"""data.go.kr 응답 엔벌로프 파서."""

from __future__ import annotations

import logging
from typing import NoReturn, cast

from kpubdata.core.models import DatasetRef
from kpubdata.exceptions import (
    AuthError,
    DatasetNotFoundError,
    InvalidRequestError,
    ProviderResponseError,
    RateLimitError,
    ServiceUnavailableError,
)

logger = logging.getLogger("kpubdata.provider.datago")


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


class DataGoEnvelopeParser:
    """data.go.kr 응답 엔벌로프에서 body와 item 목록을 추출한다."""

    def parse(
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

    def parse_odcloud(
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

    def _validate_its_flat_envelope(
        self, payload: dict[str, object], dataset_id: str
    ) -> tuple[dict[str, object], list[dict[str, object]]]:
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

        items = self.normalize_items(payload.get("items"))
        return payload, items

    def _validate_standard_envelope(
        self, response_dict: dict[str, object], dataset_id: str
    ) -> tuple[dict[str, object], list[dict[str, object]]]:
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
        items = self.normalize_items(body_dict.get("items"))
        return body_dict, items

    def _validate_gyeonggi_msg_envelope(
        self, response_dict: dict[str, object], dataset_id: str
    ) -> tuple[dict[str, object], list[dict[str, object]]]:
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
        items = self.normalize_items(items_wrapper)
        return body_dict, items

    def _coerce_result_code(self, result_code: object, dataset_id: str) -> str:
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
        list_values: list[object] = [
            value for value in body_dict.values() if isinstance(value, list)
        ]
        if len(list_values) == 1:
            return list_values[0]
        return body_dict

    def _raise_for_result_code(self, code: str, msg: str, dataset_id: str) -> NoReturn:
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

    def normalize_items(self, items_wrapper: object) -> list[dict[str, object]]:
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


__all__ = ["DataGoEnvelopeParser"]
