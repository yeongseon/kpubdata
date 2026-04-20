from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.exceptions import AuthError
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


def test_query_records_parses_success_fixture() -> None:
    payload = _load_fixture("general_restaurant_success.json")
    adapter, dataset, transport = _build_adapter_with_transport([FakeResponse(payload)])

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 3
    assert batch.total_count == 3
    assert batch.next_page is None
    assert batch.raw == payload
    assert batch.items[0]["bplcNm"] == "한밥식당"
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

    request_url = cast(str, transport.calls[0]["url"])
    assert "authKey=test-key" in request_url
    assert "opnSvcId=07_24_04_P" in request_url
    assert "resultType=json" in request_url
    assert "pageIndex=1" in request_url
    assert "pageSize=100" in request_url
    assert "localCode=41135" in request_url
