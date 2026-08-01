"""Tests for Dataset binding and capability checks."""

from __future__ import annotations

import pytest

from kpubdata.core.capability import Operation
from kpubdata.core.dataset import Dataset
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.core.representation import Representation
from kpubdata.exceptions import InvalidRequestError, UnsupportedCapabilityError


class MockAdapter:
    """Adapter that records calls for assertion."""

    def __init__(self) -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self.last_query: Query | None = None
        self.last_raw_op: str | None = None
        self.batches: list[RecordBatch] = []

    @property
    def name(self) -> str:
        """
        name 동작을 수행한다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return "mock"

    def list_datasets(self) -> list[DatasetRef]:
        """
        list datasets 동작을 수행한다.

        반환값:
            list[DatasetRef]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return []

    def search_datasets(self, text: str) -> list[DatasetRef]:
        """
        search datasets 동작을 수행한다.

        매개변수:
            text (str): 호출자가 제공하는 입력 값이다.

        반환값:
            list[DatasetRef]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        _ = text
        return []

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        """
        get dataset 동작을 수행한다.

        매개변수:
            dataset_key (str): 호출자가 제공하는 입력 값이다.

        반환값:
            DatasetRef: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        _ = dataset_key
        return _ref()

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        """
        query records 동작을 수행한다.

        매개변수:
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.
            query (Query): 호출자가 제공하는 입력 값이다.

        반환값:
            RecordBatch: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또한 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self.last_query = query
        if self.batches:
            return self.batches.pop(0)
        return RecordBatch(items=[{"k": "v"}], dataset=dataset)

    def get_schema(self, dataset: DatasetRef) -> SchemaDescriptor | None:
        """
        get schema 동작을 수행한다.

        매개변수:
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.

        반환값:
            SchemaDescriptor | None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        _ = dataset
        return None

    def call_raw(self, dataset: DatasetRef, operation: str, params: dict[str, object]) -> object:
        """
        call raw 동작을 수행한다.

        매개변수:
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.
            operation (str): 호출자가 제공하는 입력 값이다.
            params (dict[str, object]): 호출자가 제공하는 입력 값이다.

        반환값:
            object: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        _ = dataset, params
        self.last_raw_op = operation
        return {"raw": True}


def _ref(ops: frozenset[Operation] | None = None) -> DatasetRef:
    """
    내부 헬퍼로서 ref 처리를 담당한다.

    매개변수:
        ops (frozenset[Operation] | None): 호출자가 제공하는 입력 값이다.

    반환값:
        DatasetRef: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    return DatasetRef(
        id="mock.test",
        provider="mock",
        dataset_key="test",
        name="Test",
        representation=Representation.API_JSON,
        operations=ops or frozenset({Operation.LIST, Operation.RAW}),
    )


