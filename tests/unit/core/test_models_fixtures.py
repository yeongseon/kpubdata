"""테스트 모듈.

이 파일은 ``tests/unit/core/test_models_fixtures.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

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
    """
    내부 헬퍼로서 load catalogue entries 처리를 담당한다.

    반환값:
        tuple[dict[str, object], dict[str, object]]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    catalogue = cast(
        list[dict[str, object]],
        json.loads(CATALOGUE_PATH.read_text(encoding="utf-8")),
    )
    return catalogue[0], catalogue[1]


def _make_ref(entry: dict[str, object]) -> DatasetRef:
    """
    내부 헬퍼로서 make ref 처리를 담당한다.

    매개변수:
        entry (dict[str, object]): 호출자가 제공하는 입력 값이다.

    반환값:
        DatasetRef: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
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
    """
    내부 헬퍼로서 load fixture 처리를 담당한다.

    매개변수:
        name (str): 호출자가 제공하는 입력 값이다.

    반환값:
        dict[str, object]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    return cast(
        dict[str, object],
        json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8")),
    )


def _response_body(payload: dict[str, object]) -> dict[str, object]:
    """
    내부 헬퍼로서 response body 처리를 담당한다.

    매개변수:
        payload (dict[str, object]): 호출자가 제공하는 입력 값이다.

    반환값:
        dict[str, object]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    response = cast(dict[str, object], payload["response"])
    return cast(dict[str, object], response["body"])


def _items_node(body: dict[str, object]) -> dict[str, object] | None:
    """
    내부 헬퍼로서 items node 처리를 담당한다.

    매개변수:
        body (dict[str, object]): 호출자가 제공하는 입력 값이다.

    반환값:
        dict[str, object] | None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    return cast(dict[str, object] | None, body["items"])


