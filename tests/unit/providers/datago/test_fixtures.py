from __future__ import annotations

from typing import Protocol, cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.exceptions import (
    AuthError,
    InvalidRequestError,
    RateLimitError,
    ServiceUnavailableError,
)
from kpubdata.providers.datago.adapter import DataGoAdapter
from kpubdata.transport.http import HttpTransport

from .conftest import FixtureTransport, load_fixture_bytes, load_json_fixture


class AdapterFactory(Protocol):
    def __call__(
        self,
        fixture_names: list[str],
        content_type: str = "application/json",
    ) -> tuple[DataGoAdapter, DatasetRef, FixtureTransport]: ...


def _build_real_estate_adapter(
    fixture_name: str, dataset_key: str
) -> tuple[DataGoAdapter, DatasetRef]:
    data = load_fixture_bytes(fixture_name)

    class _FakeResponse:
        def __init__(self) -> None:
            self.headers: dict[str, str] = {"content-type": "application/json"}
            self.content: bytes = data
            self.text: str = data.decode("utf-8")

    class _FakeTransport:
        def request(self, _method: str, _url: str, **_kwargs: object) -> _FakeResponse:
            return _FakeResponse()

    config = KPubDataConfig(provider_keys={"datago": "test-key"})
    adapter = DataGoAdapter(
        config=config,
        transport=cast(HttpTransport, cast(object, _FakeTransport())),
    )
    dataset = adapter.get_dataset(dataset_key)
    return adapter, dataset


def test_fixture_bus_arrival_v2_call_raw_returns_full_envelope() -> None:
    adapter, dataset = _build_real_estate_adapter("bus_arrival_v2.json", "bus_arrival")
    expected = load_json_fixture("bus_arrival_v2.json")

    payload = adapter.call_raw(dataset, "getBusArrivalListv2", {"stationId": "228000704"})

    assert payload == expected
    payload_dict = cast(dict[str, object], payload)
    response = payload_dict["response"]
    assert isinstance(response, dict)
    assert "msgHeader" in response
    assert "msgBody" in response


def test_fixture_bus_arrival_v2_list_normalizes_msg_body_list() -> None:
    adapter, dataset = _build_real_estate_adapter("bus_arrival_v2.json", "bus_arrival")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 1
    assert batch.items[0]["routeId"] == 200000333
    assert batch.items[0]["stationId"] == 228000704
    assert batch.total_count is None


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


def test_fixture_apt_rent_parses() -> None:
    adapter, dataset = _build_real_estate_adapter("success_apt_rent.json", "apt_rent")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "deposit" in batch.items[0]
    assert "monthlyRent" in batch.items[0]
    assert batch.total_count == 2


def test_fixture_offi_trade_parses() -> None:
    adapter, dataset = _build_real_estate_adapter("success_offi_trade.json", "offi_trade")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "dealAmount" in batch.items[0]
    assert batch.total_count == 2


def test_fixture_offi_rent_parses() -> None:
    adapter, dataset = _build_real_estate_adapter("success_offi_rent.json", "offi_rent")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "deposit" in batch.items[0]
    assert "monthlyRent" in batch.items[0]
    assert batch.total_count == 2


def test_fixture_rh_trade_parses() -> None:
    adapter, dataset = _build_real_estate_adapter("success_rh_trade.json", "rh_trade")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "dealAmount" in batch.items[0]
    assert batch.total_count == 2


def test_fixture_rh_rent_parses() -> None:
    adapter, dataset = _build_real_estate_adapter("success_rh_rent.json", "rh_rent")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "deposit" in batch.items[0]
    assert "monthlyRent" in batch.items[0]
    assert batch.total_count == 2


def test_fixture_sh_trade_parses() -> None:
    adapter, dataset = _build_real_estate_adapter("success_sh_trade.json", "sh_trade")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "dealAmount" in batch.items[0]
    assert batch.total_count == 2


