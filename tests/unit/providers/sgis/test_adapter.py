from __future__ import annotations

import json
from importlib import import_module
from pathlib import Path
from typing import Protocol, cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.exceptions import AuthError, DatasetNotFoundError, InvalidRequestError
from kpubdata.transport.http import HttpTransport


class _SgisAdapterFactory(Protocol):
    def __call__(
        self,
        *,
        config: KPubDataConfig | None = None,
        transport: HttpTransport | None = None,
        auth_client: object = None,
    ) -> ProviderAdapter: ...


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parents[3] / "fixtures" / "sgis" / name


def _load_fixture(name: str) -> dict[str, object]:
    payload = cast(object, json.loads(_fixture_path(name).read_text(encoding="utf-8")))
    if isinstance(payload, dict):
        return cast(dict[str, object], payload)
    raise ValueError(f"Fixture must be object: {name}")


class _FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.headers: dict[str, str] = {"content-type": "application/json"}
        self.text: str = json.dumps(payload, ensure_ascii=False)
        self.content: bytes = self.text.encode("utf-8")


class _FakeTransport:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self._responses: list[_FakeResponse] = list(responses)
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> _FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        if not self._responses:
            raise AssertionError("No fixture responses remaining")
        return self._responses.pop(0)


class _FakeAuthClient:
    def __init__(self, tokens: list[str]) -> None:
        self._tokens: list[str] = list(tokens)
        self.invalidate_count: int = 0
        self.force_refresh_count: int = 0

    def get_access_token(self, *, force_refresh: bool = False) -> str:
        if force_refresh:
            self.force_refresh_count += 1
        if not self._tokens:
            raise AssertionError("No tokens remaining")
        return self._tokens.pop(0)

    def invalidate(self) -> None:
        self.invalidate_count += 1


def _build_adapter(
    responses: list[_FakeResponse],
    *,
    auth_client: _FakeAuthClient,
) -> tuple[ProviderAdapter, _FakeTransport]:
    transport = _FakeTransport(responses)
    adapter_module = import_module("kpubdata.providers.sgis.adapter")
    adapter_class_obj = cast(object, adapter_module.SgisAdapter)
    if not isinstance(adapter_class_obj, type):
        raise AssertionError("SgisAdapter is not a class")
    adapter_class = cast(_SgisAdapterFactory, adapter_class_obj)
    adapter = adapter_class(
        config=KPubDataConfig(provider_keys={"sgis": "consumer-key:consumer-secret"}),
        transport=cast(HttpTransport, cast(object, transport)),
        auth_client=auth_client,
    )
    return adapter, transport


def test_query_records_sido_parses_features() -> None:
    auth_client = _FakeAuthClient(["token-1"])
    adapter, transport = _build_adapter(
        [_FakeResponse(_load_fixture("sido_boundary.geojson"))],
        auth_client=auth_client,
    )
    dataset = adapter.get_dataset("boundary.sido")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert batch.total_count == 2
    assert batch.items[0]["adm_cd"] == "11"
    assert isinstance(batch.items[0]["geometry"], dict)
    request_params = cast(dict[str, str], transport.calls[0]["params"])
    assert request_params["year"] == "2023"
    assert request_params["low_search"] == "1"


def test_query_records_sigungu_applies_filter_overrides() -> None:
    auth_client = _FakeAuthClient(["token-1"])
    adapter, transport = _build_adapter(
        [_FakeResponse(_load_fixture("sigungu_boundary.geojson"))],
        auth_client=auth_client,
    )
    dataset = adapter.get_dataset("boundary.sigungu")

    batch = adapter.query_records(dataset, Query(filters={"year": "2021", "adm_cd": "11"}))

    assert len(batch.items) == 2
    request_params = cast(dict[str, str], transport.calls[0]["params"])
    assert request_params["year"] == "2021"
    assert request_params["adm_cd"] == "11"
    assert request_params["low_search"] == "2"


def test_query_records_refreshes_token_on_auth_error() -> None:
    auth_client = _FakeAuthClient(["expired-token", "fresh-token"])
    adapter, transport = _build_adapter(
        [
            _FakeResponse(_load_fixture("error_invalid_token.json")),
            _FakeResponse(_load_fixture("sido_boundary.geojson")),
        ],
        auth_client=auth_client,
    )
    dataset = adapter.get_dataset("boundary.sido")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert auth_client.invalidate_count == 1
    assert auth_client.force_refresh_count == 1
    first_params = cast(dict[str, str], transport.calls[0]["params"])
    second_params = cast(dict[str, str], transport.calls[1]["params"])
    assert first_params["accessToken"] == "expired-token"
    assert second_params["accessToken"] == "fresh-token"


def test_query_records_raises_auth_error_when_refresh_also_fails() -> None:
    auth_client = _FakeAuthClient(["expired-token", "fresh-token"])
    adapter, _ = _build_adapter(
        [
            _FakeResponse(_load_fixture("error_invalid_token.json")),
            _FakeResponse(_load_fixture("error_invalid_token.json")),
        ],
        auth_client=auth_client,
    )
    dataset = adapter.get_dataset("boundary.sido")

    with pytest.raises(AuthError):
        _ = adapter.query_records(dataset, Query())


def test_call_raw_list_uses_dataset_endpoint() -> None:
    auth_client = _FakeAuthClient(["token-1"])
    payload = _load_fixture("sido_boundary.geojson")
    adapter, _ = _build_adapter([_FakeResponse(payload)], auth_client=auth_client)
    dataset = adapter.get_dataset("boundary.sido")

    raw = adapter.call_raw(dataset, "list", {"year": "2022"})

    assert raw == payload


def test_call_raw_rejects_full_url_operation() -> None:
    auth_client = _FakeAuthClient(["token-1"])
    adapter, _ = _build_adapter(
        [_FakeResponse(_load_fixture("sido_boundary.geojson"))], auth_client=auth_client
    )
    dataset = adapter.get_dataset("boundary.sido")

    with pytest.raises(InvalidRequestError):
        _ = adapter.call_raw(
            dataset, "https://sgisapi.kostat.go.kr/OpenAPI3/boundary/hadmarea.geojson", {}
        )


def test_get_dataset_invalid_key_raises() -> None:
    auth_client = _FakeAuthClient(["token-1"])
    adapter, _ = _build_adapter(
        [_FakeResponse(_load_fixture("sido_boundary.geojson"))], auth_client=auth_client
    )

    with pytest.raises(DatasetNotFoundError):
        _ = adapter.get_dataset("missing.dataset")


def test_dataset_ref_ids_include_required_catalogue_entries() -> None:
    auth_client = _FakeAuthClient(["token-1"])
    adapter, _ = _build_adapter(
        [_FakeResponse(_load_fixture("sido_boundary.geojson"))], auth_client=auth_client
    )

    dataset_ids = {dataset.id for dataset in adapter.list_datasets()}
    assert "sgis.boundary.sido" in dataset_ids
    assert "sgis.boundary.sigungu" in dataset_ids
    assert "sgis.boundary.emd" in dataset_ids


def test_schema_returns_descriptor_for_boundary_dataset() -> None:
    auth_client = _FakeAuthClient(["token-1"])
    adapter, _ = _build_adapter(
        [_FakeResponse(_load_fixture("sido_boundary.geojson"))], auth_client=auth_client
    )
    dataset: DatasetRef = adapter.get_dataset("boundary.sido")

    schema = adapter.get_schema(dataset)

    assert schema is not None
    assert len(schema.fields) >= 5