def _items_list_from_body(body: dict[str, object]) -> list[dict[str, object]]:
    """
    내부 헬퍼로서 items list from body 처리를 담당한다.

    매개변수:
        body (dict[str, object]): 호출자가 제공하는 입력 값이다.

    반환값:
        list[dict[str, object]]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    items = cast(dict[str, object], body["items"])
    return cast(list[dict[str, object]], items["item"])


class TestDatasetRefFromCatalogue:
    """
    TestDatasetRefFromCatalogue 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/core/test_models_fixtures.py`` 모듈 안에서 TestDatasetRefFromCatalogue의 상태와 동작을 함께 관리한다.
    주요 메서드: test_first_entry_core_fields, test_second_entry_core_fields, test_operations_are_list_and_raw, test_query_support_offset_with_max_page_size, test_raw_metadata_is_mapping_proxy_with_required_keys.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    # test first entry core fields 테스트가 검증하는 시나리오를 설명한다.
    def test_first_entry_core_fields(self) -> None:
        """
        test first entry core fields 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        first_entry, _ = _load_catalogue_entries()
        ref = _make_ref(first_entry)

        assert ref.id == f"datago.{first_entry['dataset_key']}"
        assert ref.provider == "datago"
        assert ref.dataset_key == first_entry["dataset_key"]
        assert ref.name == first_entry["name"]
        assert ref.representation == Representation.API_JSON

    # test second entry core fields 테스트가 검증하는 시나리오를 설명한다.
    def test_second_entry_core_fields(self) -> None:
        """
        test second entry core fields 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        _, second_entry = _load_catalogue_entries()
        ref = _make_ref(second_entry)

        assert ref.id == f"datago.{second_entry['dataset_key']}"
        assert ref.provider == "datago"
        assert ref.dataset_key == second_entry["dataset_key"]
        assert ref.name == second_entry["name"]
        assert ref.representation == Representation.API_JSON

    # test operations are list and raw 테스트가 검증하는 시나리오를 설명한다.
    def test_operations_are_list_and_raw(self) -> None:
        """
        test operations are list and raw 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        first_entry, _ = _load_catalogue_entries()
        ref = _make_ref(first_entry)

        assert ref.operations == frozenset({Operation.LIST, Operation.RAW})

    # test query support offset with max page size 테스트가 검증하는 시나리오를 설명한다.
    def test_query_support_offset_with_max_page_size(self) -> None:
        """
        test query support offset with max page size 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        _, second_entry = _load_catalogue_entries()
        ref = _make_ref(second_entry)

        assert ref.query_support is not None
        assert ref.query_support.pagination == PaginationMode.OFFSET
        assert ref.query_support.max_page_size == 1000

    # test raw metadata is mapping proxy with required keys 테스트가 검증하는 시나리오를 설명한다.
    def test_raw_metadata_is_mapping_proxy_with_required_keys(self) -> None:
        """
        test raw metadata is mapping proxy with required keys 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        first_entry, _ = _load_catalogue_entries()
        ref = _make_ref(first_entry)

        assert isinstance(ref.raw_metadata, MappingProxyType)
        assert "base_url" in ref.raw_metadata
        assert "default_operation" in ref.raw_metadata
        assert "service_key_param" in ref.raw_metadata

    # test supports list and not get 테스트가 검증하는 시나리오를 설명한다.
    def test_supports_list_and_not_get(self) -> None:
        """
        test supports list and not get 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        first_entry, _ = _load_catalogue_entries()
        ref = _make_ref(first_entry)

        assert ref.supports(Operation.LIST) is True
        assert ref.supports(Operation.GET) is False

    # test is frozen 테스트가 검증하는 시나리오를 설명한다.
    def test_is_frozen(self) -> None:
        """
        test is frozen 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        first_entry, _ = _load_catalogue_entries()
        ref = _make_ref(first_entry)
        attr = "id"

        try:
            setattr(ref, attr, "datago.changed")
            raise AssertionError("DatasetRef should be frozen")
        except AttributeError:
            pass


class TestRecordBatchFromFixtures:
    """
    TestRecordBatchFromFixtures 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/core/test_models_fixtures.py`` 모듈 안에서 TestRecordBatchFromFixtures의 상태와 동작을 함께 관리한다.
    주요 메서드: test_single_page_batch_shape, test_single_item_fixture_normalized_to_list, test_empty_fixture_batch_is_falsey, test_string_numeric_fixture_shape_works_for_record_batch, test_multi_page_fixtures_can_be_combined.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    # test single page batch shape 테스트가 검증하는 시나리오를 설명한다.
    def test_single_page_batch_shape(self) -> None:
        """
        test single page batch shape 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
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

    # test single item fixture normalized to list 테스트가 검증하는 시나리오를 설명한다.
    def test_single_item_fixture_normalized_to_list(self) -> None:
        """
        test single item fixture normalized to list 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        first_entry, _ = _load_catalogue_entries()
        ref = _make_ref(first_entry)
        payload = _load_fixture("success_single_item.json")
        body = _response_body(payload)
        items = cast(dict[str, object], body["items"])
        single_item = cast(dict[str, object], items["item"])
        batch = RecordBatch(items=[single_item], dataset=ref, total_count=1, raw=payload)

        assert len(batch) == 1
        assert batch.items[0]["stationName"] == "종로구"

    # test empty fixture batch is falsey 테스트가 검증하는 시나리오를 설명한다.
    def test_empty_fixture_batch_is_falsey(self) -> None:
        """
        test empty fixture batch is falsey 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        first_entry, _ = _load_catalogue_entries()
        ref = _make_ref(first_entry)
        payload = _load_fixture("success_empty.json")
        body = _response_body(payload)
        assert _items_node(body) is None

        batch = RecordBatch(items=[], dataset=ref, total_count=0)
        assert len(batch) == 0
        assert bool(batch) is False

    # test string numeric fixture shape works for record batch 테스트가 검증하는 시나리오를 설명한다.
    def test_string_numeric_fixture_shape_works_for_record_batch(self) -> None:
        """
        test string numeric fixture shape works for record batch 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
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

    # test multi page fixtures can be combined 테스트가 검증하는 시나리오를 설명한다.
    def test_multi_page_fixtures_can_be_combined(self) -> None:
        """
        test multi page fixtures can be combined 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
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
    """
    TestQueryFromRealisticFilters 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/core/test_models_fixtures.py`` 모듈 안에서 TestQueryFromRealisticFilters의 상태와 동작을 함께 관리한다.
    주요 메서드: test_query_with_korean_filters_preserves_exact_values, test_query_defaults.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    # test query with korean filters preserves exact values 테스트가 검증하는 시나리오를 설명한다.
    def test_query_with_korean_filters_preserves_exact_values(self) -> None:
        """
        test query with korean filters preserves exact values 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
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

    # test query defaults 테스트가 검증하는 시나리오를 설명한다.
    def test_query_defaults(self) -> None:
        """
        test query defaults 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        query = Query()

        assert query.filters == {}
        assert query.page is None


class TestCapabilityImmutability:
    """
    TestCapabilityImmutability 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/core/test_models_fixtures.py`` 모듈 안에서 TestCapabilityImmutability의 상태와 동작을 함께 관리한다.
    주요 메서드: test_query_support_is_frozen.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    # test query support is frozen 테스트가 검증하는 시나리오를 설명한다.
    def test_query_support_is_frozen(self) -> None:
        """
        test query support is frozen 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        query_support = QuerySupport(pagination=PaginationMode.OFFSET, max_page_size=1000)
        attr = "pagination"

        try:
            setattr(query_support, attr, PaginationMode.CURSOR)
            raise AssertionError("QuerySupport should be frozen")
        except AttributeError:
            pass
