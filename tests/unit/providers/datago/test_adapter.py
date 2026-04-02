from __future__ import annotations

import json
from types import MappingProxyType
from typing import cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.capability import Operation, PaginationMode
from kpubdata.core.models import DatasetRef, Query
from kpubdata.core.representation import Representation
from kpubdata.exceptions import (
    AuthError,
    DatasetNotFoundError,
    InvalidRequestError,
    RateLimitError,
    ServiceUnavailableError,
)
from kpubdata.providers.datago.adapter import DataGoAdapter
from kpubdata.transport.http import HttpTransport


class FakeResponse:
    def __init__(self, payload: dict[str, object], content_type: str = "application/json") -> None:
        self.headers: dict[str, str] = {"content-type": content_type}
        self.text: str = json.dumps(payload)
        self.content: bytes = self.text.encode()


class FakeTransport:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self._responses: list[FakeResponse] = list(responses)
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        return self._responses.pop(0)


def _success_payload(
    *,
    items: object,
    total_count: object,
    num_of_rows: object,
    page_no: object,
) -> dict[str, object]:
    return {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
            "body": {
                "items": {"item": items},
                "totalCount": total_count,
                "numOfRows": num_of_rows,
                "pageNo": page_no,
            },
        }
    }


def _error_payload(code: str, msg: str = "ERROR") -> dict[str, object]:
    return {
        "response": {
            "header": {"resultCode": code, "resultMsg": msg},
            "body": {"items": {"item": []}, "totalCount": 0, "numOfRows": 10, "pageNo": 1},
        }
    }


def _build_adapter_with_transport(
    responses: list[FakeResponse],
) -> tuple[DataGoAdapter, DatasetRef, FakeTransport]:
    transport = FakeTransport(responses)
    config = KPubDataConfig(provider_keys={"datago": "test-key"})
    adapter = DataGoAdapter(
        config=config,
        transport=cast(HttpTransport, cast(object, transport)),
    )
    dataset = adapter.get_dataset("village_fcst")
    return adapter, dataset, transport


class TestDataGoAdapterDiscovery:
    def test_default_catalogue_loads(self) -> None:
        adapter = DataGoAdapter()

        datasets = adapter.list_datasets()
        assert datasets
        assert all(isinstance(dataset, DatasetRef) for dataset in datasets)

    def test_list_datasets_returns_copy(self) -> None:
        adapter = DataGoAdapter()

        first = adapter.list_datasets()
        second = adapter.list_datasets()

        assert first == second
        assert first is not second

    def test_list_datasets_all_datago_provider(self) -> None:
        adapter = DataGoAdapter()

        datasets = adapter.list_datasets()
        assert all(dataset.provider == "datago" for dataset in datasets)

    def test_list_datasets_ids_prefixed(self) -> None:
        adapter = DataGoAdapter()

        datasets = adapter.list_datasets()
        assert all(dataset.id.startswith("datago.") for dataset in datasets)

    def test_get_dataset_found(self) -> None:
        adapter = DataGoAdapter()

        dataset = adapter.get_dataset("village_fcst")
        assert dataset.id == "datago.village_fcst"
        assert dataset.dataset_key == "village_fcst"

    def test_get_dataset_not_found(self) -> None:
        adapter = DataGoAdapter()

        with pytest.raises(DatasetNotFoundError):
            _ = adapter.get_dataset("does_not_exist")

    def test_constructor_override_catalogue(self) -> None:
        custom_dataset = DatasetRef(
            id="datago.custom",
            provider="datago",
            dataset_key="custom",
            name="Custom Dataset",
            representation=Representation.API_JSON,
            operations=frozenset(),
            raw_metadata=MappingProxyType({"base_url": "https://example.test"}),
        )
        adapter = DataGoAdapter(catalogue=[custom_dataset])

        assert adapter.list_datasets() == [custom_dataset]

    def test_search_datasets_match(self) -> None:
        adapter = DataGoAdapter()

        results = adapter.search_datasets("forecast")
        assert results
        assert any(dataset.dataset_key == "village_fcst" for dataset in results)

    def test_search_datasets_no_match(self) -> None:
        adapter = DataGoAdapter()

        assert adapter.search_datasets("zzzzzz-not-a-dataset") == []

    def test_no_api_key_required_for_discovery(self) -> None:
        adapter = DataGoAdapter()

        datasets = adapter.list_datasets()
        assert datasets

        dataset = adapter.get_dataset("village_fcst")
        assert dataset.id == "datago.village_fcst"