class TestDataset:
    """
    TestDataset 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/core/test_dataset.py`` 모듈 안에서 TestDataset의 상태와 동작을 함께 관리한다.
    주요 메서드: test_list, test_list_unsupported, test_list_all_unsupported, test_call_raw, test_repr.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    # test list 테스트가 검증하는 시나리오를 설명한다.
    def test_list(self) -> None:
        """
        test list 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        ds = Dataset(ref=_ref(), adapter=adapter)
        result = ds.list(code="11680")
        assert len(result) == 1
        assert adapter.last_query is not None
        assert adapter.last_query.filters["code"] == "11680"

    # test list unsupported 테스트가 검증하는 시나리오를 설명한다.
    def test_list_unsupported(self) -> None:
        """
        test list unsupported 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        ds = Dataset(ref=_ref(frozenset({Operation.RAW})), adapter=adapter)
        with pytest.raises(UnsupportedCapabilityError, match="list"):
            _ = ds.list()

    # test list all unsupported 테스트가 검증하는 시나리오를 설명한다.
    def test_list_all_unsupported(self) -> None:
        """
        test list all unsupported 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        ds = Dataset(ref=_ref(frozenset({Operation.RAW})), adapter=adapter)
        with pytest.raises(UnsupportedCapabilityError, match="list"):
            _ = list(ds.list_all())

    # test call raw 테스트가 검증하는 시나리오를 설명한다.
    def test_call_raw(self) -> None:
        """
        test call raw 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        ds = Dataset(ref=_ref(), adapter=adapter)
        result = ds.call_raw("list", param="value")
        assert result == {"raw": True}
        assert adapter.last_raw_op == "list"

    # test repr 테스트가 검증하는 시나리오를 설명한다.
    def test_repr(self) -> None:
        """
        test repr 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        ds = Dataset(ref=_ref(), adapter=adapter)
        assert "mock.test" in repr(ds)

    # test list separates canonical query fields 테스트가 검증하는 시나리오를 설명한다.
    def test_list_separates_canonical_query_fields(self) -> None:
        """
        test list separates canonical query fields 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        ds = Dataset(ref=_ref(), adapter=adapter)

        _ = ds.list(
            start_date="202401",
            end_date="202412",
            page=2,
            page_size=50,
            region="서울",
        )

        assert adapter.last_query is not None
        assert adapter.last_query.start_date == "202401"
        assert adapter.last_query.end_date == "202412"
        assert adapter.last_query.page == 2
        assert adapter.last_query.page_size == 50
        assert adapter.last_query.filters == {"region": "서울"}

    # test list canonical fields not in filters 테스트가 검증하는 시나리오를 설명한다.
    def test_list_canonical_fields_not_in_filters(self) -> None:
        """
        test list canonical fields not in filters 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        ds = Dataset(ref=_ref(), adapter=adapter)

        _ = ds.list(cursor="abc", fields=["name", "age"], sort=["name"])

        assert adapter.last_query is not None
        assert adapter.last_query.cursor == "abc"
        assert adapter.last_query.fields == ["name", "age"]
        assert adapter.last_query.sort == ["name"]
        assert adapter.last_query.filters == {}

    # test list only filters no canonical 테스트가 검증하는 시나리오를 설명한다.
    def test_list_only_filters_no_canonical(self) -> None:
        """
        test list only filters no canonical 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        ds = Dataset(ref=_ref(), adapter=adapter)

        _ = ds.list(lawd_code="11680", deal_ym="202503")

        assert adapter.last_query is not None
        assert adapter.last_query.page is None
        assert adapter.last_query.start_date is None
        assert adapter.last_query.filters == {"lawd_code": "11680", "deal_ym": "202503"}

    # test list all yields multiple batches 테스트가 검증하는 시나리오를 설명한다.
    def test_list_all_yields_multiple_batches(self) -> None:
        """
        test list all yields multiple batches 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        dataset_ref = _ref()
        adapter.batches = [
            RecordBatch(items=[{"page": 1}], dataset=dataset_ref, next_page=2),
            RecordBatch(items=[{"page": 2}], dataset=dataset_ref, next_page=3),
            RecordBatch(items=[{"page": 3}], dataset=dataset_ref, next_page=None),
        ]
        ds = Dataset(ref=dataset_ref, adapter=adapter)

        batches = list(ds.list_all(region="서울"))

        assert [batch.items[0]["page"] for batch in batches] == [1, 2, 3]

    # test list all stops when next page is none 테스트가 검증하는 시나리오를 설명한다.
    def test_list_all_stops_when_next_page_is_none(self) -> None:
        """
        test list all stops when next page is none 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        dataset_ref = _ref()
        adapter.batches = [
            RecordBatch(items=[{"page": 1}], dataset=dataset_ref, next_page=2),
            RecordBatch(items=[{"page": 2}], dataset=dataset_ref, next_page=None),
        ]
        ds = Dataset(ref=dataset_ref, adapter=adapter)

        batches = list(ds.list_all(code="11680"))

        assert len(batches) == 2
        assert adapter.last_query is not None
        assert adapter.last_query.page == 2
        assert adapter.last_query.filters == {"code": "11680"}

    # test list all single page 테스트가 검증하는 시나리오를 설명한다.
    def test_list_all_single_page(self) -> None:
        """
        test list all single page 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        dataset_ref = _ref()
        adapter.batches = [RecordBatch(items=[{"page": 1}], dataset=dataset_ref, next_page=None)]
        ds = Dataset(ref=dataset_ref, adapter=adapter)

        batches = list(ds.list_all())

        assert len(batches) == 1
        assert batches[0].items == [{"page": 1}]

    # test list all cursor pagination 테스트가 검증하는 시나리오를 설명한다.
    def test_list_all_cursor_pagination(self) -> None:
        """
        test list all cursor pagination 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        dataset_ref = _ref()
        adapter.batches = [
            RecordBatch(items=[{"cursor": "a"}], dataset=dataset_ref, next_cursor="abc"),
            RecordBatch(items=[{"cursor": "b"}], dataset=dataset_ref, next_cursor="def"),
            RecordBatch(items=[{"cursor": "c"}], dataset=dataset_ref, next_cursor=None),
        ]
        ds = Dataset(ref=dataset_ref, adapter=adapter)

        batches = list(ds.list_all(region="서울"))

        assert [batch.items[0]["cursor"] for batch in batches] == ["a", "b", "c"]
        assert adapter.last_query is not None
        assert adapter.last_query.cursor == "def"
        assert adapter.last_query.page is None
        assert adapter.last_query.filters == {"region": "서울"}

    # test list all cursor single page 테스트가 검증하는 시나리오를 설명한다.
    def test_list_all_cursor_single_page(self) -> None:
        """
        test list all cursor single page 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        dataset_ref = _ref()
        adapter.batches = [
            RecordBatch(items=[{"cursor": "a"}], dataset=dataset_ref, next_cursor=None)
        ]
        ds = Dataset(ref=dataset_ref, adapter=adapter)

        batches = list(ds.list_all())

        assert len(batches) == 1
        assert batches[0].items == [{"cursor": "a"}]

    # test list all respects max pages parameter 테스트가 검증하는 시나리오를 설명한다.
    def test_list_all_respects_max_pages_parameter(self) -> None:
        """
        test list all respects max pages parameter 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        dataset_ref = _ref()
        # Create 5 pages of data
        adapter.batches = [
            RecordBatch(items=[{"page": 1}], dataset=dataset_ref, next_page=2),
            RecordBatch(items=[{"page": 2}], dataset=dataset_ref, next_page=3),
            RecordBatch(items=[{"page": 3}], dataset=dataset_ref, next_page=4),
            RecordBatch(items=[{"page": 4}], dataset=dataset_ref, next_page=5),
            RecordBatch(items=[{"page": 5}], dataset=dataset_ref, next_page=None),
        ]
        ds = Dataset(ref=dataset_ref, adapter=adapter)

        # Should complete normally with 5 pages when max_pages=10
        batches = list(ds.list_all(max_pages=10))
        assert len(batches) == 5

    # test list all raises when max pages exceeded 테스트가 검증하는 시나리오를 설명한다.
    def test_list_all_raises_when_max_pages_exceeded(self) -> None:
        """
        test list all raises when max pages exceeded 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        dataset_ref = _ref()
        # Create many pages to exceed the limit
        adapter.batches = [
            RecordBatch(items=[{"page": i}], dataset=dataset_ref, next_page=i + 1)
            for i in range(1, 15)
        ]
        ds = Dataset(ref=dataset_ref, adapter=adapter)

        # Should raise when exceeding max_pages=10
        with pytest.raises(InvalidRequestError, match="Pagination limit exceeded"):
            _ = list(ds.list_all(max_pages=10))

    # test list all detects page cycle 테스트가 검증하는 시나리오를 설명한다.
    def test_list_all_detects_page_cycle(self) -> None:
        """
        test list all detects page cycle 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        dataset_ref = _ref()
        # Create a cycle: page 1 -> 2 -> 3 -> 2 -> 3 ...
        adapter.batches = [
            RecordBatch(items=[{"page": 1}], dataset=dataset_ref, next_page=2),
            RecordBatch(items=[{"page": 2}], dataset=dataset_ref, next_page=3),
            RecordBatch(items=[{"page": 3}], dataset=dataset_ref, next_page=2),  # cycle back to 2
        ]
        ds = Dataset(ref=dataset_ref, adapter=adapter)

        # Should detect the cycle when trying to fetch page 2 again
        with pytest.raises(InvalidRequestError, match="pagination cycle"):
            _ = list(ds.list_all())

    # test list all detects cursor cycle 테스트가 검증하는 시나리오를 설명한다.
    def test_list_all_detects_cursor_cycle(self) -> None:
        """
        test list all detects cursor cycle 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        dataset_ref = _ref()
        # Create a cycle with cursors
        adapter.batches = [
            RecordBatch(items=[{"cursor": "a"}], dataset=dataset_ref, next_cursor="abc"),
            RecordBatch(items=[{"cursor": "b"}], dataset=dataset_ref, next_cursor="def"),
            RecordBatch(items=[{"cursor": "c"}], dataset=dataset_ref, next_cursor="abc"),  # cycle
        ]
        ds = Dataset(ref=dataset_ref, adapter=adapter)

        # Should detect the cycle when trying to use cursor "abc" again
        with pytest.raises(InvalidRequestError, match="pagination cycle"):
            _ = list(ds.list_all())

    # test list all raises on consecutive empty batches 테스트가 검증하는 시나리오를 설명한다.
    def test_list_all_raises_on_consecutive_empty_batches(self) -> None:
        """
        test list all raises on consecutive empty batches 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        dataset_ref = _ref()
        # Provider keeps returning empty batches but with next_page
        adapter.batches = [
            RecordBatch(items=[], dataset=dataset_ref, next_page=2),
            RecordBatch(items=[], dataset=dataset_ref, next_page=3),
            RecordBatch(items=[], dataset=dataset_ref, next_page=4),
        ]
        ds = Dataset(ref=dataset_ref, adapter=adapter)

        # Should raise after 3 consecutive empty batches
        with pytest.raises(InvalidRequestError, match="consecutive empty batches"):
            _ = list(ds.list_all())

    # test list all allows single empty batch 테스트가 검증하는 시나리오를 설명한다.
    def test_list_all_allows_single_empty_batch(self) -> None:
        """
        test list all allows single empty batch 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        dataset_ref = _ref()
        # A single empty batch is allowed (might be legitimate)
        adapter.batches = [RecordBatch(items=[], dataset=dataset_ref, next_page=None)]
        ds = Dataset(ref=dataset_ref, adapter=adapter)

        # Should complete normally
        batches = list(ds.list_all())
        assert len(batches) == 1
        assert batches[0].items == []

    # test list all handles mixed empty and non empty batches 테스트가 검증하는 시나리오를 설명한다.
    def test_list_all_handles_mixed_empty_and_non_empty_batches(self) -> None:
        """
        test list all handles mixed empty and non empty batches 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        dataset_ref = _ref()
        # Mix of empty and non-empty batches should be fine
        adapter.batches = [
            RecordBatch(items=[{"page": 1}], dataset=dataset_ref, next_page=2),
            RecordBatch(items=[], dataset=dataset_ref, next_page=3),  # empty but has next
            RecordBatch(items=[{"page": 3}], dataset=dataset_ref, next_page=None),
        ]
        ds = Dataset(ref=dataset_ref, adapter=adapter)

        # Should complete normally
        batches = list(ds.list_all())
        assert len(batches) == 3
        assert [batch.items[0].get("page") if batch.items else None for batch in batches] == [
            1,
            None,
            3,
        ]

    # test list all uses default max pages when not specified 테스트가 검증하는 시나리오를 설명한다.
    def test_list_all_uses_default_max_pages_when_not_specified(self) -> None:
        """
        test list all uses default max pages when not specified 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        dataset_ref = _ref()
        # Create a reasonable number of pages (should be under default limit)
        adapter.batches = [
            RecordBatch(items=[{"page": i}], dataset=dataset_ref, next_page=i + 1)
            for i in range(1, 10)
        ]
        adapter.batches.append(
            RecordBatch(items=[{"page": 10}], dataset=dataset_ref, next_page=None)
        )
        ds = Dataset(ref=dataset_ref, adapter=adapter)

        # Should work with default max_pages
        batches = list(ds.list_all())
        assert len(batches) == 10

    # test list all detects immediate cycle from first page 테스트가 검증하는 시나리오를 설명한다.
    def test_list_all_detects_immediate_cycle_from_first_page(self) -> None:
        """
        test list all detects immediate cycle from first page 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        dataset_ref = _ref()
        # First batch immediately returns to page 1 (cycle to itself)
        adapter.batches = [RecordBatch(items=[{"page": 1}], dataset=dataset_ref, next_page=1)]
        ds = Dataset(ref=dataset_ref, adapter=adapter)

        # Should detect cycle when trying to fetch page 1 again
        with pytest.raises(InvalidRequestError, match="pagination cycle"):
            _ = list(ds.list_all())

    # test list all passes through filters with max pages 테스트가 검증하는 시나리오를 설명한다.
    def test_list_all_passes_through_filters_with_max_pages(self) -> None:
        """
        test list all passes through filters with max pages 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        dataset_ref = _ref()
        adapter.batches = [RecordBatch(items=[{"page": 1}], dataset=dataset_ref, next_page=None)]
        ds = Dataset(ref=dataset_ref, adapter=adapter)

        _ = list(ds.list_all(max_pages=5, region="서울", code="11680"))

        assert adapter.last_query is not None
        assert adapter.last_query.filters == {"region": "서울", "code": "11680"}

    # test list all with max pages None uses default 테스트가 검증하는 시나리오를 설명한다.
    def test_list_all_with_max_pages_none_uses_default(self) -> None:
        """
        test list all with max pages None uses default 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또한 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        dataset_ref = _ref()
        adapter.batches = [RecordBatch(items=[{"page": 1}], dataset=dataset_ref, next_page=None)]
        ds = Dataset(ref=dataset_ref, adapter=adapter)

        # max_pages=None should use default (1000)
        batches = list(ds.list_all(max_pages=None))
        assert len(batches) == 1

    # test list all with max pages one 테스트가 검증하는 시나리오를 설명한다.
    def test_list_all_with_max_pages_one(self) -> None:
        """
        test list all with max pages one 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또은 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        dataset_ref = _ref()
        adapter.batches = [RecordBatch(items=[{"page": 1}], dataset=dataset_ref, next_page=None)]
        ds = Dataset(ref=dataset_ref, adapter=adapter)

        # max_pages=1 should work
        batches = list(ds.list_all(max_pages=1))
        assert len(batches) == 1

    # test list all rejects max pages zero 테스트가 검증하는 시나리오를 설명한다.
    def test_list_all_rejects_max_pages_zero(self) -> None:
        """
        test list all rejects max pages zero 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또은 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        dataset_ref = _ref()
        ds = Dataset(ref=dataset_ref, adapter=adapter)

        # max_pages=0 should raise InvalidRequestError
        with pytest.raises(InvalidRequestError, match="must be None or a positive integer"):
            _ = list(ds.list_all(max_pages=0))

    # test list all rejects max pages negative 테스트가 검증하는 시나리오를 설명한다.
    def test_list_all_rejects_max_pages_negative(self) -> None:
        """
        test list all rejects max pages negative 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또은 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        dataset_ref = _ref()
        ds = Dataset(ref=dataset_ref, adapter=adapter)

        # max_pages=-1 should raise InvalidRequestError
        with pytest.raises(InvalidRequestError, match="must be None or a positive integer"):
            _ = list(ds.list_all(max_pages=-1))

    # test list all rejects max pages true 테스트가 검증하는 시나리오를 설명한다.
    def test_list_all_rejects_max_pages_true(self) -> None:
        """
        test list all rejects max pages true 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또은 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        dataset_ref = _ref()
        ds = Dataset(ref=dataset_ref, adapter=adapter)

        # max_pages=True should raise InvalidRequestError
        with pytest.raises(
            InvalidRequestError, match="must be None or a positive integer.*got bool"
        ):
            _ = list(ds.list_all(max_pages=True))

    # test list all rejects max pages string 테스트가 검증하는 시나리오를 설명한다.
    def test_list_all_rejects_max_pages_string(self) -> None:
        """
        test list all rejects max pages string 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또은 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = MockAdapter()
        dataset_ref = _ref()
        ds = Dataset(ref=dataset_ref, adapter=adapter)

        # max_pages="10" should raise InvalidRequestError
        with pytest.raises(
            InvalidRequestError, match="must be None or a positive integer.*got str"
        ):
            _ = list(ds.list_all(max_pages="10"))
