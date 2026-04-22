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
    return Path(__file__).resolve().parents[1] / "fixtures" / "localdata" / name


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
    config = KPubDataConfig(provider_keys={"localdata": "test-key"})
    adapter_module = import_module("kpubdata.providers.localdata.adapter")
    adapter_class_obj = cast(object, adapter_module.LocaldataAdapter)
    if not isinstance(adapter_class_obj, type):
        raise AssertionError("LocaldataAdapter is not a class")
    adapter_class = cast(_AdapterFactory, adapter_class_obj)
    adapter_obj = adapter_class(
        config=config,
        transport=cast(HttpTransport, cast(object, transport)),
    )
    return adapter_obj


class TestLocaldataAdapterContract(ProviderAdapterContract):
    @pytest.fixture()
    def adapter(self) -> ProviderAdapter:
        return _build_adapter(
            [
                "general_restaurant_success.json",
                "rest_cafe_success.json",
                "bakery_success.json",
                "hospital_success.json",
                "clinic_success.json",
                "pharmacy_success.json",
                "animal_hospital_success.json",
                "optical_shop_success.json",
                "public_bath_success.json",
                "laundry_success.json",
                "barber_shop_success.json",
                "beauty_salon_success.json",
                "pet_grooming_success.json",
                "dance_academy_success.json",
                "karaoke_success.json",
                "singing_bar_success.json",
                "billiard_hall_success.json",
                "performance_hall_success.json",
                "movie_theater_success.json",
                "swimming_pool_success.json",
                "fitness_center_success.json",
                "ice_rink_success.json",
                "golf_course_success.json",
                "golf_practice_range_success.json",
                "horse_riding_success.json",
                "ski_resort_success.json",
            ]
        )

    @pytest.fixture()
    def valid_dataset_key(self) -> str:
        return "general_restaurant"

    @pytest.fixture()
    def invalid_dataset_key(self) -> str:
        return "nonexistent_dataset_key_xyz"

    @pytest.fixture()
    def sample_dataset(self, adapter: ProviderAdapter) -> DatasetRef:
        return adapter.get_dataset("general_restaurant")

    @pytest.fixture()
    def sample_query(self) -> Query:
        return Query()

    @pytest.fixture()
    def raw_operation(self) -> tuple[str, dict[str, object]]:
        return ("info", {"pageNo": "1", "numOfRows": "10"})
