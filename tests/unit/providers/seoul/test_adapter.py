from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import Query
from kpubdata.exceptions import AuthError, InvalidRequestError, ProviderResponseError
from kpubdata.providers.seoul.adapter import SeoulAdapter
from kpubdata.transport.http import HttpTransport


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parents[3] / "fixtures" / "seoul" / name


def _load_fixture(name: str) -> dict[str, object]:
    return cast(dict[str, object], json.loads(_fixture_path(name).read_text(encoding="utf-8")))


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.headers: dict[str, str] = {"content-type": "application/json"}
        self.text: str = json.dumps(payload, ensure_ascii=False)
        self.content: bytes = self.text.encode("utf-8")


class FakeTransport:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self._responses: list[FakeResponse] = list(responses)
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        if not self._responses:
            raise AssertionError("No fixture responses remaining")
        return self._responses.pop(0)


def _build_adapter(
    responses: list[FakeResponse],
    *,
    config: KPubDataConfig | None = None,
) -> tuple[SeoulAdapter, FakeTransport]:
    transport = FakeTransport(responses)
    adapter = SeoulAdapter(
        config=config or KPubDataConfig(provider_keys={"seoul": "test-seoul-key"}),
        transport=cast(HttpTransport, cast(object, transport)),
    )
    return adapter, transport


def test_query_records_builds_subway_url_with_path_key() -> None:
    adapter, transport = _build_adapter(
        [FakeResponse(_load_fixture("subway_realtime_arrival_success.json"))]
    )
    dataset = adapter.get_dataset("subway_realtime_arrival")

    _ = adapter.query_records(dataset, Query(filters={"stationName": "강남"}))

    assert transport.calls[0]["url"] == (
        "http://swopenAPI.seoul.go.kr/api/subway/test-seoul-key/json/"
        "realtimeStationArrival/1/100/%EA%B0%95%EB%82%A8"
    )


def test_query_records_builds_bike_url_with_path_key() -> None:
    adapter, transport = _build_adapter(
        [FakeResponse(_load_fixture("bike_rent_month_success.json"))]
    )
    dataset = adapter.get_dataset("bike_rent_month")

    _ = adapter.query_records(dataset, Query(filters={"RENT_NM": "202401"}, page_size=10))

    assert transport.calls[0]["url"] == (
        "http://openapi.seoul.go.kr:8088/test-seoul-key/json/tbCycleRentUseMonthInfo/1/10/202401"
    )


def test_query_records_parses_successful_envelope() -> None:
    adapter, _ = _build_adapter(
        [FakeResponse(_load_fixture("subway_realtime_arrival_success.json"))]
    )
    dataset = adapter.get_dataset("subway_realtime_arrival")

    batch = adapter.query_records(
        dataset, Query(filters={"stationName": "강남"}, page=1, page_size=2)
    )

    assert len(batch.items) == 2
    assert batch.items[0]["statnNm"] == "강남"
    assert batch.total_count == 2
    assert batch.next_page is None


def test_info_100_raises_auth_error() -> None:
    adapter, _ = _build_adapter([FakeResponse(_load_fixture("error_auth.json"))])
    dataset = adapter.get_dataset("subway_realtime_arrival")

    with pytest.raises(AuthError) as exc_info:
        _ = adapter.query_records(dataset, Query(filters={"stationName": "강남"}))

    assert exc_info.value.provider_code == "INFO-100"


def test_info_200_returns_empty_record_batch() -> None:
    adapter, _ = _build_adapter([FakeResponse(_load_fixture("empty_response.json"))])
    dataset = adapter.get_dataset("subway_realtime_arrival")

    batch = adapter.query_records(dataset, Query(filters={"stationName": "강남"}))

    assert batch.items == []
    assert batch.total_count is None
    assert batch.next_page is None


def test_call_raw_returns_raw_payload() -> None:
    payload = _load_fixture("bike_rent_month_success.json")
    adapter, _ = _build_adapter([FakeResponse(payload)])
    dataset = adapter.get_dataset("bike_rent_month")

    raw = adapter.call_raw(
        dataset,
        "tbCycleRentUseMonthInfo",
        {"RENT_NM": "202401", "page_no": 1, "page_size": 5},
    )

    assert raw == payload


def test_pagination_uses_index_window_in_url() -> None:
    adapter, transport = _build_adapter(
        [FakeResponse(_load_fixture("bike_rent_month_success.json"))]
    )
    dataset = adapter.get_dataset("bike_rent_month")

    _ = adapter.query_records(dataset, Query(filters={"RENT_NM": "202401"}, page=2, page_size=10))

    assert "/11/20/202401" in cast(str, transport.calls[0]["url"])


@pytest.mark.parametrize(
    ("code", "expected_exception"),
    [
        ("INFO-300", AuthError),
        ("INFO-400", InvalidRequestError),
        ("INFO-500", ProviderResponseError),
        ("ERROR-300", InvalidRequestError),
        ("ERROR-336", InvalidRequestError),
        ("ERROR-600", ProviderResponseError),
        ("UNKNOWN-999", ProviderResponseError),
    ],
)
def test_error_code_mapping_table(code: str, expected_exception: type[Exception]) -> None:
    payload: dict[str, object] = {
        "realtimeStationArrival": {
            "list_total_count": 0,
            "RESULT": {"CODE": code, "MESSAGE": f"error: {code}"},
            "row": [],
        }
    }
    adapter, _ = _build_adapter([FakeResponse(payload)])
    dataset = adapter.get_dataset("subway_realtime_arrival")

    with pytest.raises(expected_exception) as exc_info:
        _ = adapter.query_records(dataset, Query(filters={"stationName": "강남"}))

    provider_error = exc_info.value
    assert getattr(provider_error, "provider_code", None) == code


def test_config_from_env_injects_seoul_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KPUBDATA_SEOUL_API_KEY", "env-seoul-key")
    adapter, transport = _build_adapter(
        [FakeResponse(_load_fixture("subway_realtime_arrival_success.json"))],
        config=KPubDataConfig.from_env(),
    )
    dataset = adapter.get_dataset("subway_realtime_arrival")

    _ = adapter.query_records(dataset, Query(filters={"stationName": "강남"}))

    assert "/env-seoul-key/json/" in cast(str, transport.calls[0]["url"])


def test_page_size_over_1000_raises_invalid_request() -> None:
    adapter, _ = _build_adapter([])
    dataset = adapter.get_dataset("bike_rent_month")

    with pytest.raises(InvalidRequestError, match="page_size must be <= 1000"):
        _ = adapter.query_records(dataset, Query(filters={"RENT_NM": "202401"}, page_size=1001))
