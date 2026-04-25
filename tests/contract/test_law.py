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
    return Path(__file__).resolve().parents[1] / "fixtures" / "law" / name


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


def _build_adapter(fixture_names: list[str]) -> tuple[ProviderAdapter, _FixtureTransport]:
    transport = _FixtureTransport(fixture_names)
    config = KPubDataConfig(provider_keys={"law": "test-law-key"})
    adapter_module = import_module("kpubdata.providers.law.adapter")
    adapter_class_obj = cast(object, adapter_module.LawAdapter)
    adapter_class = cast(_AdapterFactory, adapter_class_obj)
    adapter = adapter_class(
        config=config,
        transport=cast(HttpTransport, cast(object, transport)),
    )
    return adapter, transport


class TestLawAdapterContract(ProviderAdapterContract):
    @pytest.fixture()
    def adapter(self) -> ProviderAdapter:
        adapter, _ = _build_adapter(["success_law_search.json"] * 5)
        return adapter

    @pytest.fixture()
    def valid_dataset_key(self) -> str:
        return "law_search"

    @pytest.fixture()
    def invalid_dataset_key(self) -> str:
        return "nonexistent_dataset_key_xyz"

    @pytest.fixture()
    def sample_dataset(self, adapter: ProviderAdapter) -> DatasetRef:
        return adapter.get_dataset("law_search")

    @pytest.fixture()
    def sample_query(self) -> Query:
        return Query(filters={"query": "임대차", "search": "1"})

    @pytest.fixture()
    def raw_operation(self) -> tuple[str, dict[str, object]]:
        return ("lawSearch", {"query": "임대차", "search": "1"})

    def test_query_records_uses_law_search_url_and_oc_param(self) -> None:
        adapter, transport = _build_adapter(["success_law_search.json"])

        dataset = adapter.get_dataset("law_search")
        _ = adapter.query_records(dataset, Query())

        request_url = cast(str, transport.calls[0]["url"])
        assert request_url.startswith("http://www.law.go.kr/DRF/lawSearch.do?")
        assert "OC=test-law-key" in request_url
        assert "target=law" in request_url
        assert "type=JSON" in request_url
        assert "display=100" in request_url
        assert "page=1" in request_url

    def test_call_raw_supports_law_detail_endpoint(self) -> None:
        adapter, transport = _build_adapter(["success_law_detail.json"])

        dataset = adapter.get_dataset("law_detail")
        raw = adapter.call_raw(dataset, "lawService", {"MST": "17523"})

        request_url = cast(str, transport.calls[0]["url"])
        assert isinstance(raw, dict)
        assert "법령정보" in raw
        assert request_url.startswith("http://www.law.go.kr/DRF/lawService.do?")
        assert "MST=17523" in request_url
