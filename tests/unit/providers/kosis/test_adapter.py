from __future__ import annotations

import json
import logging
from typing import cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.exceptions import InvalidRequestError
from kpubdata.providers.kosis.adapter import KosisAdapter
from kpubdata.transport.http import HttpTransport


class FakeResponse:
    def __init__(self, payload: object) -> None:
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
) -> tuple[KosisAdapter, DatasetRef, FakeTransport]:
    transport = FakeTransport(responses)
    adapter = KosisAdapter(
        config=KPubDataConfig(provider_keys={"kosis": "test-key"}),
        transport=cast(HttpTransport, cast(object, transport)),
    )
    dataset = adapter.get_dataset("population_migration")
    return adapter, dataset, transport


def test_query_records_missing_start_date_logs_debug(caplog: pytest.LogCaptureFixture) -> None:
    adapter, dataset, _ = _build_adapter_with_transport([])

    caplog.set_level(logging.DEBUG, logger="kpubdata.provider.kosis")
    with pytest.raises(InvalidRequestError, match="start_date"):
        adapter.query_records(dataset, Query(end_date="202401"))

    record = next(
        record
        for record in caplog.records
        if record.getMessage() == "KOSIS invalid query: missing start_date"
    )
    assert record.__dict__["dataset_id"] == dataset.id


def test_query_records_zero_items_logs_debug(caplog: pytest.LogCaptureFixture) -> None:
    adapter, dataset, _ = _build_adapter_with_transport([FakeResponse([])])

    caplog.set_level(logging.DEBUG, logger="kpubdata.provider.kosis")
    batch = adapter.query_records(dataset, Query(start_date="202401", end_date="202401"))

    assert batch.items == []
    record = next(
        record for record in caplog.records if record.getMessage() == "KOSIS envelope: zero items"
    )
    assert record.__dict__["dataset_id"] == dataset.id
    assert record.__dict__["page"] is None
    assert record.__dict__["page_size"] == 100
    assert record.__dict__["total_count"] == 0
