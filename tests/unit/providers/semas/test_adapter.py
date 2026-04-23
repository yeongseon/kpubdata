from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.exceptions import AuthError, InvalidRequestError
from kpubdata.providers.semas.adapter import SemasAdapter
from kpubdata.transport.http import HttpTransport


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parents[3] / "fixtures" / "semas" / name


def _load_fixture(name: str) -> dict[str, object]:
    payload = cast(object, json.loads(_fixture_path(name).read_text(encoding="utf-8")))
    if isinstance(payload, dict):
        return cast(dict[str, object], payload)
    raise ValueError(f"Fixture must be object: {name}")


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.headers: dict[str, str] = {"content-type": "application/json"}
        self.text: str = json.dumps(payload)
        self.content: bytes = self.text.encode()


class FakeTransport:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self._responses: list[FakeResponse] = list(responses)
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        return self._responses.pop(0)


def _build_adapter_with_transport(
    dataset_key: str,
    responses: list[FakeResponse],
) -> tuple[SemasAdapter, DatasetRef, FakeTransport]:
    transport = FakeTransport(responses)
    adapter = SemasAdapter(
        config=KPubDataConfig(provider_keys={"datago": "test-key"}),
        transport=cast(HttpTransport, cast(object, transport)),
    )
    dataset = adapter.get_dataset(dataset_key)
    return adapter, dataset, transport


def test_query_records_parses_zone_success_fixture() -> None:
    payload = _load_fixture("zone_one_success.json")
    adapter, dataset, transport = _build_adapter_with_transport("zone_one", [FakeResponse(payload)])

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert batch.total_count == 2
    assert batch.next_page is None
    assert batch.raw == payload
    assert batch.items[0]["mainTrarNm"] == "강남역 상권"
    assert len(transport.calls) == 1


def test_query_records_parses_store_success_fixture() -> None:
    payload = _load_fixture("store_one_success.json")
    adapter, dataset, _ = _build_adapter_with_transport("store_one", [FakeResponse(payload)])

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 3
    assert batch.total_count == 3
    assert batch.items[0]["bizesNm"] == "테스트카페"


def test_query_records_parses_upjong_success_fixture() -> None:
    payload = _load_fixture("upjong_large_success.json")
    adapter, dataset, _ = _build_adapter_with_transport("upjong_large", [FakeResponse(payload)])

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 3
    assert batch.items[1]["indsLclsNm"] == "음식"


def test_query_records_sets_next_page_with_total_count() -> None:
    payload = _load_fixture("store_one_success.json")
    adapter, dataset, _ = _build_adapter_with_transport("store_one", [FakeResponse(payload)])

    batch = adapter.query_records(dataset, Query(page=1, page_size=2))

    assert batch.total_count == 3
    assert batch.next_page == 2


def test_query_records_passes_filters() -> None:
    payload = _load_fixture("store_one_success.json")
    adapter, dataset, transport = _build_adapter_with_transport(
        "store_radius", [FakeResponse(payload)]
    )

    _ = adapter.query_records(dataset, Query(filters={"radius": "250", "cx": "127.0"}))

    request_params = cast(dict[str, str], transport.calls[0]["params"])
    assert request_params["serviceKey"] == "test-key"
    assert request_params["type"] == "json"
    assert request_params["pageNo"] == "1"
    assert request_params["numOfRows"] == "100"
    assert request_params["radius"] == "250"
    assert request_params["cx"] == "127.0"


def test_call_raw_returns_payload_and_uses_requested_operation() -> None:
    payload = _load_fixture("zone_one_success.json")
    adapter, dataset, transport = _build_adapter_with_transport("zone_one", [FakeResponse(payload)])

    raw = adapter.call_raw(
        dataset,
        "storeZoneInRadius",
        {"radius": "250", "serviceKey": "ignored-user-key"},
    )

    request_params = cast(dict[str, str], transport.calls[0]["params"])
    assert raw == payload
    assert cast(str, transport.calls[0]["url"]).endswith("/storeZoneInRadius")
    assert request_params["serviceKey"] == "test-key"
    assert request_params["type"] == "json"
    assert request_params["radius"] == "250"


def test_query_records_handles_empty_response() -> None:
    payload = _load_fixture("empty_response.json")
    adapter, dataset, _ = _build_adapter_with_transport("store_one", [FakeResponse(payload)])

    batch = adapter.query_records(dataset, Query())

    assert batch.items == []
    assert batch.total_count is None
    assert batch.next_page is None


def test_query_records_raises_auth_error_on_auth_fixture() -> None:
    payload = _load_fixture("error_auth.json")
    adapter, dataset, _ = _build_adapter_with_transport("store_one", [FakeResponse(payload)])

    with pytest.raises(AuthError, match="SERVICE KEY") as exc_info:
        _ = adapter.query_records(dataset, Query())

    assert exc_info.value.provider_code == "30"


def test_query_records_raises_invalid_request_error() -> None:
    payload = _load_fixture("error_invalid_request.json")
    adapter, dataset, _ = _build_adapter_with_transport("store_one", [FakeResponse(payload)])

    with pytest.raises(InvalidRequestError, match="INVALID REQUEST") as exc_info:
        _ = adapter.query_records(dataset, Query())

    assert exc_info.value.provider_code == "10"


def test_adapter_lists_all_datasets() -> None:
    adapter = SemasAdapter(config=KPubDataConfig(provider_keys={"datago": "test-key"}))

    datasets = adapter.list_datasets()

    assert len(datasets) == 17
    assert [dataset.dataset_key for dataset in datasets] == [
        "zone_one",
        "zone_radius",
        "zone_rect",
        "zone_admi",
        "store_one",
        "store_building",
        "store_pnu",
        "store_dong",
        "store_area",
        "store_radius",
        "store_rect",
        "store_polygon",
        "store_upjong",
        "store_date",
        "upjong_large",
        "upjong_middle",
        "upjong_small",
    ]


def test_get_schema_returns_catalogue_schema() -> None:
    adapter = SemasAdapter(config=KPubDataConfig(provider_keys={"datago": "test-key"}))
    dataset = adapter.get_dataset("store_one")

    schema = adapter.get_schema(dataset)

    assert schema is not None
    assert schema.fields[0].name == "bizesId"
    assert schema.fields[-1].name == "lat"
    assert len(schema.fields) == 39
