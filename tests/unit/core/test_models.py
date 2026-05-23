"""Tests for canonical core models."""

from __future__ import annotations

from types import MappingProxyType

from kpubdata.core.capability import Operation, PaginationMode, QuerySupport
from kpubdata.core.models import (
    DatasetRef,
    FieldConstraints,
    FieldDescriptor,
    Query,
    RecordBatch,
    SchemaDescriptor,
)
from kpubdata.core.representation import Representation


class TestOperation:
    """
    TestOperation 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/core/test_models.py`` 모듈 안에서 TestOperation의 상태와 동작을 함께 관리한다.
    주요 메서드: test_values, test_str_mixin.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    # test values 테스트가 검증하는 시나리오를 설명한다.
    def test_values(self) -> None:
        """
        test values 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        assert Operation.LIST.value == "list"
        assert Operation.GET.value == "get"
        assert Operation.RAW.value == "raw"

    # test str mixin 테스트가 검증하는 시나리오를 설명한다.
    def test_str_mixin(self) -> None:
        """
        test str mixin 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        assert str(Operation.LIST) == "Operation.LIST" or "list" in str(Operation.LIST)


class TestRepresentation:
    """
    TestRepresentation 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/core/test_models.py`` 모듈 안에서 TestRepresentation의 상태와 동작을 함께 관리한다.
    주요 메서드: test_values.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    # test values 테스트가 검증하는 시나리오를 설명한다.
    def test_values(self) -> None:
        """
        test values 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        assert Representation.API_JSON.value == "api_json"
        assert Representation.API_XML.value == "api_xml"


class TestQuerySupport:
    """
    TestQuerySupport 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/core/test_models.py`` 모듈 안에서 TestQuerySupport의 상태와 동작을 함께 관리한다.
    주요 메서드: test_defaults, test_frozen.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    # test defaults 테스트가 검증하는 시나리오를 설명한다.
    def test_defaults(self) -> None:
        """
        test defaults 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        qs = QuerySupport()
        assert qs.pagination == PaginationMode.NONE
        assert qs.filterable_fields == frozenset()
        assert qs.time_range is False
        assert qs.max_page_size is None

    # test frozen 테스트가 검증하는 시나리오를 설명한다.
    def test_frozen(self) -> None:
        """
        test frozen 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        qs = QuerySupport(pagination=PaginationMode.OFFSET)
        try:
            qs.pagination = PaginationMode.CURSOR  # type: ignore[misc]
            raise AssertionError("Should be frozen")
        except AttributeError:
            pass


