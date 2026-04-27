from __future__ import annotations

import importlib
import sys
from types import SimpleNamespace

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.capability import Operation
from kpubdata.core.models import DatasetRef, Query
from kpubdata.exceptions import ConfigError, DatasetNotFoundError
from kpubdata.providers._common import build_dataset_ref
from kpubdata.providers.krx.adapter import KrxAdapter


class _ExposedKrxAdapter(KrxAdapter):
    def load_pykrx_for_test(self) -> object:
        return self._load_pykrx()


def _unknown_dataset() -> DatasetRef:
    return build_dataset_ref(
        "krx",
        {
            "dataset_key": "unknown",
            "name": "Unknown",
            "representation": "api_json",
            "operations": [Operation.LIST.value, Operation.RAW.value],
        },
    )


def test_list_datasets_returns_empty_list_for_empty_catalogue() -> None:
    adapter = KrxAdapter(config=KPubDataConfig())

    assert adapter.list_datasets() == []
    assert adapter.search_datasets("kospi") == []


def test_get_dataset_unknown_key_raises_dataset_not_found() -> None:
    adapter = KrxAdapter(config=KPubDataConfig())

    with pytest.raises(DatasetNotFoundError, match="krx.unknown"):
        _ = adapter.get_dataset("unknown")


def test_query_records_unknown_dataset_raises_dataset_not_found() -> None:
    adapter = KrxAdapter(config=KPubDataConfig())

    with pytest.raises(DatasetNotFoundError, match="krx.unknown"):
        _ = adapter.query_records(_unknown_dataset(), Query())


def test_call_raw_unknown_dataset_raises_dataset_not_found() -> None:
    adapter = KrxAdapter(config=KPubDataConfig())

    with pytest.raises(DatasetNotFoundError, match="krx.unknown"):
        _ = adapter.call_raw(_unknown_dataset(), "list", {})


def test_query_records_known_scaffold_dataset_raises_dataset_not_found() -> None:
    dataset = build_dataset_ref(
        "krx",
        {
            "dataset_key": "sample",
            "name": "Sample dataset",
            "representation": "api_json",
            "operations": [Operation.LIST.value],
        },
    )
    adapter = KrxAdapter(config=KPubDataConfig(), catalogue=[dataset])

    with pytest.raises(DatasetNotFoundError, match="krx.sample"):
        _ = adapter.query_records(dataset, Query())


def test_call_raw_known_scaffold_dataset_raises_dataset_not_found() -> None:
    dataset = build_dataset_ref(
        "krx",
        {
            "dataset_key": "sample",
            "name": "Sample dataset",
            "representation": "api_json",
            "operations": [Operation.RAW.value],
        },
    )
    adapter = KrxAdapter(config=KPubDataConfig(), catalogue=[dataset])

    with pytest.raises(DatasetNotFoundError, match="krx.sample"):
        _ = adapter.call_raw(dataset, "list", {})


def test_get_schema_builds_from_catalogue_metadata() -> None:
    dataset = build_dataset_ref(
        "krx",
        {
            "dataset_key": "sample",
            "name": "Sample dataset",
            "representation": "api_json",
            "operations": [Operation.LIST.value],
            "fields": [
                {
                    "name": "ticker",
                    "title": "Ticker",
                    "type": "string",
                    "description": "Market ticker",
                    "nullable": False,
                }
            ],
        },
    )
    adapter = KrxAdapter(config=KPubDataConfig(), catalogue=[dataset])

    schema = adapter.get_schema(dataset)

    assert schema is not None
    assert [field.name for field in schema.fields] == ["ticker"]
    assert schema.fields[0].title == "Ticker"
    assert schema.fields[0].nullable is False


def test_load_pykrx_raises_install_hint_when_dependency_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = _ExposedKrxAdapter(config=KPubDataConfig())

    def _raise_import_error() -> SimpleNamespace:
        raise ImportError("pykrx is unavailable")

    monkeypatch.setattr(adapter, "_import_pykrx", _raise_import_error)

    with pytest.raises(ConfigError, match=r"Install kpubdata\[krx\] to enable KRX provider"):
        _ = adapter.load_pykrx_for_test()


def test_load_pykrx_returns_imported_module(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = _ExposedKrxAdapter(config=KPubDataConfig())
    pykrx_module = SimpleNamespace(stock=SimpleNamespace())

    def _import_module(name: str) -> SimpleNamespace:
        assert name == "pykrx"
        return pykrx_module

    monkeypatch.setattr(importlib, "import_module", _import_module)

    assert adapter.load_pykrx_for_test() is pykrx_module


def test_adapter_is_constructible_without_krx_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KPUBDATA_KRX_API_KEY", raising=False)

    adapter = KrxAdapter(config=KPubDataConfig.from_env())

    assert adapter.name == "krx"
    assert adapter.requires_api_key is False


def test_adapter_construction_does_not_import_pykrx(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delitem(sys.modules, "pykrx", raising=False)

    _ = KrxAdapter(config=KPubDataConfig())

    assert "pykrx" not in sys.modules
