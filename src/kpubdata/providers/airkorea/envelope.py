"""AirKorea 응답 유효성 검증."""

from __future__ import annotations

from typing import cast

from kpubdata.exceptions import ParseError, ProviderResponseError


def validate_envelope(
    payload: dict[str, object],
    service_name: str,
    dataset_id: str,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    """AirKorea 응답 구조를 검증하고 본문과 아이템을 반환한다.

    Args:
        payload: AirKorea API 응답
        service_name: 서비스 이름 (예: "CtprvnRltmMesureDnsty")
        dataset_id: 데이터셋 ID

    Returns:
        (본문 딕셔너리, 아이템 리스트) 튜플

    Raises:
        ParseError: 응답 구조가 올바르지 않은 경우
    """
    # 최상위 구조: {service_name: {total_count: N, row: [items]}}
    if service_name not in payload:
        raise ParseError(
            f"Service data not found in response: expected {service_name} key",
            provider="airkorea",
            dataset_id=dataset_id,
        )

    service_data = payload.get(service_name)
    if not isinstance(service_data, dict):
        raise ParseError(
            f"Service data is not an object",
            provider="airkorea",
            dataset_id=dataset_id,
        )

    # total_count 확인
    total_count = service_data.get("total_count")
    if total_count is not None and not isinstance(total_count, int):
        raise ParseError(
            "total_count must be an integer",
            provider="airkorea",
            dataset_id=dataset_id,
        )

    # row 데이터 확인
    row_data = service_data.get("row")
    if row_data is not None and not isinstance(row_data, list):
        raise ParseError(
            "row must be a list",
            provider="airkorea",
            dataset_id=dataset_id,
        )

    items = cast(list[dict[str, object]], row_data if isinstance(row_data, list) else [])

    return service_data, items