class TestDatasetRef:
    """
    TestDatasetRef 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/core/test_models.py`` 모듈 안에서 TestDatasetRef의 상태와 동작을 함께 관리한다.
    주요 메서드: _make_ref, test_supports, test_frozen, test_raw_metadata_immutable, test_repr.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    def _make_ref(self, **kwargs: object) -> DatasetRef:
        """
        내부 헬퍼로서 make ref 처리를 담당한다.

        매개변수:
            **kwargs (object): 호출자가 제공하는 입력 값이다.

        반환값:
            DatasetRef: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        defaults: dict[str, object] = {
            "id": "test.dataset",
            "provider": "test",
            "dataset_key": "dataset",
            "name": "Test Dataset",
            "representation": Representation.API_JSON,
            "operations": frozenset({Operation.LIST, Operation.RAW}),
        }
        defaults.update(kwargs)
        return DatasetRef(**defaults)  # type: ignore[arg-type]

    # test supports 테스트가 검증하는 시나리오를 설명한다.
    def test_supports(self) -> None:
        """
        test supports 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        ref = self._make_ref()
        assert ref.supports(Operation.LIST) is True
        assert ref.supports(Operation.GET) is False

    # test frozen 테스트가 검증하는 시나리오를 설명한다.
    def test_frozen(self) -> None:
        """
        test frozen 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        ref = self._make_ref()
        try:
            ref.id = "changed"  # type: ignore[misc]
            raise AssertionError("Should be frozen")
        except AttributeError:
            pass

    # test raw metadata immutable 테스트가 검증하는 시나리오를 설명한다.
    def test_raw_metadata_immutable(self) -> None:
        """
        test raw metadata immutable 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        ref = self._make_ref()
        assert isinstance(ref.raw_metadata, MappingProxyType)

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
        ref = self._make_ref()
        r = repr(ref)
        assert "test.dataset" in r
        assert "test" in r

    # test metadata defaults 테스트가 검증하는 시나리오를 설명한다.
    def test_metadata_defaults(self) -> None:
        """
        test metadata defaults 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        ref = self._make_ref()
        assert ref.description is None
        assert ref.tags == ()
        assert ref.source_url is None

    # test metadata populated 테스트가 검증하는 시나리오를 설명한다.
    def test_metadata_populated(self) -> None:
        """
        test metadata populated 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        ref = self._make_ref(
            description="Weather forecast data",
            tags=("weather", "forecast"),
            source_url="https://data.go.kr/example",
        )
        assert ref.description == "Weather forecast data"
        assert ref.tags == ("weather", "forecast")
        assert ref.source_url == "https://data.go.kr/example"

    # test metadata frozen 테스트가 검증하는 시나리오를 설명한다.
    def test_metadata_frozen(self) -> None:
        """
        test metadata frozen 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        ref = self._make_ref(description="test", tags=("a",), source_url="http://x")
        try:
            ref.description = "changed"  # type: ignore[misc]
            raise AssertionError("Should be frozen")
        except AttributeError:
            pass
        try:
            ref.tags = ("b",)  # type: ignore[misc]
            raise AssertionError("Should be frozen")
        except AttributeError:
            pass


