from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef
from kpubdata.providers.datago.adapter import DataGoAdapter
from kpubdata.transport.http import HttpTransport


def fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parents[3] / "fixtures" / "datago" / name


def load_json_fixture(name: str) -> dict[str, object]:
    payload = cast(object, json.loads(fixture_path(name).read_text(encoding="utf-8")))
    if isinstance(payload, dict):
        return cast(dict[str, object], payload)
    raise ValueError(f"Fixture must contain a JSON object: {name}")


def load_fixture_bytes(name: str) -> bytes:
    return fixture_path(name).read_bytes()


class FakeResponse:
    def __init__(self, data: bytes, content_type: str = "application/json") -> None:
        self.headers: dict[str, str] = {"content-type": content_type}
        self.content: bytes = data
        self.text: str = data.decode("utf-8")


class FixtureTransport:
    def __init__(self, fixture_names: list[str], content_type: str = "application/json") -> None:
        self._responses: list[FakeResponse] = [
            FakeResponse(load_fixture_bytes(name), content_type=content_type)
            for name in fixture_names
        ]
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        if not self._responses:
            raise AssertionError("No fixture responses remaining")
        return self._responses.pop(0)


@pytest.fixture
def configured_adapter() -> Callable[
    [list[str], str], tuple[DataGoAdapter, DatasetRef, FixtureTransport]
]:
    def _build(
        fixture_names: list[str],
        content_type: str = "application/json",
    ) -> tuple[DataGoAdapter, DatasetRef, FixtureTransport]:
        transport = FixtureTransport(fixture_names=fixture_names, content_type=content_type)
        config = KPubDataConfig(provider_keys={"datago": "test-key"})
        adapter = DataGoAdapter(
            config=config,
            transport=cast(HttpTransport, cast(object, transport)),
        )
        dataset = adapter.get_dataset("village_fcst")
        return adapter, dataset, transport

    return _build
