from __future__ import annotations

import json
from importlib import import_module
from pathlib import Path
from typing import Protocol, cast

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query, RecordBatch
from kpubdata.transport.http import HttpTransport


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parents[3] / "fixtures" / "law" / name


def _load_fixture(name: str) -> dict[str, object]:
    payload = cast(object, json.loads(_fixture_path(name).read_text(encoding="utf-8")))
    if isinstance(payload, dict):
        return cast(dict[str, object], payload)
    raise ValueError(f"Fixture must be object: {name}")


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.headers: dict[str, str] = {"content-type": "application/json"}
        self.text: str = json.dumps(payload, ensure_ascii=False)
        self.content: bytes = self.text.encode("utf-8")


class FakeTransport:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self._responses: list[FakeResponse] = list(responses)
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        return self._responses.pop(0)


class _AdapterFactory(Protocol):
    def __call__(
        self,
        *,
        config: KPubDataConfig | None = None,
        transport: HttpTransport | None = None,
    ) -> _LawAdapterProtocol: ...


class _LawAdapterProtocol(Protocol):
    def get_dataset(self, dataset_key: str) -> DatasetRef: ...

    def list_datasets(self) -> list[DatasetRef]: ...

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch: ...

    def call_raw(
        self, dataset: DatasetRef, operation: str, params: dict[str, object]
    ) -> object: ...


def _build_adapter_with_transport(
    dataset_key: str,
    responses: list[FakeResponse],
) -> tuple[_LawAdapterProtocol, DatasetRef, FakeTransport]:
    transport = FakeTransport(responses)
    adapter_module = import_module("kpubdata.providers.law.adapter")
    adapter_class_obj = cast(object, adapter_module.LawAdapter)
    adapter_class = cast(_AdapterFactory, adapter_class_obj)
    adapter = adapter_class(
        config=KPubDataConfig(provider_keys={"law": "test-law-key"}),
        transport=cast(HttpTransport, cast(object, transport)),
    )
    dataset = adapter.get_dataset(dataset_key)
    return adapter, dataset, transport


def test_query_records_parses_law_search_fixture() -> None:
    payload = _load_fixture("success_law_search.json")
    adapter, dataset, transport = _build_adapter_with_transport(
        "law_search", [FakeResponse(payload)]
    )

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert batch.total_count == 2
    assert batch.next_page is None
    assert batch.raw == payload
    assert batch.items[0]["법령명한글"] == "주택임대차보호법"
    assert len(transport.calls) == 1


def test_query_records_sets_next_page_and_uses_law_params() -> None:
    payload = _load_fixture("success_law_search.json")
    adapter, dataset, transport = _build_adapter_with_transport(
        "law_search", [FakeResponse(payload)]
    )

    batch = adapter.query_records(
        dataset,
        Query(page=1, page_size=1, filters={"query": "임대차", "search": "1"}),
    )

    request_url = cast(str, transport.calls[0]["url"])
    assert batch.next_page == 2
    assert "OC=test-law-key" in request_url
    assert "target=law" in request_url
    assert "type=JSON" in request_url
    assert "display=1" in request_url
    assert "page=1" in request_url
    assert "query=%EC%9E%84%EB%8C%80%EC%B0%A8" in request_url
    assert "search=1" in request_url


def test_query_records_parses_ordin_search_fixture() -> None:
    payload = _load_fixture("success_ordin_search.json")
    adapter, dataset, transport = _build_adapter_with_transport(
        "ordin_search", [FakeResponse(payload)]
    )

    batch = adapter.query_records(dataset, Query(page=1, page_size=2))

    request_url = cast(str, transport.calls[0]["url"])
    assert len(batch.items) == 2
    assert batch.total_count == 2
    assert batch.items[0]["자치법규명"] == "서울특별시 주택 임대차분쟁조정 지원 조례"
    assert "target=ordin" in request_url
    assert "display=2" in request_url


def test_call_raw_returns_law_detail_payload() -> None:
    payload = _load_fixture("success_law_detail.json")
    adapter, dataset, transport = _build_adapter_with_transport(
        "law_detail", [FakeResponse(payload)]
    )

    raw = adapter.call_raw(dataset, "lawService", {"MST": "17523"})

    request_url = cast(str, transport.calls[0]["url"])
    assert raw == payload
    assert "OC=test-law-key" in request_url
    assert "target=law" in request_url
    assert "type=JSON" in request_url
    assert "MST=17523" in request_url


def test_adapter_lists_all_datasets() -> None:
    adapter_module = import_module("kpubdata.providers.law.adapter")
    adapter_class_obj = cast(object, adapter_module.LawAdapter)
    adapter_class = cast(_AdapterFactory, adapter_class_obj)
    adapter = adapter_class(config=KPubDataConfig(provider_keys={"law": "test-law-key"}))

    datasets = adapter.list_datasets()

    assert [dataset.dataset_key for dataset in datasets] == [
        "law_search",
        "law_detail",
        "ordin_search",
    ]
