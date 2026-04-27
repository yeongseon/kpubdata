from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Protocol, cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.transport.http import HttpTransport
from tests.contract.provider_adapter import ProviderAdapterContract


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "bok" / name


def _load_fixture_bytes(name: str) -> bytes:
    return _fixture_path(name).read_bytes()


class _FakeResponse:
    def __init__(self, data: bytes, content_type: str = "application/json") -> None:
        self.headers: dict[str, str] = {"content-type": content_type}
        self.content: bytes = data
        self.text: str = data.decode("utf-8")


class _FixtureTransport:
    def __init__(self, fixture_names: list[str]) -> None:
        self._responses: list[_FakeResponse] = [
            _FakeResponse(_load_fixture_bytes(name)) for name in fixture_names
        ]
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> _FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        if not self._responses:
            raise AssertionError("No fixture responses remaining")
        return self._responses.pop(0)


class _AdapterFactory(Protocol):
    def __call__(
        self,
        *,
        config: KPubDataConfig | None = None,
        transport: HttpTransport | None = None,
    ) -> ProviderAdapter: ...


def _build_adapter_with_transport(
    fixture_names: list[str],
) -> tuple[ProviderAdapter, _FixtureTransport]:
    transport = _FixtureTransport(fixture_names)
    config = KPubDataConfig(provider_keys={"bok": "test-key"})
    adapter_module = import_module("kpubdata.providers.bok.adapter")
    adapter_class_obj = cast(object, adapter_module.BokAdapter)
    if not isinstance(adapter_class_obj, type):
        raise AssertionError("BokAdapter is not a class")
    adapter_class = cast(_AdapterFactory, adapter_class_obj)
    adapter_obj = adapter_class(
        config=config,
        transport=cast(HttpTransport, cast(object, transport)),
    )
    return adapter_obj, transport


def _build_adapter(fixture_names: list[str]) -> ProviderAdapter:
    adapter, _ = _build_adapter_with_transport(fixture_names)
    return adapter


class TestBokAdapterContract(ProviderAdapterContract):
    @pytest.fixture()
    def adapter(self) -> ProviderAdapter:
        return _build_adapter(["success_single_page.json"] * 5)

    @pytest.fixture()
    def valid_dataset_key(self) -> str:
        return "base_rate"

    @pytest.fixture()
    def invalid_dataset_key(self) -> str:
        return "nonexistent_dataset_key_xyz"

    @pytest.fixture()
    def sample_dataset(self, adapter: ProviderAdapter) -> DatasetRef:
        return adapter.get_dataset("base_rate")

    @pytest.fixture()
    def sample_query(self) -> Query:
        return Query(start_date="202401", end_date="202403")

    @pytest.fixture()
    def raw_operation(self) -> tuple[str, dict[str, object]]:
        return (
            "StatisticSearch",
            {"start_date": "202401", "end_date": "202403", "frequency": "M"},
        )


def test_usd_krw_query_records_builds_daily_ecos_url_and_parses_fixture() -> None:
    adapter, transport = _build_adapter_with_transport(["usd_krw_success.json"])
    dataset = adapter.get_dataset("usd_krw")

    batch = adapter.query_records(
        dataset,
        Query(
            start_date="20240101",
            end_date="20240105",
            extra={"frequency": "D"},
        ),
    )

    request_url = cast(str, transport.calls[0]["url"])
    assert "/StatisticSearch/" in request_url
    assert "731Y003/D/20240101/20240105/0000003" in request_url
    assert len(batch.items) == 4
    assert [item["TIME"] for item in batch.items] == [
        "20240102",
        "20240103",
        "20240104",
        "20240105",
    ]


def test_bond_yield_3y_query_records_builds_daily_ecos_url_and_parses_fixture() -> None:
    adapter, transport = _build_adapter_with_transport(["bond_yield_3y_success.json"])
    dataset = adapter.get_dataset("bond_yield_3y")

    batch = adapter.query_records(
        dataset,
        Query(
            start_date="20240102",
            end_date="20240108",
            extra={"frequency": "D"},
        ),
    )

    request_url = cast(str, transport.calls[0]["url"])
    assert "/StatisticSearch/" in request_url
    assert "817Y002/D/20240102/20240108/010200000" in request_url
    assert len(batch.items) == 5
    assert [item["TIME"] for item in batch.items] == [
        "20240102",
        "20240103",
        "20240104",
        "20240105",
        "20240108",
    ]
