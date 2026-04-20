from __future__ import annotations

import json
import logging
from typing import cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.exceptions import InvalidRequestError
from kpubdata.providers.bok.adapter import BokAdapter
from kpubdata.transport.http import HttpTransport


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


def _success_payload(*, items: object, total_count: object) -> dict[str, object]:
    return {
        "StatisticSearch": {
            "list_total_count": total_count,
            "row": items,
        }
    }


def _build_adapter_with_transport(
    responses: list[FakeResponse],
) -> tuple[BokAdapter, DatasetRef, FakeTransport]:
    transport = FakeTransport(responses)
    adapter = BokAdapter(
        config=KPubDataConfig(provider_keys={"bok": "test-key"}),
        transport=cast(HttpTransport, cast(object, transport)),
    )
    dataset = adapter.get_dataset("base_rate")
    return adapter, dataset, transport


def test_query_records_returns_single_page_and_sets_next_page() -> None:
    payload = _success_payload(items=[{"id": 1}, {"id": 2}], total_count=5)
    adapter, dataset, transport = _build_adapter_with_transport([FakeResponse(payload)])

    batch = adapter.query_records(
        dataset,
        Query(page=1, page_size=2, start_date="202401", end_date="202403"),
    )

    assert batch.items == [{"id": 1}, {"id": 2}]
    assert batch.total_count == 5
    assert batch.next_page == 2
    assert batch.raw == payload
    assert len(transport.calls) == 1


def test_query_records_uses_default_page_size_100() -> None:
    payload = _success_payload(items=[{"id": 1}], total_count=1)
    adapter, dataset, transport = _build_adapter_with_transport([FakeResponse(payload)])

    _ = adapter.query_records(dataset, Query(start_date="202401", end_date="202403"))

    request_url = cast(str, transport.calls[0]["url"])
    assert "/1/100/" in request_url


def test_query_records_uses_heuristic_next_page_without_total_count() -> None:
    payload = _success_payload(items=[{"id": 1}, {"id": 2}], total_count=None)
    adapter, dataset, _ = _build_adapter_with_transport([FakeResponse(payload)])

    batch = adapter.query_records(
        dataset,
        Query(page=1, page_size=2, start_date="202401", end_date="202403"),
    )

    assert batch.total_count is None
    assert batch.next_page == 2


def test_query_records_missing_dates_logs_debug(caplog: pytest.LogCaptureFixture) -> None:
    adapter, dataset, _ = _build_adapter_with_transport([])

    caplog.set_level(logging.DEBUG, logger="kpubdata.provider.bok")
    with pytest.raises(InvalidRequestError, match="start_date and end_date"):
        adapter.query_records(dataset, Query())

    record = next(
        record
        for record in caplog.records
        if record.getMessage() == "BOK ECOS invalid query: missing start/end date"
    )
    assert record.__dict__["dataset_id"] == dataset.id


def test_query_records_zero_items_logs_debug(caplog: pytest.LogCaptureFixture) -> None:
    payload = _success_payload(items=[], total_count=0)
    adapter, dataset, _ = _build_adapter_with_transport([FakeResponse(payload)])

    caplog.set_level(logging.DEBUG, logger="kpubdata.provider.bok")
    batch = adapter.query_records(
        dataset,
        Query(page=1, page_size=10, start_date="202401", end_date="202403"),
    )

    assert batch.items == []
    record = next(
        record for record in caplog.records if record.getMessage() == "BOK envelope: zero items"
    )
    assert record.__dict__["dataset_id"] == dataset.id
    assert record.__dict__["page"] == 1
    assert record.__dict__["page_size"] == 10
    assert record.__dict__["total_count"] == 0
