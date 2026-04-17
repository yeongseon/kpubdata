from __future__ import annotations

import json
from pathlib import Path
from types import MappingProxyType
from typing import cast

from kpubdata.core.capability import Operation, PaginationMode, QuerySupport
from kpubdata.core.models import DatasetRef, Query, RecordBatch
from kpubdata.core.representation import Representation

REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOGUE_PATH = REPO_ROOT / "src/kpubdata/providers/datago/catalogue.json"
FIXTURES_DIR = REPO_ROOT / "tests/fixtures/datago"


def _load_catalogue_entries() -> tuple[dict[str, object], dict[str, object]]:
    catalogue = cast(
        list[dict[str, object]],
        json.loads(CATALOGUE_PATH.read_text(encoding="utf-8")),
    )
    return catalogue[0], catalogue[1]


def _make_ref(entry: dict[str, object]) -> DatasetRef:
    return DatasetRef(
        id=f"datago.{entry['dataset_key']}",
        provider="datago",
        dataset_key=str(entry["dataset_key"]),
        name=str(entry["name"]),
        representation=Representation.API_JSON,
        operations=frozenset({Operation.LIST, Operation.RAW}),
        query_support=QuerySupport(
            pagination=PaginationMode.OFFSET,
            max_page_size=1000,
        ),
        raw_metadata=MappingProxyType(
            {
                "base_url": entry["base_url"],
                "default_operation": entry["default_operation"],
                "service_key_param": entry["service_key_param"],
            }
        ),
    )


def _load_fixture(name: str) -> dict[str, object]:
    return cast(
        dict[str, object],
        json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8")),
    )


def _response_body(payload: dict[str, object]) -> dict[str, object]:
    response = cast(dict[str, object], payload["response"])
    return cast(dict[str, object], response["body"])


def _items_node(body: dict[str, object]) -> dict[str, object] | None:
    return cast(dict[str, object] | None, body["items"])


def _items_list_from_body(body: dict[str, object]) -> list[dict[str, object]]:
    items = cast(dict[str, object], body["items"])
    return cast(list[dict[str, object]], items["item"])


class TestDatasetRefFromCatalogue:
    def test_first_entry_core_fields(self) -> None:
        first_entry, _ = _load_catalogue_entries()
        ref = _make_ref(first_entry)

        assert ref.id == f"datago.{first_entry['dataset_key']}"
        assert ref.provider == "datago"
        assert ref.dataset_key == first_entry["dataset_key"]
        assert ref.name == first_entry["name"]
        assert ref.representation == Representation.API_JSON

    def test_second_entry_core_fields(self) -> None:
        _, second_entry = _load_catalogue_entries()
        ref = _make_ref(second_entry)

        assert ref.id == f"datago.{second_entry['dataset_key']}"
        assert ref.provider == "datago"
        assert ref.dataset_key == second_entry["dataset_key"]
        assert ref.name == second_entry["name"]
        assert ref.representation == Representation.API_JSON

    def test_operations_are_list_and_raw(self) -> None:
        first_entry, _ = _load_catalogue_entries()
        ref = _make_ref(first_entry)

        assert ref.operations == frozenset({Operation.LIST, Operation.RAW})

    def test_query_support_offset_with_max_page_size(self) -> None:
        _, second_entry = _load_catalogue_entries()
        ref = _make_ref(second_entry)

        assert ref.query_support is not None
        assert ref.query_support.pagination == PaginationMode.OFFSET
        assert ref.query_support.max_page_size == 1000

    def test_raw_metadata_is_mapping_proxy_with_required_keys(self) -> None:
        first_entry, _ = _load_catalogue_entries()
        ref = _make_ref(first_entry)

        assert isinstance(ref.raw_metadata, MappingProxyType)
        assert "base_url" in ref.raw_metadata
        assert "default_operation" in ref.raw_metadata
        assert "service_key_param" in ref.raw_metadata

    def test_supports_list_and_not_get(self) -> None:
        first_entry, _ = _load_catalogue_entries()
        ref = _make_ref(first_entry)

        assert ref.supports(Operation.LIST) is True
        assert ref.supports(Operation.SCHEMA) is False

    def test_is_frozen(self) -> None:
        first_entry, _ = _load_catalogue_entries()
        ref = _make_ref(first_entry)
        attr = "id"

        try:
            setattr(ref, attr, "datago.changed")
            raise AssertionError("DatasetRef should be frozen")
        except AttributeError:
            pass


