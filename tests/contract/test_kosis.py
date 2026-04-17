from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from typing import cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.exceptions import AuthError
from kpubdata.transport.http import HttpTransport
from tests.contract.provider_adapter import ProviderAdapterContract


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "kosis" / name


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


def _build_adapter(fixture_names: list[str]) -> ProviderAdapter:
    transport = _FixtureTransport(fixture_names)
    config = KPubDataConfig(provider_keys={"kosis": "test-key"})
    module = import_module("kpubdata.providers.kosis.adapter")
    adapter_class = cast(Callable[..., ProviderAdapter], module.KosisAdapter)
    return adapter_class(
        config=config,
        transport=cast(HttpTransport, cast(object, transport)),
    )


class TestKosisAdapterContract(ProviderAdapterContract):
    @pytest.fixture()
    def adapter(self) -> ProviderAdapter:
        return _build_adapter(["success_single_page.json"] * 5)

    @pytest.fixture()
    def valid_dataset_key(self) -> str:
        return "population_migration"

    @pytest.fixture()
    def invalid_dataset_key(self) -> str:
        return "nonexistent_dataset_key_xyz"

    @pytest.fixture()
    def sample_dataset(self, adapter: ProviderAdapter) -> DatasetRef:
        return adapter.get_dataset("population_migration")

    @pytest.fixture()
    def sample_query(self) -> Query:
        return Query(start_date="202401", end_date="202401")

    @pytest.fixture()
    def raw_operation(self) -> tuple[str, dict[str, object]]:
        return ("statisticsParameterData", {})

    def test_query_records_empty_array_returns_empty_batch(self) -> None:
        adapter = _build_adapter(["success_empty.json"])
        dataset = adapter.get_dataset("population_migration")

        batch = adapter.query_records(dataset, Query(start_date="202401", end_date="202401"))

        assert batch.items == []
        assert batch.total_count == 0

    def test_query_records_auth_error_maps_to_auth_error(self) -> None:
        adapter = _build_adapter(["error_auth.json"])
        dataset = adapter.get_dataset("population_migration")

        with pytest.raises(AuthError):
            _ = adapter.query_records(dataset, Query(start_date="202401", end_date="202401"))
