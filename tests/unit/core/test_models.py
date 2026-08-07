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
from kpubdata.exceptions import InvalidRequestError


class TestOperation:
    """Tests for Operation enum."""

    def test_values(self) -> None:
        assert Operation.LIST.value == "list"
        assert Operation.GET.value == "get"
        assert Operation.RAW.value == "raw"

    def test_str_mixin(self) -> None:
        assert str(Operation.LIST) == "Operation.LIST" or "list" in str(Operation.LIST)


class TestRepresentation:
    """Tests for Representation enum."""

    def test_values(self) -> None:
        assert Representation.API_JSON.value == "api_json"
        assert Representation.API_XML.value == "api_xml"


class TestQuerySupport:
    """Tests for QuerySupport dataclass."""

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
    """Tests for DatasetRef dataclass."""

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
    """Tests for Query dataclass."""

    def test_defaults(self) -> None:
        q = Query()
        assert q.filters == {}
        assert q.page is None
        assert q.extra == {}

    def test_with_filters(self) -> None:
        q = Query(filters={"key": "value"}, page=1, page_size=10)
        assert q.filters["key"] == "value"
        assert q.page == 1

    def test_all_fields_valid(self) -> None:
        q = Query(
            filters={"region": "11"},
            page=1,
            page_size=100,
            cursor="next-token",
            start_date="202401",
            end_date="202412",
            fields=["name", "date"],
            sort=["date"],
            extra={"provider_option": True},
        )
        assert q.filters == {"region": "11"}
        assert q.page == 1
        assert q.page_size == 100
        assert q.cursor == "next-token"
        assert q.start_date == "202401"
        assert q.end_date == "202412"
        assert q.fields == ["name", "date"]
        assert q.sort == ["date"]
        assert q.extra == {"provider_option": True}


class TestQueryPageValidation:
    """Tests for Query page field validation."""

    def test_valid(self) -> None:
        q = Query(page=1)
        assert q.page == 1

    def test_none_allowed(self) -> None:
        q = Query(page=None)
        assert q.page is None

    def test_zero_rejected(self) -> None:
        try:
            Query(page=0)
            raise AssertionError("page=0 should raise InvalidRequestError")
        except InvalidRequestError as e:
            assert "page must be a positive integer" in str(e)

    def test_negative_rejected(self) -> None:
        try:
            Query(page=-1)
            raise AssertionError("page=-1 should raise InvalidRequestError")
        except InvalidRequestError as e:
            assert "page must be a positive integer" in str(e)

    def test_bool_rejected(self) -> None:
        try:
            Query(page=True)
            raise AssertionError("page=True should raise InvalidRequestError")
        except InvalidRequestError as e:
            assert "page must be an integer, not bool" in str(e)

    def test_string_rejected(self) -> None:
        try:
            Query(page="1")
            raise AssertionError("page='1' should raise InvalidRequestError")
        except InvalidRequestError as e:
            assert "page must be an integer or None" in str(e)


class TestQueryPageSizeValidation:
    """Tests for Query page_size field validation."""

    def test_valid(self) -> None:
        q = Query(page_size=1)
        assert q.page_size == 1

    def test_none_allowed(self) -> None:
        q = Query(page_size=None)
        assert q.page_size is None

    def test_zero_rejected(self) -> None:
        try:
            Query(page_size=0)
            raise AssertionError("page_size=0 should raise InvalidRequestError")
        except InvalidRequestError as e:
            assert "page_size must be a positive integer" in str(e)

    def test_negative_rejected(self) -> None:
        try:
            Query(page_size=-1)
            raise AssertionError("page_size=-1 should raise InvalidRequestError")
        except InvalidRequestError as e:
            assert "page_size must be a positive integer" in str(e)

    def test_bool_rejected(self) -> None:
        try:
            Query(page_size=True)
            raise AssertionError("page_size=True should raise InvalidRequestError")
        except InvalidRequestError as e:
            assert "page_size must be an integer, not bool" in str(e)

    def test_float_rejected(self) -> None:
        try:
            Query(page_size=1.5)
            raise AssertionError("page_size=1.5 should raise InvalidRequestError")
        except InvalidRequestError as e:
            assert "page_size must be an integer or None" in str(e)

    def test_string_rejected(self) -> None:
        try:
            Query(page_size="100")
            raise AssertionError("page_size='100' should raise InvalidRequestError")
        except InvalidRequestError as e:
            assert "page_size must be an integer or None" in str(e)


class TestQueryCursorValidation:
    """Tests for Query cursor field validation."""

    def test_valid(self) -> None:
        q = Query(cursor="abc")
        assert q.cursor == "abc"

    def test_none_allowed(self) -> None:
        q = Query(cursor=None)
        assert q.cursor is None

    def test_int_rejected(self) -> None:
        try:
            Query(cursor=123)
            raise AssertionError("cursor=123 should raise InvalidRequestError")
        except InvalidRequestError as e:
            assert "cursor must be a string or None" in str(e)

    def test_list_rejected(self) -> None:
        try:
            Query(cursor=[])
            raise AssertionError("cursor=[] should raise InvalidRequestError")
        except InvalidRequestError as e:
            assert "cursor must be a string or None" in str(e)

    def test_empty_string_rejected(self) -> None:
        try:
            Query(cursor="")
            raise AssertionError("cursor='' should raise InvalidRequestError")
        except InvalidRequestError as e:
            assert "cursor must be a non-empty string" in str(e)