def test_fixture_sh_rent_parses() -> None:
    adapter, dataset = _build_real_estate_adapter("success_sh_rent.json", "sh_rent")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "deposit" in batch.items[0]
    assert "monthlyRent" in batch.items[0]
    assert batch.total_count == 2


def test_fixture_tour_kor_area_parses() -> None:
    adapter, dataset = _build_real_estate_adapter("success_tour_kor_area.json", "tour_kor_area")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert batch.items[0]["title"] == "경복궁"
    assert "contentid" in batch.items[0]
    assert batch.total_count == 2


def test_fixture_tour_kor_location_parses() -> None:
    adapter, dataset = _build_real_estate_adapter(
        "success_tour_kor_location.json", "tour_kor_location"
    )

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "dist" in batch.items[0]
    assert batch.total_count == 2


def test_fixture_tour_kor_keyword_parses() -> None:
    adapter, dataset = _build_real_estate_adapter(
        "success_tour_kor_keyword.json", "tour_kor_keyword"
    )

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "title" in batch.items[0]
    assert batch.total_count == 2


def test_fixture_tour_kor_festival_parses() -> None:
    adapter, dataset = _build_real_estate_adapter(
        "success_tour_kor_festival.json", "tour_kor_festival"
    )

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "eventstartdate" in batch.items[0]
    assert "eventenddate" in batch.items[0]
    assert batch.total_count == 2


def test_fixture_metro_fare_parses() -> None:
    adapter, dataset = _build_real_estate_adapter("success_metro_fare.json", "metro_fare")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "startStation" in batch.items[0]
    assert "endStation" in batch.items[0]
    assert "fareCard" in batch.items[0]
    assert batch.total_count == 2


def test_fixture_metro_path_parses() -> None:
    adapter, dataset = _build_real_estate_adapter("success_metro_path.json", "metro_path")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 3
    assert batch.items[0]["stationName"] == "서울역"
    assert "lineNum" in batch.items[0]
    assert batch.total_count == 3


def test_fixture_building_title_parses() -> None:
    adapter, dataset = _build_real_estate_adapter("success_building_title.json", "building_title")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "bldNm" in batch.items[0]
    assert batch.total_count == 2


def test_fixture_building_recap_title_parses() -> None:
    adapter, dataset = _build_real_estate_adapter(
        "success_building_recap_title.json", "building_recap_title"
    )

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "vlRat" in batch.items[0]
    assert "bcRat" in batch.items[0]
    assert batch.total_count == 2


def test_fixture_building_floor_parses() -> None:
    adapter, dataset = _build_real_estate_adapter("success_building_floor.json", "building_floor")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "flrNo" in batch.items[0]
    assert "area" in batch.items[0]
    assert batch.total_count == 2


def test_fixture_building_area_parses() -> None:
    adapter, dataset = _build_real_estate_adapter("success_building_area.json", "building_area")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "hoNm" in batch.items[0]
    assert "exposPubuseGbCdNm" in batch.items[0]
    assert batch.total_count == 2


def test_fixture_g2b_contract_parses() -> None:
    adapter, dataset = _build_real_estate_adapter("success_g2b_contract.json", "g2b_contract")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "cntrctSn" in batch.items[0]
    assert "prdctNm" in batch.items[0]
    assert "cntrctAmt" in batch.items[0]
    assert batch.total_count == 2


def test_fixture_social_enterprise_parses() -> None:
    adapter, dataset = _build_real_estate_adapter(
        "success_social_enterprise.json", "social_enterprise"
    )

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "entNmV" in batch.items[0]
    assert "certiNumV" in batch.items[0]
    assert batch.total_count == 4783


def test_fixture_g2b_catalog_parses() -> None:
    adapter, dataset = _build_real_estate_adapter("success_g2b_catalog.json", "g2b_catalog")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "prdctIdntNo" in batch.items[0]
    assert "prdctNm" in batch.items[0]
    assert "crtfcTyNm" in batch.items[0]
    assert batch.total_count == 2
