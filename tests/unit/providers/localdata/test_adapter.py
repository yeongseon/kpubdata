from __future__ import annotations

import json
import logging
from pathlib import Path
from types import MappingProxyType
from typing import cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.exceptions import AuthError, ProviderResponseError
from kpubdata.providers.localdata.adapter import LocaldataAdapter
from kpubdata.transport.http import HttpTransport


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parents[3] / "fixtures" / "localdata" / name


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
    responses: list[FakeResponse],
) -> tuple[LocaldataAdapter, DatasetRef, FakeTransport]:
    transport = FakeTransport(responses)
    adapter = LocaldataAdapter(
        config=KPubDataConfig(provider_keys={"localdata": "test-key"}),
        transport=cast(HttpTransport, cast(object, transport)),
    )
    dataset = adapter.get_dataset("general_restaurant")
    return adapter, dataset, transport


def _build_rest_cafe_adapter_with_transport(
    responses: list[FakeResponse],
) -> tuple[LocaldataAdapter, DatasetRef, FakeTransport]:
    transport = FakeTransport(responses)
    adapter = LocaldataAdapter(
        config=KPubDataConfig(provider_keys={"localdata": "test-key"}),
        transport=cast(HttpTransport, cast(object, transport)),
    )
    dataset = adapter.get_dataset("rest_cafe")
    return adapter, dataset, transport


def test_query_records_parses_success_fixture() -> None:
    payload = _load_fixture("general_restaurant_success.json")
    adapter, dataset, transport = _build_adapter_with_transport([FakeResponse(payload)])

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 3
    assert batch.total_count == 3
    assert batch.next_page is None
    assert batch.raw == payload
    assert batch.items[0]["BPLC_NM"] == "한밥식당"
    assert len(transport.calls) == 1


def test_query_records_raises_auth_error_on_auth_fixture() -> None:
    payload = _load_fixture("error_auth.json")
    adapter, dataset, _ = _build_adapter_with_transport([FakeResponse(payload)])

    try:
        _ = adapter.query_records(dataset, Query())
    except AuthError as exc_info:
        assert exc_info.provider_code == "30"
        return

    raise AssertionError("AuthError was not raised")


def test_query_records_handles_empty_response() -> None:
    payload = _load_fixture("empty_response.json")
    adapter, dataset, _ = _build_adapter_with_transport([FakeResponse(payload)])

    batch = adapter.query_records(dataset, Query())

    assert batch.items == []
    assert batch.total_count is None
    assert batch.next_page is None


def test_query_records_handles_empty_response_logs_debug(
    caplog: pytest.LogCaptureFixture,
) -> None:
    payload = _load_fixture("empty_response.json")
    adapter, dataset, _ = _build_adapter_with_transport([FakeResponse(payload)])

    caplog.set_level(logging.DEBUG, logger="kpubdata.provider.localdata")
    batch = adapter.query_records(dataset, Query())

    assert batch.items == []
    record = next(
        record
        for record in caplog.records
        if record.getMessage() == "Localdata envelope: zero items"
    )
    assert record.__dict__["dataset_id"] == dataset.id
    assert record.__dict__["page"] == 1
    assert record.__dict__["page_size"] == 100
    assert record.__dict__["total_count"] == 0


def test_query_records_sets_next_page_with_total_count() -> None:
    payload = _load_fixture("general_restaurant_success.json")
    adapter, dataset, _ = _build_adapter_with_transport([FakeResponse(payload)])

    batch = adapter.query_records(dataset, Query(page=1, page_size=2))

    assert len(batch.items) == 3
    assert batch.total_count == 3
    assert batch.next_page == 2


def test_query_records_passes_local_code_filter() -> None:
    payload = _load_fixture("general_restaurant_success.json")
    adapter, dataset, transport = _build_adapter_with_transport([FakeResponse(payload)])

    _ = adapter.query_records(dataset, Query(filters={"localCode": "41135"}))

    request_params = cast(dict[str, str], transport.calls[0]["params"])
    assert request_params["serviceKey"] == "test-key"
    assert request_params["type"] == "json"
    assert request_params["pageNo"] == "1"
    assert request_params["numOfRows"] == "100"
    assert request_params["localCode"] == "41135"


def test_rest_cafe_query_records_parses_success_fixture() -> None:
    payload = _load_fixture("rest_cafe_success.json")
    adapter, dataset, _ = _build_rest_cafe_adapter_with_transport([FakeResponse(payload)])

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 3
    assert batch.items[0]["BPLC_NM"] == "카페모카"


def test_adapter_lists_two_datasets() -> None:
    adapter = LocaldataAdapter(config=KPubDataConfig(provider_keys={"localdata": "test-key"}))

    datasets = adapter.list_datasets()

    assert len(datasets) == 2
    assert [dataset.dataset_key for dataset in datasets] == [
        "general_restaurant",
        "rest_cafe",
    ]


def test_build_request_url_missing_base_url_logs_debug(caplog: pytest.LogCaptureFixture) -> None:
    adapter, dataset, _ = _build_adapter_with_transport([])
    dataset = DatasetRef(
        id=dataset.id,
        provider=dataset.provider,
        dataset_key=dataset.dataset_key,
        name=dataset.name,
        representation=dataset.representation,
        operations=dataset.operations,
        raw_metadata=MappingProxyType(
            {k: v for k, v in dataset.raw_metadata.items() if k != "base_url"}
        ),
        query_support=dataset.query_support,
    )

    caplog.set_level(logging.DEBUG, logger="kpubdata.provider.localdata")
    with pytest.raises(ProviderResponseError, match="base_url"):
        adapter.query_records(dataset, Query())

    record = next(
        record
        for record in caplog.records
        if record.getMessage() == "Localdata dataset metadata missing base_url"
    )
    assert record.__dict__["dataset_id"] == dataset.id