class TestRecordBatchFromFixtures:
    def test_single_page_batch_shape(self) -> None:
        first_entry, _ = _load_catalogue_entries()
        ref = _make_ref(first_entry)
        payload = _load_fixture("success_single_page.json")
        body = _response_body(payload)
        items_list = _items_list_from_body(body)
        batch = RecordBatch(items=items_list, dataset=ref, total_count=3, raw=payload)

        assert len(batch) == 3
        assert bool(batch) is True
        assert list(batch) == items_list
        assert batch.total_count == 3
        assert batch.raw is payload

    def test_single_item_fixture_normalized_to_list(self) -> None:
        first_entry, _ = _load_catalogue_entries()
        ref = _make_ref(first_entry)
        payload = _load_fixture("success_single_item.json")
        body = _response_body(payload)
        items = cast(dict[str, object], body["items"])
        single_item = cast(dict[str, object], items["item"])
        batch = RecordBatch(items=[single_item], dataset=ref, total_count=1, raw=payload)

        assert len(batch) == 1
        assert batch.items[0]["stationName"] == "종로구"

    def test_empty_fixture_batch_is_falsey(self) -> None:
        first_entry, _ = _load_catalogue_entries()
        ref = _make_ref(first_entry)
        payload = _load_fixture("success_empty.json")
        body = _response_body(payload)
        assert _items_node(body) is None

        batch = RecordBatch(items=[], dataset=ref, total_count=0)
        assert len(batch) == 0
        assert bool(batch) is False

    def test_string_numeric_fixture_shape_works_for_record_batch(self) -> None:
        first_entry, _ = _load_catalogue_entries()
        ref = _make_ref(first_entry)
        payload = _load_fixture("success_string_numerics.json")
        body = _response_body(payload)
        items = _items_list_from_body(body)

        batch = RecordBatch(
            items=items,
            dataset=ref,
            total_count=int(cast(str, body["totalCount"])),
            raw=payload,
        )
        assert len(batch) == 1
        assert batch.total_count == 1

    def test_multi_page_fixtures_can_be_combined(self) -> None:
        first_entry, _ = _load_catalogue_entries()
        ref = _make_ref(first_entry)
        page1_payload = _load_fixture("success_multi_page_1.json")
        page2_payload = _load_fixture("success_multi_page_2.json")
        page1_items = _items_list_from_body(_response_body(page1_payload))
        page2_items = _items_list_from_body(_response_body(page2_payload))
        all_items = [*page1_items, *page2_items]

        batch = RecordBatch(
            items=all_items,
            dataset=ref,
            total_count=3,
            raw=[page1_payload, page2_payload],
        )

        assert len(batch) == 3
        assert isinstance(batch.raw, list)


class TestQueryFromRealisticFilters:
    def test_query_with_korean_filters_preserves_exact_values(self) -> None:
        query = Query(
            filters={"stationName": "종로구", "dataTime": "2024-01-15 14:00"},
            page=1,
            page_size=10,
            extra={"returnType": "json"},
        )

        assert query.filters["stationName"] == "종로구"
        assert query.filters["dataTime"] == "2024-01-15 14:00"
        assert query.page == 1
        assert query.page_size == 10
        assert query.extra["returnType"] == "json"

    def test_query_defaults(self) -> None:
        query = Query()

        assert query.filters == {}
        assert query.page is None


class TestCapabilityImmutability:
    def test_query_support_is_frozen(self) -> None:
        query_support = QuerySupport(pagination=PaginationMode.OFFSET, max_page_size=1000)
        attr = "pagination"

        try:
            setattr(query_support, attr, PaginationMode.CURSOR)
            raise AssertionError("QuerySupport should be frozen")
        except AttributeError:
            pass
