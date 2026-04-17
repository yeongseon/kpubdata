from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Protocol, cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.exceptions import AuthError
from kpubdata.transport.http import HttpTransport
from tests.contract.provider_adapter import ProviderAdapterContract


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "lofin" / name


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
    config = KPubDataConfig(provider_keys={"lofin": "test-key"})
    adapter_module = import_module("kpubdata.providers.lofin.adapter")
    adapter_class_obj = cast(object, adapter_module.LofinAdapter)
    if not isinstance(adapter_class_obj, type):
        raise AssertionError("LofinAdapter is not a class")
    adapter_class = cast(_AdapterFactory, adapter_class_obj)
    adapter_obj = adapter_class(
        config=config,
        transport=cast(HttpTransport, cast(object, transport)),
    )
    return adapter_obj


class TestLofinAdapterContract(ProviderAdapterContract):
    @pytest.fixture()
    def adapter(self) -> ProviderAdapter:
        return _build_adapter(["success_single_page.json"] * 5)

    @pytest.fixture()
    def valid_dataset_key(self) -> str:
        return "expenditure_budget"

    @pytest.fixture()
    def invalid_dataset_key(self) -> str:
        return "nonexistent_dataset_key_xyz"

    @pytest.fixture()
    def sample_dataset(self, adapter: ProviderAdapter) -> DatasetRef:
        return adapter.get_dataset("expenditure_budget")

    @pytest.fixture()
    def sample_query(self) -> Query:
        return Query()

    @pytest.fixture()
    def raw_operation(self) -> tuple[str, dict[str, object]]:
        return ("list", {"pIndex": "1", "pSize": "10"})

    def test_get_record_not_implemented(self, adapter: ProviderAdapter) -> None:
        dataset = adapter.get_dataset("expenditure_budget")
        with pytest.raises(NotImplementedError):
            _ = adapter.get_record(dataset, {})

    def test_query_records_uses_lofin365_url_and_key_param(self) -> None:
        transport = _FixtureTransport(["success_single_page.json"])
        config = KPubDataConfig(provider_keys={"lofin": "test-key"})
        adapter_module = import_module("kpubdata.providers.lofin.adapter")
        adapter_class_obj = cast(object, adapter_module.LofinAdapter)
        if not isinstance(adapter_class_obj, type):
            raise AssertionError("LofinAdapter is not a class")
        adapter_class = cast(_AdapterFactory, adapter_class_obj)
        adapter = adapter_class(
            config=config,
            transport=cast(HttpTransport, cast(object, transport)),
        )

        dataset = adapter.get_dataset("expenditure_budget")
        _ = adapter.query_records(dataset, Query())

        request_url = cast(str, transport.calls[0]["url"])
        assert request_url.startswith("https://www.lofin365.go.kr/lf/hub/AJGCF")
        assert "?Key=test-key&Type=json&pIndex=1&pSize=100" in request_url

    def test_query_records_handles_top_level_auth_error(self) -> None:
        transport = _FixtureTransport(["error_auth.json"])
        config = KPubDataConfig(provider_keys={"lofin": "invalid-key"})
        adapter_module = import_module("kpubdata.providers.lofin.adapter")
        adapter_class_obj = cast(object, adapter_module.LofinAdapter)
        if not isinstance(adapter_class_obj, type):
            raise AssertionError("LofinAdapter is not a class")
        adapter_class = cast(_AdapterFactory, adapter_class_obj)
        adapter = adapter_class(
            config=config,
            transport=cast(HttpTransport, cast(object, transport)),
        )

        dataset = adapter.get_dataset("expenditure_budget")
        with pytest.raises(AuthError) as exc_info:
            _ = adapter.query_records(dataset, Query())

        assert exc_info.value.provider_code == "ERROR-290"

    def test_query_records_fiacrv_dataset(self) -> None:
        transport = _FixtureTransport(["success_fiacrv.json"])
        config = KPubDataConfig(provider_keys={"lofin": "test-key"})
        adapter_module = import_module("kpubdata.providers.lofin.adapter")
        adapter_class_obj = cast(object, adapter_module.LofinAdapter)
        if not isinstance(adapter_class_obj, type):
            raise AssertionError("LofinAdapter is not a class")
        adapter_class = cast(_AdapterFactory, adapter_class_obj)
        adapter = adapter_class(
            config=config,
            transport=cast(HttpTransport, cast(object, transport)),
        )

        dataset = adapter.get_dataset("revenue_by_source")
        result = adapter.query_records(dataset, Query())

        assert result.total_count == 2
        assert len(result.items) == 2
        assert result.items[0]["armk_nm"] == "총괄"
        assert result.items[1]["armk_nm"] == "지방세수입"

        request_url = cast(str, transport.calls[0]["url"])
        assert "FIACRV" in request_url