class TestQueryDateValidation:
    """Tests for Query date field validation."""

    def test_valid_yyyymm_format(self) -> None:
        q = Query(start_date="202401", end_date="202412")
        assert q.start_date == "202401"
        assert q.end_date == "202412"

    def test_valid_yyyymmdd_format(self) -> None:
        q = Query(start_date="20240102", end_date="20240108")
        assert q.start_date == "20240102"
        assert q.end_date == "20240108"

    def test_none_allowed(self) -> None:
        q = Query(start_date=None, end_date=None)
        assert q.start_date is None
        assert q.end_date is None

    def test_int_rejected(self) -> None:
        try:
            Query(start_date=202401)
            raise AssertionError("start_date=202401 should raise InvalidRequestError")
        except InvalidRequestError as e:
            assert "start_date must be a string or None" in str(e)

    def test_list_rejected(self) -> None:
        try:
            Query(end_date=[])
            raise AssertionError("end_date=[] should raise InvalidRequestError")
        except InvalidRequestError as e:
            assert "end_date must be a string or None" in str(e)

    def test_empty_string_rejected(self) -> None:
        try:
            Query(start_date="")
            raise AssertionError("start_date='' should raise InvalidRequestError")
        except InvalidRequestError as e:
            assert "start_date must be a non-empty string" in str(e)

    def test_whitespace_rejected(self) -> None:
        try:
            Query(start_date="   ")
            raise AssertionError("start_date='   ' should raise InvalidRequestError")
        except InvalidRequestError as e:
            assert "start_date must be a non-empty string" in str(e)


class TestQueryFieldsValidation:
    """Tests for Query fields field validation."""

    def test_valid(self) -> None:
        q = Query(fields=["a", "b"])
        assert q.fields == ["a", "b"]

    def test_empty_list(self) -> None:
        q = Query(fields=[])
        assert q.fields == []

    def test_none_allowed(self) -> None:
        q = Query(fields=None)
        assert q.fields is None

    def test_string_rejected(self) -> None:
        try:
            Query(fields="a")
            raise AssertionError("fields='a' should raise InvalidRequestError")
        except InvalidRequestError as e:
            assert "fields must be a list of strings or None" in str(e)

    def test_tuple_rejected(self) -> None:
        try:
            Query(fields=("a", "b"))
            raise AssertionError("fields=('a', 'b') should raise InvalidRequestError")
        except InvalidRequestError as e:
            assert "fields must be a list of strings or None" in str(e)

    def test_non_string_element_rejected(self) -> None:
        try:
            Query(fields=["a", 1])
            raise AssertionError("fields=['a', 1] should raise InvalidRequestError")
        except InvalidRequestError as e:
            assert "fields must contain only strings" in str(e)
            assert "at index 1" in str(e)


class TestQuerySortValidation:
    """Tests for Query sort field validation."""

    def test_valid(self) -> None:
        q = Query(sort=["date", "name"])
        assert q.sort == ["date", "name"]

    def test_empty_list(self) -> None:
        q = Query(sort=[])
        assert q.sort == []

    def test_none_allowed(self) -> None:
        q = Query(sort=None)
        assert q.sort is None

    def test_non_string_element_rejected(self) -> None:
        try:
            Query(sort=["date", None])
            raise AssertionError("sort=['date', None] should raise InvalidRequestError")
        except InvalidRequestError as e:
            assert "sort must contain only strings" in str(e)


class TestQueryFiltersValidation:
    """Tests for Query filters field validation."""

    def test_valid(self) -> None:
        q = Query(filters={"a": 1})
        assert q.filters == {"a": 1}

    def test_empty_dict(self) -> None:
        q = Query(filters={})
        assert q.filters == {}

    def test_nested_dict(self) -> None:
        q = Query(filters={"a": {"nested": True}})
        assert q.filters == {"a": {"nested": True}}

    def test_list_rejected(self) -> None:
        try:
            Query(filters=[])
            raise AssertionError("filters=[] should raise InvalidRequestError")
        except InvalidRequestError as e:
            assert "filters must be a dict" in str(e)

    def test_non_string_key_rejected(self) -> None:
        try:
            Query(filters={1: "value"})
            raise AssertionError("filters={1: 'value'} should raise InvalidRequestError")
        except InvalidRequestError as e:
            assert "filters keys must be strings" in str(e)


class TestQueryExtraValidation:
    """Tests for Query extra field validation."""

    def test_valid(self) -> None:
        q = Query(extra={"option": True})
        assert q.extra == {"option": True}

    def test_empty_dict(self) -> None:
        q = Query(extra={})
        assert q.extra == {}

    def test_list_rejected(self) -> None:
        try:
            Query(extra=[])
            raise AssertionError("extra=[] should raise InvalidRequestError")
        except InvalidRequestError as e:
            assert "extra must be a dict" in str(e)

    def test_non_string_key_rejected(self) -> None:
        try:
            Query(extra={1: "value"})
            raise AssertionError("extra={1: 'value'} should raise InvalidRequestError")
        except InvalidRequestError as e:
            assert "extra keys must be strings" in str(e)


class TestRecordBatch:
    """Tests for RecordBatch dataclass."""

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
    """Tests for SchemaDescriptor dataclass."""

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
    """Tests for FieldConstraints dataclass."""

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
    """Tests for FieldDescriptor with constraints."""

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
