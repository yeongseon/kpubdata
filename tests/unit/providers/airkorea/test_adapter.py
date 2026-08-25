"""AirKorea 어댑터 단위 테스트."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import Query
from kpubdata.exceptions import AuthError, InvalidRequestError, ProviderResponseError
from kpubdata.providers.airkorea.adapter import AirKoreaAdapter
from kpubdata.transport.http import HttpTransport


def _fixture_path(name: str) -> Path:
    """내부 헬퍼로서 fixture path 처리를 담당한다."""
    return Path(__file__).resolve().parents[4] / "fixtures" / "airkorea" / name


def _load_fixture(name: str) -> dict[str, object]:
    """내부 헬퍼로서 load fixture 처리를 담당한다."""
    return cast(dict[str, object], json.loads(_fixture_path(name).read_text(encoding="utf-8")))


class FakeResponse:
    """FakeResponse 관련 역할을 캡슐화하는 클래스."""

    def __init__(self, payload: dict[str, object]) -> None:
        """인스턴스가 사용할 내부 상태를 초기화한다."""
        self.headers: dict[str, str] = {"content-type": "application/json"}
        self.text: str = json.dumps(payload, ensure_ascii=False)
        self.content: bytes = self.text.encode("utf-8")


class FakeTransport:
    """FakeTransport 관련 역할을 캡슐화하는 클래스."""

    def __init__(self, responses: list[FakeResponse]) -> None:
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
    ) -> FakeResponse:
        """가짜 HTTP 요청을 처리하고 응답을 반환한다."""
        if self._call_count >= len(self._responses):
            raise RuntimeError("Unexpected request: no more responses")
        response = self._responses[self._call_count]
        self._call_count += 1
        return response


def _create_adapter(responses: list[FakeResponse] | None = None) -> AirKoreaAdapter:
    """테스트용 AirKorea 어댑터 인스턴스를 생성한다."""
    transport = FakeTransport(responses) if responses else None
    config = KPubDataConfig()
    return AirKoreaAdapter(config=config, transport=transport)


def test_list_datasets() -> None:
    """list datasets 시나리오를 검증한다."""
    adapter = _create_adapter()
    datasets = adapter.list_datasets()

    assert len(datasets) == 3
    assert all(ds.provider == "airkorea" for ds in datasets)
    dataset_ids = [ds.id for ds in datasets]
    assert "airkorea.realtime_air_quality" in dataset_ids
    assert "airkorea.air_quality_forecast" in dataset_ids
    assert "airkorea.cai_index" in dataset_ids


def test_get_dataset() -> None:
    """get dataset 시나리오를 검증한다."""
    adapter = _create_adapter()

    dataset = adapter.get_dataset("realtime_air_quality")
    assert dataset.id == "airkorea.realtime_air_quality"
    assert dataset.provider == "airkorea"
    assert "실시간 측정소별 대기질 정보" in dataset.name


def test_get_dataset_not_found() -> None:
    """get dataset not found 시나리오를 검증한다."""
    adapter = _create_adapter()

    with pytest.raises(Exception) as exc_info:
        adapter.get_dataset("nonexistent_dataset")

    assert "airkorea.nonexistent_dataset" in str(exc_info.value)


def test_query_records_success() -> None:
    """query records success 시나리오를 검증한다."""
    fixture = _load_fixture("realtime_air_quality.json")
    transport = FakeTransport([FakeResponse(fixture)])
    adapter = AirKoreaAdapter(config=KPubDataConfig(), transport=transport)

    dataset = adapter.get_dataset("realtime_air_quality")
    query = Query(page=1, page_size=10)
    batch = adapter.query_records(dataset, query)

    assert len(batch.items) == 5
    assert batch.total_count == 5
    assert batch.next_page is None

    first_item = batch.items[0]
    assert "dataTime" in first_item
    assert "pm10Value" in first_item
    assert "pm25Value" in first_item


def test_query_records_pagination() -> None:
    """query records pagination 시나리오를 검증한다."""
    fixture = _load_fixture("realtime_air_quality.json")
    transport = FakeTransport([FakeResponse(fixture)])
    adapter = AirKoreaAdapter(config=KPubDataConfig(), transport=transport)

    dataset = adapter.get_dataset("realtime_air_quality")
    query = Query(page=1, page_size=2)
    batch = adapter.query_records(dataset, query)

    assert len(batch.items) == 2
    assert batch.total_count == 5
    assert batch.next_page == 2


def test_call_raw_success() -> None:
    """call raw success 시나리오를 검증한다."""
    fixture = _load_fixture("realtime_air_quality.json")
    transport = FakeTransport([FakeResponse(fixture)])
    adapter = AirKoreaAdapter(config=KPubDataConfig(), transport=transport)

    dataset = adapter.get_dataset("realtime_air_quality")
    params = {"page_no": 1, "page_size": 10}
    result = adapter.call_raw(dataset, "", params)

    assert "CtprvnRltmMesureDnsty" in result


def test_pagination_validation_invalid_page() -> None:
    """pagination validation invalid page 시나리오를 검증한다."""
    adapter = _create_adapter()
    dataset = adapter.get_dataset("realtime_air_quality")
    query = Query(page=0, page_size=10)

    with pytest.raises(InvalidRequestError) as exc_info:
        adapter.query_records(dataset, query)

    assert "page_no must be >= 1" in str(exc_info.value)


def test_pagination_validation_invalid_size() -> None:
    """pagination validation invalid size 시나리오를 검증한다."""
    adapter = _create_adapter()
    dataset = adapter.get_dataset("realtime_air_quality")
    query = Query(page=1, page_size=0)

    with pytest.raises(InvalidRequestError) as exc_info:
        adapter.query_records(dataset, query)

    assert "page_size must be >= 1" in str(exc_info.value)


def test_pagination_validation_too_large_size() -> None:
    """pagination validation too large size 시나리오를 검증한다."""
    adapter = _create_adapter()
    dataset = adapter.get_dataset("realtime_air_quality")
    query = Query(page=1, page_size=1001)

    with pytest.raises(InvalidRequestError) as exc_info:
        adapter.query_records(dataset, query)

    assert "page_size must be <= 1000" in str(exc_info.value)


def test_search_datasets() -> None:
    """search datasets 시나리오를 검증한다."""
    adapter = _create_adapter()

    results = adapter.search_datasets("대기질")
    assert len(results) > 0
    assert all("대기질" in ds.name or "대기질" in ds.description for ds in results)

    results = adapter.search_datasets("airkorea")
    assert len(results) > 0

    empty_results = adapter.search_datasets("nonexistent")
    assert len(empty_results) == 0


def test_get_schema() -> None:
    """get schema 시나리오를 검증한다."""
    adapter = _create_adapter()
    dataset = adapter.get_dataset("realtime_air_quality")

    schema = adapter.get_schema(dataset)
    assert schema is not None


def test_envelope_validation_missing_service_key() -> None:
    """envelope validation missing service key 시나리오를 검증한다."""
    from kpubdata.providers.airkorea.envelope import validate_envelope

    invalid_payload = {
        "other_key": {
            "total_count": 1,
            "row": [{"data": "test"}]
        }
    }

    with pytest.raises(Exception) as exc_info:
        validate_envelope(invalid_payload, "CtprvnRltmMesureDnsty", "airkorea.realtime_air_quality")

    assert "Service data not found" in str(exc_info.value)


def test_envelope_validation_invalid_row_type() -> None:
    """envelope validation invalid row type 시나리오를 검증한다."""
    from kpubdata.providers.airkorea.envelope import validate_envelope

    invalid_payload = {
        "CtprvnRltmMesureDnsty": {
            "total_count": 1,
            "row": "not a list"
        }
    }

    with pytest.raises(Exception) as exc_info:
        validate_envelope(invalid_payload, "CtprvnRltmMesureDnsty", "airkorea.realtime_air_quality")

    assert "row must be a list" in str(exc_info.value)