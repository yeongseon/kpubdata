"""AirKorea Provider 계약 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.transport.http import HttpTransport
from tests.contract.provider_adapter import ProviderAdapterContract


def _fixture_path(name: str) -> Path:
    """내부 헬퍼로서 fixture path 처리를 담당한다."""
    return Path(__file__).resolve().parents[1] / "fixtures" / "airkorea" / name


def _load_fixture_bytes(name: str) -> bytes:
    """내부 헬퍼로서 load fixture bytes 처리를 담당한다."""
    return _fixture_path(name).read_bytes()


class _FakeResponse:
    """_FakeResponse 관련 역할을 캡슐화하는 클래스."""

    def __init__(self, data: bytes, content_type: str = "application/json") -> None:
        """인스턴스가 사용할 내부 상태를 초기화한다."""
        self.headers: dict[str, str] = {"content-type": content_type}
        self.content: bytes = data


class _FakeHttpTransport:
    """_FakeHttpTransport 관련 역할을 캡슐화하는 클래스."""

    def __init__(self, responses: list[_FakeResponse]) -> None:
        """인스턴스가 사용할 내부 상태를 초기화한다."""
        self._responses = responses
        self._call_count = 0

    def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        content: bytes | None = None,
        json_body: object = None,
        dataset_id: str | None = None,
        provider: str | None = None,
        sensitive_values: tuple[str, ...] = (),
    ) -> _FakeResponse:
        """가짜 HTTP 요청을 처리하고 응답을 반환한다."""
        if self._call_count >= len(self._responses):
            raise RuntimeError("Unexpected request: no more responses")
        response = self._responses[self._call_count]
        self._call_count += 1
        return response


def _create_adapter(responses: list[_FakeResponse]) -> ProviderAdapter:
    """테스트용 AirKorea 어댑터 인스턴스를 생성한다."""
    from kpubdata.providers.airkorea.adapter import AirKoreaAdapter

    transport = _FakeHttpTransport(responses)
    config = KPubDataConfig()
    return AirKoreaAdapter(config=config, transport=transport)


def test_adapter_implements_protocol() -> None:
    """adapter implements protocol 시나리오를 검증한다."""
    from kpubdata.providers.airkorea.adapter import AirKoreaAdapter

    assert issubclass(AirKoreaAdapter, ProviderAdapter)


def test_list_datasets_returns_valid_refs() -> None:
    """list datasets returns valid refs 시나리오를 검증한다."""
    fixture = _load_fixture_bytes("realtime_air_quality.json")
    responses = [_FakeResponse(fixture)]
    adapter = _create_adapter(responses)

    datasets = adapter.list_datasets()

    assert len(datasets) > 0
    for dataset in datasets:
        assert isinstance(dataset, DatasetRef)
        assert dataset.provider == "airkorea"
        assert dataset.id.startswith("airkorea.")
        assert dataset.dataset_key


def test_get_dataset_returns_valid_ref() -> None:
    """get dataset returns valid ref 시나리오를 검증한다."""
    fixture = _load_fixture_bytes("realtime_air_quality.json")
    responses = [_FakeResponse(fixture)]
    adapter = _create_adapter(responses)

    dataset = adapter.get_dataset("realtime_air_quality")

    assert isinstance(dataset, DatasetRef)
    assert dataset.provider == "airkorea"
    assert dataset.id == "airkorea.realtime_air_quality"
    assert dataset.dataset_key == "realtime_air_quality"


def test_query_records_returns_valid_batch() -> None:
    """query records returns valid batch 시나리오를 검증한다."""
    fixture = _load_fixture_bytes("realtime_air_quality.json")
    responses = [_FakeResponse(fixture)]
    adapter = _create_adapter(responses)

    dataset = adapter.get_dataset("realtime_air_quality")
    query = Query(page=1, page_size=10)
    batch = adapter.query_records(dataset, query)

    assert batch.dataset == dataset
    assert batch.total_count is not None
    assert batch.total_count > 0
    assert len(batch.items) > 0
    assert batch.raw is not None
    assert all(isinstance(item, dict) for item in batch.items)


def test_query_records_pagination_works() -> None:
    """query records pagination works 시나리오를 검증한다."""
    fixture = _load_fixture_bytes("realtime_air_quality.json")
    responses = [_FakeResponse(fixture)]
    adapter = _create_adapter(responses)

    dataset = adapter.get_dataset("realtime_air_quality")
    query = Query(page=1, page_size=2)
    batch = adapter.query_records(dataset, query)

    assert batch.total_count == 5
    assert batch.next_page == 2


def test_call_raw_returns_response() -> None:
    """call raw returns response 시나리오를 검증한다."""
    fixture = _load_fixture_bytes("realtime_air_quality.json")
    responses = [_FakeResponse(fixture)]
    adapter = _create_adapter(responses)

    dataset = adapter.get_dataset("realtime_air_quality")
    result = adapter.call_raw(dataset, "", {})

    assert isinstance(result, dict)
    assert "CtprvnRltmMesureDnsty" in result


def test_get_schema_returns_descriptor() -> None:
    """get schema returns descriptor 시나리오를 검증한다."""
    fixture = _load_fixture_bytes("realtime_air_quality.json")
    responses = [_FakeResponse(fixture)]
    adapter = _create_adapter(responses)

    dataset = adapter.get_dataset("realtime_air_quality")
    schema = adapter.get_schema(dataset)

    assert schema is not None
    assert hasattr(schema, "fields")


def test_search_datasets_filters_correctly() -> None:
    """search datasets filters correctly 시나리오를 검증한다."""
    fixture = _load_fixture_bytes("realtime_air_quality.json")
    responses = [_FakeResponse(fixture)]
    adapter = _create_adapter(responses)

    results = adapter.search_datasets("대기질")
    assert len(results) > 0

    exact_results = adapter.search_datasets("realtime_air_quality")
    assert len(exact_results) == 1
    assert exact_results[0].dataset_key == "realtime_air_quality"


def test_provider_contract_compliance() -> None:
    """provider contract compliance 시나리오를 검증한다."""
    from kpubdata.providers.airkorea.adapter import AirKoreaAdapter

    assert hasattr(AirKoreaAdapter, "requires_api_key")
    assert AirKoreaAdapter.requires_api_key is True

    contract = ProviderAdapterContract(AirKoreaAdapter)
    assert contract.test_required_methods()
    assert contract.test_required_attributes()