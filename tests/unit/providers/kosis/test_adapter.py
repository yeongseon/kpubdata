from __future__ import annotations

import json
import logging
from importlib.resources import files
from typing import cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.exceptions import InvalidRequestError
from kpubdata.providers._common import build_dataset_ref
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
    *,
    dataset_key: str = "population_migration",
) -> tuple[KosisAdapter, DatasetRef, FakeTransport]:
    transport = FakeTransport(responses)
    adapter = KosisAdapter(
        config=KPubDataConfig(provider_keys={"kosis": "test-key"}),
        transport=cast(HttpTransport, cast(object, transport)),
    )
    dataset = adapter.get_dataset(dataset_key)
    return adapter, dataset, transport


def test_catalogue_parses_industrial_production_default_query_params() -> None:
    _, dataset, _ = _build_adapter_with_transport([], dataset_key="industrial_production")
    catalogue = cast(
        list[dict[str, object]],
        json.loads(files("kpubdata.providers.kosis").joinpath("catalogue.json").read_text()),
    )
    entry = next(entry for entry in catalogue if entry["dataset_key"] == "industrial_production")

    assert dataset.id == "kosis.industrial_production"
    assert dataset.raw_metadata["org_id"] == "101"
    assert dataset.raw_metadata["tbl_id"] == "DT_1J22003"
    assert dataset.raw_metadata["default_query_params"] == {
        "objL1": "T10",
        "itmId": "T",
        "prdSe": "M",
    }
    assert entry["default_query_params"] == {
        "objL1": "T10",
        "itmId": "T",
        "prdSe": "M",
    }


def test_adapter_docstring_documents_default_query_params_merge_rule() -> None:
    assert KosisAdapter.__doc__ is not None
    assert "dataset default_query_params < query.filters (caller wins)" in KosisAdapter.__doc__


def test_query_records_missing_start_date_logs_debug(caplog: pytest.LogCaptureFixture) -> None:
    adapter, dataset, _ = _build_adapter_with_transport([])

    caplog.set_level(logging.DEBUG, logger="kpubdata.provider.kosis")
    with pytest.raises(InvalidRequestError, match="start_date"):
        _ = adapter.query_records(dataset, Query(end_date="202401"))

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


def test_population_migration_keeps_hardcoded_default_query_params() -> None:
    adapter, dataset, transport = _build_adapter_with_transport([FakeResponse([])])

    batch = adapter.query_records(dataset, Query(start_date="202401", end_date="202401"))

    assert batch.items == []
    request_url = cast(str, transport.calls[0]["url"])
    assert "objL1=ALL" in request_url
    assert "objL2=ALL" in request_url
    assert "itmId=ALL" in request_url
    assert "prdSe=M" in request_url


def test_query_records_applies_dataset_default_query_params_when_filters_absent() -> None:
    adapter, dataset, transport = _build_adapter_with_transport(
        [FakeResponse([])],
        dataset_key="industrial_production",
    )

    _ = adapter.query_records(dataset, Query(start_date="202401", end_date="202401"))

    request_url = cast(str, transport.calls[0]["url"])
    assert "objL1=T10" in request_url
    assert "itmId=T" in request_url
    assert "prdSe=M" in request_url
    assert "objL2=ALL" not in request_url


def test_query_records_merges_default_query_params_but_query_filters_win() -> None:
    adapter, dataset, transport = _build_adapter_with_transport(
        [FakeResponse([])],
        dataset_key="industrial_production",
    )

    _ = adapter.query_records(
        dataset,
        Query(
            start_date="202401",
            end_date="202401",
            filters={"objL1": "T20", "itmId": "X", "prdSe": "Q"},
        ),
    )

    request_url = cast(str, transport.calls[0]["url"])
    assert "objL1=T20" in request_url
    assert "itmId=X" in request_url
    assert "prdSe=Q" in request_url
    assert "objL1=T10" not in request_url
    assert "itmId=T" not in request_url


def test_query_records_ignores_non_kosis_default_query_param_keys() -> None:
    adapter, _, transport = _build_adapter_with_transport([FakeResponse([])])
    dataset = build_dataset_ref(
        "kosis",
        {
            "dataset_key": "custom_defaults",
            "name": "Custom Defaults",
            "representation": "api_json",
            "base_url": "https://kosis.kr/openapi/Param/statisticsParameterData.do",
            "org_id": "101",
            "tbl_id": "DT_1J22003",
            "default_query_params": {
                "objL1": "T10",
                "itmId": "T",
                "unknown": "ignored",
                "apiKey": "ignored",
            },
        },
    )

    _ = adapter.query_records(dataset, Query(start_date="202401", end_date="202401"))

    request_url = cast(str, transport.calls[0]["url"])
    assert "objL1=T10" in request_url
    assert "itmId=T" in request_url
    assert "unknown=ignored" not in request_url
    assert request_url.count("apiKey=") == 1
