from __future__ import annotations

from typing import Protocol, cast
from pathlib import Path

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.transport.http import HttpTransport


class _FakeResponse:
    def __init__(self, data: bytes, content_type: str = "application/json") -> None:
        self.headers = {"content-type": content_type}
        self.content = data
        self.text = data.decode("utf-8")


class _FixtureTransport:
    def __init__(self, fixture_bytes: bytes) -> None:
        self._response = _FakeResponse(fixture_bytes)

    def request(self, method: str, url: str, **kwargs: object) -> _FakeResponse:
        return self._response


class _AdapterFactory(Protocol):
    def __call__(
        self,
        *,
        config: KPubDataConfig | None = None,
        transport: HttpTransport | None = None,
    ) -> object: ...


def test_seoul_park_info_parses_fixture(tmp_path):
    fixture_path = tmp_path.joinpath("park.json")
    # load fixture from repository
    repo_fixture = (
        Path(__file__).resolve().parents[2] / "fixtures" / "seoul" / "park_info_success.json"
    )
    data = repo_fixture.read_bytes()

    transport = _FixtureTransport(data)
    config = KPubDataConfig(provider_keys={"seoul": "test-key"})
    adapter_module = __import__("kpubdata.providers.seoul.adapter", fromlist=["SeoulAdapter"]) 
    adapter_class_obj = cast(object, adapter_module.SeoulAdapter)
    adapter_class = cast(_AdapterFactory, adapter_class_obj)
    adapter = adapter_class(config=config, transport=cast(HttpTransport, transport))

    ds = adapter.get_dataset("park_info")
    assert isinstance(ds, DatasetRef)

    result = adapter.query_records(ds, Query(filters={"SIGUN_NM": "Test"}))
    assert result.total_count == 1 or result.total_count is None
    assert len(result.items) == 1
    assert result.items[0]["PARK_NAME"] == "Test Park"
