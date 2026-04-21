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
    return Path(__file__).resolve().parents[1] / "fixtures" / "seoul" / name


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


def _build_adapter(fixture_names: list[str]) -> ProviderAdapter:
    transport = _FixtureTransport(fixture_names)
    config = KPubDataConfig(provider_keys={"seoul": "test-key"})
    adapter_module = import_module("kpubdata.providers.seoul.adapter")
    adapter_class_obj = cast(object, adapter_module.SeoulAdapter)
    if not isinstance(adapter_class_obj, type):
        raise AssertionError("SeoulAdapter is not a class")
    adapter_class = cast(_AdapterFactory, adapter_class_obj)
    return adapter_class(
        config=config,
        transport=cast(HttpTransport, cast(object, transport)),
    )


class TestSeoulAdapterContract(ProviderAdapterContract):
    @pytest.fixture()
    def adapter(self) -> ProviderAdapter:
        return _build_adapter(["subway_realtime_arrival_success.json"] * 5)

    @pytest.fixture()
    def valid_dataset_key(self) -> str:
        return "subway_realtime_arrival"

    @pytest.fixture()
    def invalid_dataset_key(self) -> str:
        return "nonexistent_dataset_key_xyz"

    @pytest.fixture()
    def sample_dataset(self, adapter: ProviderAdapter) -> DatasetRef:
        return adapter.get_dataset("subway_realtime_arrival")

    @pytest.fixture()
    def sample_query(self) -> Query:
        return Query(filters={"stationName": "강남"})

    @pytest.fixture()
    def raw_operation(self) -> tuple[str, dict[str, object]]:
        return ("realtimeStationArrival", {"stationName": "강남", "page_no": 1, "page_size": 5})
