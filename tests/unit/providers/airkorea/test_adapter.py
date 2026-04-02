from __future__ import annotations

from typing import cast

import pytest

from kpubdata.core.models import DatasetRef, Query
from kpubdata.providers.airkorea import AirKoreaAdapter
from kpubdata.providers.airkorea.adapter import AirKoreaAdapter as AirKoreaAdapterFromModule


def test_import_from_package_init_exports_adapter() -> None:
    assert AirKoreaAdapter is AirKoreaAdapterFromModule


def test_name_property() -> None:
    adapter = AirKoreaAdapter()

    assert adapter.name == "airkorea"


@pytest.mark.parametrize(
    "method_name",
    [
        "list_datasets",
        "search_datasets",
        "get_dataset",
        "query_records",
        "get_record",
        "get_schema",
        "call_raw",
    ],
)
def test_stub_methods_raise_not_implemented(method_name: str) -> None:
    adapter = AirKoreaAdapter()
    dataset = cast(DatasetRef, object())

    with pytest.raises(NotImplementedError):
        if method_name == "list_datasets":
            _ = adapter.list_datasets()
        elif method_name == "search_datasets":
            _ = adapter.search_datasets("query")
        elif method_name == "get_dataset":
            _ = adapter.get_dataset("dataset-key")
        elif method_name == "query_records":
            _ = adapter.query_records(dataset, Query())
        elif method_name == "get_record":
            _ = adapter.get_record(dataset, {"id": 1})
        elif method_name == "get_schema":
            _ = adapter.get_schema(dataset)
        elif method_name == "call_raw":
            _ = adapter.call_raw(dataset, "operation", {"x": 1})
