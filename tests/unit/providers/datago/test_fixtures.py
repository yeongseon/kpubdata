from __future__ import annotations

from typing import Protocol, cast

import pytest

from kpubdata.core.models import DatasetRef, Query
from kpubdata.exceptions import (
    AuthError,
    InvalidRequestError,
    RateLimitError,
    ServiceUnavailableError,
)
from kpubdata.providers.datago.adapter import DataGoAdapter

from .conftest import FixtureTransport, load_json_fixture


class AdapterFactory(Protocol):
    def __call__(
        self,
        fixture_names: list[str],
        content_type: str = "application/json",
    ) -> tuple[DataGoAdapter, DatasetRef, FixtureTransport]: ...


def test_fixture_single_page(configured_adapter: AdapterFactory) -> None:
    adapter, dataset, _ = configured_adapter(["success_single_page.json"])

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 3
    assert batch.total_count == 3
    assert batch.next_page is None
    assert isinstance(batch.raw, dict)


def test_fixture_multi_page_pagination(configured_adapter: AdapterFactory) -> None:
    adapter, dataset, _ = configured_adapter(
        ["success_multi_page_1.json", "success_multi_page_2.json"]
    )

    batch = adapter.query_records(dataset, Query(page_size=2))

    assert len(batch.items) == 2
    assert [item["stationName"] for item in batch.items] == ["종로구", "강남구"]
    assert batch.next_page == 2


def test_fixture_single_item_normalization(configured_adapter: AdapterFactory) -> None:
    adapter, dataset, _ = configured_adapter(["success_single_item.json"])

    batch = adapter.query_records(dataset, Query())

    assert batch.items == [{"stationName": "종로구", "pm10Value": "45"}]
    assert batch.total_count == 1


def test_fixture_empty_response(configured_adapter: AdapterFactory) -> None:
    adapter, dataset, _ = configured_adapter(["success_empty.json"])

    batch = adapter.query_records(dataset, Query())

    assert batch.items == []
    assert batch.total_count is None


def test_fixture_string_numerics(configured_adapter: AdapterFactory) -> None:
    adapter, dataset, _ = configured_adapter(["success_string_numerics.json"])

    batch = adapter.query_records(dataset, Query(page=1, page_size=100))

    assert isinstance(batch.total_count, int)
    assert batch.total_count == 1


def test_fixture_auth_error(configured_adapter: AdapterFactory) -> None:
    adapter, dataset, _ = configured_adapter(["error_auth_30.json"])

    with pytest.raises(AuthError) as excinfo:
        _ = adapter.query_records(dataset, Query())

    assert excinfo.value.provider_code == "30"


def test_fixture_rate_limit(configured_adapter: AdapterFactory) -> None:
    adapter, dataset, _ = configured_adapter(["error_rate_limit_22.json"])

    with pytest.raises(RateLimitError) as excinfo:
        _ = adapter.query_records(dataset, Query())

    assert excinfo.value.provider_code == "22"
    assert excinfo.value.retryable is False


def test_fixture_invalid_request(configured_adapter: AdapterFactory) -> None:
    adapter, dataset, _ = configured_adapter(["error_invalid_request_10.json"])

    with pytest.raises(InvalidRequestError):
        _ = adapter.query_records(dataset, Query())


def test_fixture_service_unavailable(configured_adapter: AdapterFactory) -> None:
    adapter, dataset, _ = configured_adapter(["error_service_unavailable_01.json"])

    with pytest.raises(ServiceUnavailableError):
        _ = adapter.query_records(dataset, Query())


def test_fixture_xml_response(configured_adapter: AdapterFactory) -> None:
    pytest.importorskip("xmltodict")
    adapter, dataset, _ = configured_adapter(["success_xml.xml"], "application/xml")

    batch = adapter.query_records(dataset, Query())

    assert [item["stationName"] for item in batch.items] == ["종로구", "강남구"]
    assert batch.total_count == 2


def test_fixture_records_have_korean_text(configured_adapter: AdapterFactory) -> None:
    adapter, dataset, _ = configured_adapter(["success_single_page.json"])

    batch = adapter.query_records(dataset, Query())

    assert batch.items[0]["stationName"] == "종로구"
    assert batch.items[1]["stationName"] == "강남구"


def test_fixture_call_raw_returns_full_envelope(configured_adapter: AdapterFactory) -> None:
    adapter, dataset, _ = configured_adapter(["success_single_page.json"])
    expected = load_json_fixture("success_single_page.json")

    payload = adapter.call_raw(dataset, "getVilageFcst", {})

    assert payload == expected
    payload_dict = cast(dict[str, object], payload)
    response = payload_dict["response"]
    assert isinstance(response, dict)
    assert "header" in response
    assert "body" in response