class TestDataGoAdapterQueryRecords:
    def test_query_records_single_page(self) -> None:
        payload = _success_payload(
            items=[{"id": 1}, {"id": 2}, {"id": 3}],
            total_count=3,
            num_of_rows=10,
            page_no=1,
        )
        adapter, dataset, transport = _build_adapter_with_transport([FakeResponse(payload)])

        batch = adapter.query_records(dataset, Query())

        assert len(batch.items) == 3
        assert batch.total_count == 3
        assert batch.next_page is None
        assert isinstance(batch.raw, list)
        assert len(batch.raw) == 1
        assert len(transport.calls) == 1

    def test_query_records_multi_page(self) -> None:
        page1 = _success_payload(
            items=[{"id": 1}, {"id": 2}],
            total_count=5,
            num_of_rows=2,
            page_no=1,
        )
        page2 = _success_payload(
            items=[{"id": 3}, {"id": 4}],
            total_count=5,
            num_of_rows=2,
            page_no=2,
        )
        page3 = _success_payload(
            items=[{"id": 5}],
            total_count=5,
            num_of_rows=2,
            page_no=3,
        )
        adapter, dataset, transport = _build_adapter_with_transport(
            [FakeResponse(page1), FakeResponse(page2), FakeResponse(page3)]
        )

        batch = adapter.query_records(dataset, Query(page_size=2))

        assert [item["id"] for item in batch.items] == [1, 2, 3, 4, 5]
        assert batch.total_count == 5
        assert len(transport.calls) == 3

    def test_query_records_single_item_dict(self) -> None:
        payload = _success_payload(items={"id": 1}, total_count=1, num_of_rows=10, page_no=1)
        adapter, dataset, _ = _build_adapter_with_transport([FakeResponse(payload)])

        batch = adapter.query_records(dataset, Query())

        assert batch.items == [{"id": 1}]
        assert batch.total_count == 1

    def test_query_records_empty_items(self) -> None:
        payload = _success_payload(items=None, total_count=0, num_of_rows=10, page_no=1)
        adapter, dataset, _ = _build_adapter_with_transport([FakeResponse(payload)])

        batch = adapter.query_records(dataset, Query())

        assert batch.items == []
        assert batch.total_count == 0

    def test_query_records_string_numerics(self) -> None:
        payload = _success_payload(
            items=[{"id": 1}], total_count="1", num_of_rows="10", page_no="1"
        )
        adapter, dataset, _ = _build_adapter_with_transport([FakeResponse(payload)])

        batch = adapter.query_records(dataset, Query(page=1, page_size=10))

        assert batch.total_count == 1
        assert len(batch.items) == 1

    def test_query_records_auth_error_30(self) -> None:
        adapter, dataset, _ = _build_adapter_with_transport([FakeResponse(_error_payload("30"))])

        with pytest.raises(AuthError):
            _ = adapter.query_records(dataset, Query())

    def test_query_records_rate_limit_22(self) -> None:
        adapter, dataset, _ = _build_adapter_with_transport([FakeResponse(_error_payload("22"))])

        with pytest.raises(RateLimitError) as excinfo:
            _ = adapter.query_records(dataset, Query())

        assert excinfo.value.retryable is False

    def test_query_records_invalid_request_10(self) -> None:
        adapter, dataset, _ = _build_adapter_with_transport([FakeResponse(_error_payload("10"))])

        with pytest.raises(InvalidRequestError):
            _ = adapter.query_records(dataset, Query())

    def test_query_records_dataset_not_found_12(self) -> None:
        adapter, dataset, _ = _build_adapter_with_transport([FakeResponse(_error_payload("12"))])

        with pytest.raises(DatasetNotFoundError):
            _ = adapter.query_records(dataset, Query())

    def test_query_records_service_unavailable_01(self) -> None:
        adapter, dataset, _ = _build_adapter_with_transport([FakeResponse(_error_payload("01"))])

        with pytest.raises(ServiceUnavailableError):
            _ = adapter.query_records(dataset, Query())

    def test_query_records_filters_passed(self) -> None:
        payload = _success_payload(items=[{"id": 1}], total_count=1, num_of_rows=10, page_no=1)
        adapter, dataset, transport = _build_adapter_with_transport([FakeResponse(payload)])

        _ = adapter.query_records(dataset, Query(filters={"stationName": "Seoul", "page": 1}))

        params = transport.calls[0]["params"]
        assert isinstance(params, dict)
        assert params["stationName"] == "Seoul"
        assert params["page"] == "1"

    def test_query_records_reserved_keys_protected(self) -> None:
        payload = _success_payload(items=[{"id": 1}], total_count=1, num_of_rows=10, page_no=1)
        adapter, dataset, transport = _build_adapter_with_transport([FakeResponse(payload)])

        _ = adapter.query_records(
            dataset,
            Query(
                filters={
                    "serviceKey": "bad-key",
                    "pageNo": "999",
                    "numOfRows": "999",
                    "x": "ok",
                }
            ),
        )

        params = transport.calls[0]["params"]
        assert isinstance(params, dict)
        assert params["serviceKey"] == "test-key"
        assert params["pageNo"] == "1"
        assert params["numOfRows"] == "10"
        assert params["x"] == "ok"