class TestQuery:
    """
    TestQuery 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/core/test_models.py`` 모듈 안에서 TestQuery의 상태와 동작을 함께 관리한다.
    주요 메서드: test_defaults, test_with_filters.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    # test defaults 테스트가 검증하는 시나리오를 설명한다.
    def test_defaults(self) -> None:
        """
        test defaults 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        q = Query()
        assert q.filters == {}
        assert q.page is None
        assert q.extra == {}

    # test with filters 테스트가 검증하는 시나리오를 설명한다.
    def test_with_filters(self) -> None:
        """
        test with filters 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        q = Query(filters={"key": "value"}, page=1, page_size=10)
        assert q.filters["key"] == "value"
        assert q.page == 1


class TestRecordBatch:
    """
    TestRecordBatch 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/core/test_models.py`` 모듈 안에서 TestRecordBatch의 상태와 동작을 함께 관리한다.
    주요 메서드: _make_ref, test_len, test_iter, test_bool_empty, test_bool_nonempty.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    def _make_ref(self) -> DatasetRef:
        """
        내부 헬퍼로서 make ref 처리를 담당한다.

        반환값:
            DatasetRef: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return DatasetRef(
            id="test.ds",
            provider="test",
            dataset_key="ds",
            name="DS",
            representation=Representation.API_JSON,
        )

    # test len 테스트가 검증하는 시나리오를 설명한다.
    def test_len(self) -> None:
        """
        test len 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        batch = RecordBatch(items=[{"a": 1}, {"a": 2}], dataset=self._make_ref())
        assert len(batch) == 2

    # test iter 테스트가 검증하는 시나리오를 설명한다.
    def test_iter(self) -> None:
        """
        test iter 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        items = [{"a": 1}, {"a": 2}]
        batch = RecordBatch(items=items, dataset=self._make_ref())
        assert list(batch) == items

    # test bool empty 테스트가 검증하는 시나리오를 설명한다.
    def test_bool_empty(self) -> None:
        """
        test bool empty 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        batch = RecordBatch(items=[], dataset=self._make_ref())
        assert not batch

    # test bool nonempty 테스트가 검증하는 시나리오를 설명한다.
    def test_bool_nonempty(self) -> None:
        """
        test bool nonempty 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        batch = RecordBatch(items=[{"a": 1}], dataset=self._make_ref())
        assert batch


class TestSchemaDescriptor:
    """
    TestSchemaDescriptor 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/core/test_models.py`` 모듈 안에서 TestSchemaDescriptor의 상태와 동작을 함께 관리한다.
    주요 메서드: test_fields.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    # test fields 테스트가 검증하는 시나리오를 설명한다.
    def test_fields(self) -> None:
        """
        test fields 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        ref = DatasetRef(
            id="t.d",
            provider="t",
            dataset_key="d",
            name="D",
            representation=Representation.API_JSON,
        )
        fd = FieldDescriptor(name="col1", title="Column 1", type="string")
        sd = SchemaDescriptor(dataset=ref, fields=[fd])
        assert len(sd.fields) == 1
        assert sd.fields[0].name == "col1"


class TestFieldConstraints:
    """
    TestFieldConstraints 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/core/test_models.py`` 모듈 안에서 TestFieldConstraints의 상태와 동작을 함께 관리한다.
    주요 메서드: test_all_defaults_none, test_populated, test_single_field, test_partial_population.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    # test all defaults none 테스트가 검증하는 시나리오를 설명한다.
    def test_all_defaults_none(self) -> None:
        """
        test all defaults none 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        fc = FieldConstraints()
        assert fc.max_length is None
        assert fc.min_value is None
        assert fc.max_value is None
        assert fc.pattern is None
        assert fc.allowed_values is None
        assert fc.format is None

    # test populated 테스트가 검증하는 시나리오를 설명한다.
    def test_populated(self) -> None:
        """
        test populated 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        fc = FieldConstraints(
            max_length=100,
            min_value=0,
            max_value=999.9,
            pattern=r"^\d{6}$",
            allowed_values=("A", "B", "C"),
            format="YYYYMM",
        )
        assert fc.max_length == 100
        assert fc.min_value == 0
        assert fc.max_value == 999.9
        assert fc.pattern == r"^\d{6}$"
        assert fc.allowed_values == ("A", "B", "C")
        assert fc.format == "YYYYMM"

    # test single field 테스트가 검증하는 시나리오를 설명한다.
    def test_single_field(self) -> None:
        """
        test single field 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        fc = FieldConstraints(max_length=10)
        assert fc.max_length == 10

    # test partial population 테스트가 검증하는 시나리오를 설명한다.
    def test_partial_population(self) -> None:
        """
        test partial population 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        fc = FieldConstraints(format="date", allowed_values=("yes", "no"))
        assert fc.max_length is None
        assert fc.format == "date"
        assert fc.allowed_values == ("yes", "no")


class TestFieldDescriptorConstraints:
    """
    TestFieldDescriptorConstraints 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/core/test_models.py`` 모듈 안에서 TestFieldDescriptorConstraints의 상태와 동작을 함께 관리한다.
    주요 메서드: test_default_constraints_none, test_with_constraints, test_positional_raw_backward_compat.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    # test default constraints none 테스트가 검증하는 시나리오를 설명한다.
    def test_default_constraints_none(self) -> None:
        """
        test default constraints none 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        fd = FieldDescriptor(name="col")
        assert fd.constraints is None

    # test with constraints 테스트가 검증하는 시나리오를 설명한다.
    def test_with_constraints(self) -> None:
        """
        test with constraints 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        fc = FieldConstraints(max_length=50, format="YYYYMM")
        fd = FieldDescriptor(name="date_col", type="string", constraints=fc)
        assert fd.constraints is not None
        assert fd.constraints.max_length == 50
        assert fd.constraints.format == "YYYYMM"

    # test positional raw backward compat 테스트가 검증하는 시나리오를 설명한다.
    def test_positional_raw_backward_compat(self) -> None:
        """
        test positional raw backward compat 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        proxy = MappingProxyType({"k": "v"})
        fd = FieldDescriptor("col", "Title", "string", "desc", True, proxy)
        assert fd.name == "col"
        assert fd.raw == proxy
        assert fd.constraints is None
