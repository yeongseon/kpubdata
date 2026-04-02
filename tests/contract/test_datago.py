from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.providers.datago.adapter import DataGoAdapter
from kpubdata.transport.http import HttpTransport
from tests.contract.provider_adapter import ProviderAdapterContract


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "datago" / name


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


def _build_adapter(fixture_names: list[str]) -> DataGoAdapter:
    transport = _FixtureTransport(fixture_names)
    config = KPubDataConfig(provider_keys={"datago": "test-key"})
    return DataGoAdapter(
        config=config,
        transport=cast(HttpTransport, cast(object, transport)),
    )


class TestDataGoAdapterContract(ProviderAdapterContract):
    @pytest.fixture()
    def adapter(self) -> DataGoAdapter:
        return _build_adapter(["success_single_page.json"] * 5)

    @pytest.fixture()
    def valid_dataset_key(self) -> str:
        return "village_fcst"

    @pytest.fixture()
    def invalid_dataset_key(self) -> str:
        return "nonexistent_dataset_key_xyz"

    @pytest.fixture()
    def sample_dataset(self, adapter: DataGoAdapter) -> DatasetRef:
        return adapter.get_dataset("village_fcst")

    @pytest.fixture()
    def sample_query(self) -> Query:
        return Query()

    @pytest.fixture()
    def raw_operation(self) -> tuple[str, dict[str, object]]:
        return ("getVilageFcst", {})

    def test_get_record_not_implemented(self, adapter: DataGoAdapter) -> None:
        dataset = adapter.get_dataset("village_fcst")
        with pytest.raises(NotImplementedError):
            _ = adapter.get_record(dataset, {})