class TestDataGoAdapterCallRaw:
    def test_call_raw_returns_full_payload(self) -> None:
        payload = _success_payload(items=[{"id": 1}], total_count=1, num_of_rows=1, page_no=1)
        adapter, dataset, _ = _build_adapter_with_transport([FakeResponse(payload)])

        result = adapter.call_raw(dataset, "getVilageFcst", {"base_date": "20250101"})

        assert result == payload

    def test_call_raw_custom_operation(self) -> None:
        payload = _success_payload(items=[{"id": 1}], total_count=1, num_of_rows=1, page_no=1)
        adapter, dataset, transport = _build_adapter_with_transport([FakeResponse(payload)])

        _ = adapter.call_raw(dataset, "customOperation", {"foo": "bar"})

        url = transport.calls[0]["url"]
        assert isinstance(url, str)
        assert url.endswith("/customOperation")

    def test_call_raw_error_mapped(self) -> None:
        adapter, dataset, _ = _build_adapter_with_transport([FakeResponse(_error_payload("30"))])

        with pytest.raises(AuthError):
            _ = adapter.call_raw(dataset, "getVilageFcst", {})


class TestDataGoAdapterCatalogueOperations:
    def test_default_catalogue_has_operations(self) -> None:
        adapter = DataGoAdapter()

        datasets = adapter.list_datasets()
        assert datasets
        for dataset in datasets:
            assert Operation.LIST in dataset.operations
            assert Operation.RAW in dataset.operations

    def test_default_catalogue_has_query_support(self) -> None:
        adapter = DataGoAdapter()

        datasets = adapter.list_datasets()
        assert datasets
        for dataset in datasets:
            assert dataset.query_support is not None
            assert dataset.query_support.pagination is PaginationMode.OFFSET
            assert dataset.query_support.max_page_size == 1000


class TestDataGoAdapterXml:
    def test_query_records_xml_multi_item(self, configured_adapter) -> None:
        adapter, dataset, _ = configured_adapter(["success_xml.xml"], content_type="text/xml")
        batch = adapter.query_records(dataset, Query())

        assert len(batch.items) == 2
        assert batch.items[0]["stationName"] == "종로구"
        assert batch.items[1]["stationName"] == "강남구"
        assert batch.total_count == 2

    def test_query_records_xml_single_item(self, configured_adapter) -> None:
        adapter, dataset, _ = configured_adapter(
            ["success_xml_single_item.xml"], content_type="text/xml"
        )
        batch = adapter.query_records(dataset, Query())

        assert len(batch.items) == 1
        assert batch.items[0]["stationName"] == "종로구"
        assert batch.total_count == 1

    def test_call_raw_xml_response(self, configured_adapter) -> None:
        adapter, dataset, _ = configured_adapter(["success_xml.xml"], content_type="text/xml")
        result = adapter.call_raw(dataset, "getVilageFcst", {})

        assert isinstance(result, dict)
        assert result["response"]["header"]["resultCode"] == "00"

    def test_xml_error_maps_to_exception(self, configured_adapter) -> None:
        adapter, dataset, _ = configured_adapter(["error_xml_auth_30.xml"], content_type="text/xml")
        with pytest.raises(AuthError):
            _ = adapter.query_records(dataset, Query())
