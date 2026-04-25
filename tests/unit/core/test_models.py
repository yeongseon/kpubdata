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
    def test_values(self) -> None:
        assert Operation.LIST.value == "list"
        assert Operation.GET.value == "get"
        assert Operation.RAW.value == "raw"

    def test_str_mixin(self) -> None:
        assert str(Operation.LIST) == "Operation.LIST" or "list" in str(Operation.LIST)


class TestRepresentation:
    def test_values(self) -> None:
        assert Representation.API_JSON.value == "api_json"
        assert Representation.API_XML.value == "api_xml"


class TestQuerySupport:
    def test_defaults(self) -> None:
        qs = QuerySupport()
        assert qs.pagination == PaginationMode.NONE
        assert qs.filterable_fields == frozenset()
        assert qs.time_range is False
        assert qs.max_page_size is None

    def test_frozen(self) -> None:
        qs = QuerySupport(pagination=PaginationMode.OFFSET)
        try:
            qs.pagination = PaginationMode.CURSOR  # type: ignore[misc]
            raise AssertionError("Should be frozen")
        except AttributeError:
            pass


class TestDatasetRef:
    def _make_ref(self, **kwargs: object) -> DatasetRef:
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

    def test_supports(self) -> None:
        ref = self._make_ref()
        assert ref.supports(Operation.LIST) is True
        assert ref.supports(Operation.GET) is False

    def test_frozen(self) -> None:
        ref = self._make_ref()
        try:
            ref.id = "changed"  # type: ignore[misc]
            raise AssertionError("Should be frozen")
        except AttributeError:
            pass

    def test_raw_metadata_immutable(self) -> None:
        ref = self._make_ref()
        assert isinstance(ref.raw_metadata, MappingProxyType)

    def test_repr(self) -> None:
        ref = self._make_ref()
        r = repr(ref)
        assert "test.dataset" in r
        assert "test" in r

    def test_metadata_defaults(self) -> None:
        ref = self._make_ref()
        assert ref.description is None
        assert ref.tags == ()
        assert ref.source_url is None

    def test_metadata_populated(self) -> None:
        ref = self._make_ref(
            description="Weather forecast data",
            tags=("weather", "forecast"),
            source_url="https://data.go.kr/example",
        )
        assert ref.description == "Weather forecast data"
        assert ref.tags == ("weather", "forecast")
        assert ref.source_url == "https://data.go.kr/example"

    def test_metadata_frozen(self) -> None:
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
    def test_defaults(self) -> None:
        q = Query()
        assert q.filters == {}
        assert q.page is None
        assert q.extra == {}

    def test_with_filters(self) -> None:
        q = Query(filters={"key": "value"}, page=1, page_size=10)
        assert q.filters["key"] == "value"
        assert q.page == 1


class TestRecordBatch:
    def _make_ref(self) -> DatasetRef:
        return DatasetRef(
            id="test.ds",
            provider="test",
            dataset_key="ds",
            name="DS",
            representation=Representation.API_JSON,
        )

    def test_len(self) -> None:
        batch = RecordBatch(items=[{"a": 1}, {"a": 2}], dataset=self._make_ref())
        assert len(batch) == 2

    def test_iter(self) -> None:
        items = [{"a": 1}, {"a": 2}]
        batch = RecordBatch(items=items, dataset=self._make_ref())
        assert list(batch) == items

    def test_bool_empty(self) -> None:
        batch = RecordBatch(items=[], dataset=self._make_ref())
        assert not batch

    def test_bool_nonempty(self) -> None:
        batch = RecordBatch(items=[{"a": 1}], dataset=self._make_ref())
        assert batch


class TestSchemaDescriptor:
    def test_fields(self) -> None:
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
    def test_all_defaults_none(self) -> None:
        fc = FieldConstraints()
        assert fc.max_length is None
        assert fc.min_value is None
        assert fc.max_value is None
        assert fc.pattern is None
        assert fc.allowed_values is None
        assert fc.format is None

    def test_populated(self) -> None:
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

    def test_single_field(self) -> None:
        fc = FieldConstraints(max_length=10)
        assert fc.max_length == 10

    def test_partial_population(self) -> None:
        fc = FieldConstraints(format="date", allowed_values=("yes", "no"))
        assert fc.max_length is None
        assert fc.format == "date"
        assert fc.allowed_values == ("yes", "no")


class TestFieldDescriptorConstraints:
    def test_default_constraints_none(self) -> None:
        fd = FieldDescriptor(name="col")
        assert fd.constraints is None

    def test_with_constraints(self) -> None:
        fc = FieldConstraints(max_length=50, format="YYYYMM")
        fd = FieldDescriptor(name="date_col", type="string", constraints=fc)
        assert fd.constraints is not None
        assert fd.constraints.max_length == 50
        assert fd.constraints.format == "YYYYMM"

    def test_positional_raw_backward_compat(self) -> None:
        proxy = MappingProxyType({"k": "v"})
        fd = FieldDescriptor("col", "Title", "string", "desc", True, proxy)
        assert fd.name == "col"
        assert fd.raw == proxy
        assert fd.constraints is None
