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


def _build_dataset_adapter_with_transport(
    dataset_key: str,
    responses: list[FakeResponse],
) -> tuple[LocaldataAdapter, DatasetRef, FakeTransport]:
    transport = FakeTransport(responses)
    adapter = LocaldataAdapter(
        config=KPubDataConfig(provider_keys={"localdata": "test-key"}),
        transport=cast(HttpTransport, cast(object, transport)),
    )
    dataset = adapter.get_dataset(dataset_key)
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
    adapter, dataset, _ = _build_dataset_adapter_with_transport(
        "rest_cafe", [FakeResponse(payload)]
    )

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 3
    assert batch.items[0]["BPLC_NM"] == "카페모카"


def test_adapter_lists_all_datasets() -> None:
    adapter = LocaldataAdapter(config=KPubDataConfig(provider_keys={"localdata": "test-key"}))

    datasets = adapter.list_datasets()

    assert len(datasets) == 26
    assert [dataset.dataset_key for dataset in datasets] == [
        "general_restaurant",
        "rest_cafe",
        "bakery",
        "hospital",
        "clinic",
        "pharmacy",
        "animal_hospital",
        "optical_shop",
        "public_bath",
        "laundry",
        "barber_shop",
        "beauty_salon",
        "pet_grooming",
        "dance_academy",
        "karaoke",
        "singing_bar",
        "billiard_hall",
        "performance_hall",
        "movie_theater",
        "swimming_pool",
        "fitness_center",
        "ice_rink",
        "golf_course",
        "golf_practice_range",
        "horse_riding",
        "ski_resort",
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


# --- New dataset fixture parsing tests ---


_NEW_DATASETS = [
    ("bakery", "bakery_success.json", "중앙베이커리"),
    ("hospital", "hospital_success.json", "중앙내과의원"),
    ("clinic", "clinic_success.json", "대흥가정의원"),
    ("pharmacy", "pharmacy_success.json", "중앙약국"),
    ("animal_hospital", "animal_hospital_success.json", "중앙24시동물병원"),
    ("optical_shop", "optical_shop_success.json", "선화안경원"),
    ("public_bath", "public_bath_success.json", "중앙대중목욕탕"),
    ("laundry", "laundry_success.json", "깨끗한세탁소"),
    ("barber_shop", "barber_shop_success.json", "클래식이발관"),
    ("beauty_salon", "beauty_salon_success.json", "뷰티헤어살롱"),
    ("pet_grooming", "pet_grooming_success.json", "멍멍살롱중앙점"),
    ("dance_academy", "dance_academy_success.json", "대전리듬댄스학원"),
    ("karaoke", "karaoke_success.json", "노래천국"),
    ("singing_bar", "singing_bar_success.json", "은행스타유흥주점"),
    ("billiard_hall", "billiard_hall_success.json", "유천당구클럽"),
    ("performance_hall", "performance_hall_success.json", "중앙소극장"),
    ("movie_theater", "movie_theater_success.json", "중앙시네마"),
    ("swimming_pool", "swimming_pool_success.json", "산성아쿠아센터"),
    ("fitness_center", "fitness_center_success.json", "태평피트니스클럽"),
    ("ice_rink", "ice_rink_success.json", "대전아이스링크"),
    ("golf_course", "golf_course_success.json", "대전힐즈골프장"),
    (
        "golf_practice_range",
        "golf_practice_range_success.json",
        "문화스크린골프연습장",
    ),
    ("horse_riding", "horse_riding_success.json", "보문승마클럽"),
    ("ski_resort", "ski_resort_success.json", "대전스노우리조트"),
]


@pytest.mark.parametrize(
    ("dataset_key", "fixture_name", "expected_first_name"),
    _NEW_DATASETS,
    ids=[d[0] for d in _NEW_DATASETS],
)
def test_new_dataset_query_records_parses_success_fixture(
    dataset_key: str,
    fixture_name: str,
    expected_first_name: str,
) -> None:
    payload = _load_fixture(fixture_name)
    adapter, dataset, _ = _build_dataset_adapter_with_transport(
        dataset_key, [FakeResponse(payload)]
    )

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 3
    assert batch.total_count == 3
    assert batch.items[0]["BPLC_NM"] == expected_first_name
