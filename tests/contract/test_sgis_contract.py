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
    return Path(__file__).resolve().parents[1] / "fixtures" / "sgis" / name


class _FakeResponse:
    def __init__(self, data: bytes, content_type: str = "application/json") -> None:
        self.headers: dict[str, str] = {"content-type": content_type}
        self.content: bytes = data
        self.text: str = data.decode("utf-8")


class _FixtureTransport:
    def __init__(self, fixture_names: list[str]) -> None:
        self._responses: list[_FakeResponse] = [
            _FakeResponse(_fixture_path(name).read_bytes()) for name in fixture_names
        ]

    def request(self, _method: str, _url: str, **_kwargs: object) -> _FakeResponse:
        if not self._responses:
            raise AssertionError("No fixture responses remaining")
        return self._responses.pop(0)


class _FixtureAuthClient:
    def get_access_token(self, *, force_refresh: bool = False) -> str:
        _ = force_refresh
        return "contract-token"

    def invalidate(self) -> None:
        return None


class _SgisAdapterFactory(Protocol):
    def __call__(
        self,
        *,
        config: KPubDataConfig | None = None,
        transport: HttpTransport | None = None,
        auth_client: object = None,
    ) -> ProviderAdapter: ...


def _build_adapter(fixture_names: list[str]) -> ProviderAdapter:
    transport = _FixtureTransport(fixture_names)
    config = KPubDataConfig(provider_keys={"sgis": "consumer-key:consumer-secret"})
    adapter_module = import_module("kpubdata.providers.sgis.adapter")
    adapter_class_obj = cast(object, adapter_module.SgisAdapter)
    if not isinstance(adapter_class_obj, type):
        raise AssertionError("SgisAdapter is not a class")
    adapter_class = cast(_SgisAdapterFactory, adapter_class_obj)
    return adapter_class(
        config=config,
        transport=cast(HttpTransport, cast(object, transport)),
        auth_client=_FixtureAuthClient(),
    )


class TestSgisAdapterContract(ProviderAdapterContract):
    @pytest.fixture()
    def adapter(self) -> ProviderAdapter:
        return _build_adapter(["sido_boundary.geojson"] * 5)

    @pytest.fixture()
    def valid_dataset_key(self) -> str:
        return "boundary.sido"

    @pytest.fixture()
    def invalid_dataset_key(self) -> str:
        return "nonexistent_dataset_key_xyz"

    @pytest.fixture()
    def sample_dataset(self, adapter: ProviderAdapter) -> DatasetRef:
        return adapter.get_dataset("boundary.sido")

    @pytest.fixture()
    def sample_query(self) -> Query:
        return Query(filters={"year": "2023", "low_search": 1})

    @pytest.fixture()
    def raw_operation(self) -> tuple[str, dict[str, object]]:
        return ("list", {"year": "2023", "low_search": 1})
