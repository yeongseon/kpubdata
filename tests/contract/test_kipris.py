"""KIPRIS Provider 계약 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.providers.kipris.envelope import extract_items, parse_xml_response, validate_envelope


def _fixture_path(name: str) -> Path:
    """내부 헬퍼로서 fixture path 처리를 담당한다."""
    return Path(__file__).resolve().parents[1] / "fixtures" / "kipris" / name


def _load_fixture(name: str) -> dict[str, object]:
    """내부 헬퍼로서 load fixture 처리를 담당한다."""
    from kpubdata.transport.decode import decode_json

    return decode_json(_fixture_path(name).read_bytes())


class _FakeResponse:
    """_FakeResponse 관련 역할을 캡슐화하는 클래스."""

    def __init__(self, data: dict[str, object], content_type: str = "application/xml") -> None:
        """인스턴스가 사용할 내부 상태를 초기화한다."""
        self.headers: dict[str, str] = {"content-type": content_type}
        self.data = data

    @property
    def content(self) -> bytes:
        """content를 반환한다."""
        import json

        return json.dumps(self.data).encode("utf-8")


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
    """테스트용 KIPRIS 어댑터 인스턴스를 생성한다."""
    from kpubdata.providers.kipris.adapter import KiprisAdapter

    transport = _FakeHttpTransport(responses)
    config = KPubDataConfig()
    return KiprisAdapter(config=config, transport=transport)


def test_adapter_implements_protocol() -> None:
    """adapter implements protocol 시나리오를 검증한다."""
    from kpubdata.providers.kipris.adapter import KiprisAdapter

    from kpubdata.core.protocol import ProviderAdapter

    assert isinstance(KiprisAdapter, type)
    assert hasattr(KiprisAdapter, "requires_api_key")
    assert hasattr(KiprisAdapter, "name")
    assert hasattr(KiprisAdapter, "list_datasets")
    assert hasattr(KiprisAdapter, "search_datasets")
    assert hasattr(KiprisAdapter, "get_dataset")
    assert hasattr(KiprisAdapter, "query_records")
    assert hasattr(KiprisAdapter, "get_schema")
    assert hasattr(KiprisAdapter, "call_raw")


def test_list_datasets_returns_valid_refs() -> None:
    """list datasets returns valid refs 시나리오를 검증한다."""
    fixture = _load_fixture("patent_search.json")
    responses = [_FakeResponse(fixture)]
    adapter = _create_adapter(responses)

    datasets = adapter.list_datasets()

    assert len(datasets) == 3
    for dataset in datasets:
        assert isinstance(dataset, DatasetRef)
        assert dataset.provider == "kipris"
        assert dataset.id.startswith("kipris.")
        assert dataset.dataset_key


def test_get_dataset_returns_valid_ref() -> None:
    """get dataset returns valid ref 시나리오를 검증한다."""
    fixture = _load_fixture("patent_search.json")
    responses = [_FakeResponse(fixture)]
    adapter = _create_adapter(responses)

    dataset = adapter.get_dataset("patent_search")

    assert isinstance(dataset, DatasetRef)
    assert dataset.provider == "kipris"
    assert dataset.id == "kipris.patent_search"
    assert dataset.dataset_key == "patent_search"
    assert "특허" in dataset.name


def test_envelope_parsing() -> None:
    """envelope parsing 시나리오를 검증한다."""
    fixture = _load_fixture("patent_search.json")

    items = extract_items(fixture)

    assert len(items) >= 3
    assert all(isinstance(item, dict) for item in items)

    first_item = items[0] if isinstance(items, list) and items else items
    if isinstance(first_item, dict):
        assert first_item.get("applicationNumber") == "1020210012345"
        assert first_item.get("inventionTitle") == "인공지능 기반 데이터 분석 시스템 및 방법"


def test_envelope_validation_success() -> None:
    """envelope validation success 시나리오를 검증한다."""
    fixture = _load_fixture("patent_search.json")

    envelope = validate_envelope(fixture)

    assert "items" in envelope
    assert envelope["num_of_rows"] == 3
    assert envelope["page_no"] == 1
    assert envelope["total_count"] == 3
    items = envelope["items"]
    if isinstance(items, dict) and "item" in items:
        assert len(items["item"]) == 3
    elif isinstance(items, list):
        assert len(items) >= 3


def test_envelope_validation_error() -> None:
    """envelope validation error 시나리오를 검증한다."""
    error_response = {
        "response": {
            "header": {"resultCode": "99", "resultMsg": "SERVICE ERROR"},
            "body": {},
        }
    }

    with pytest.raises(ValueError) as exc_info:
        validate_envelope(error_response)

    assert "99" in str(exc_info.value)
    assert "SERVICE ERROR" in str(exc_info.value)


def test_empty_response_handling() -> None:
    """empty response handling 시나리오를 검증한다."""
    with pytest.raises(ValueError):
        validate_envelope({})


def test_empty_body_handling() -> None:
    """empty body handling 시나리오를 검증한다."""
    response_with_empty_body = {"response": {"header": {"resultCode": "00", "resultMsg": "OK"}, "body": {}}}

    with pytest.raises(ValueError):
        validate_envelope(response_with_empty_body)


def test_single_item_handling() -> None:
    """single item handling 시나리오를 검증한다."""
    single_item_response = {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "OK"},
            "body": {
                "items": {
                    "item": {
                        "applicationNumber": "1020210000001",
                        "inventionTitle": "Single Test Patent",
                    }
                },
                "numOfRows": 1,
                "pageNo": 1,
                "totalCount": 1,
            },
        }
    }

    items = extract_items(single_item_response)

    assert len(items) == 1
    assert isinstance(items[0], dict)
    assert items[0].get("applicationNumber") == "1020210000001"


def test_provider_contract_compliance() -> None:
    """provider contract compliance 시나리오를 검증한다."""
    from kpubdata.providers.kipris.adapter import KiprisAdapter

    assert hasattr(KiprisAdapter, "requires_api_key")
    assert KiprisAdapter.requires_api_key is True

    assert hasattr(KiprisAdapter, "provider_id")
    assert hasattr(KiprisAdapter, "name")


def test_schema_generation_from_first_item() -> None:
    """schema generation from first item 시나리오를 검증한다."""
    fixture = _load_fixture("patent_search.json")
    responses = [_FakeResponse(fixture)]
    adapter = _create_adapter(responses)

    dataset = adapter.get_dataset("patent_search")
    schema = adapter.get_schema(dataset)

    assert schema is not None
    assert hasattr(schema, "fields")


def test_pagination_info_in_envelope() -> None:
    """pagination info in envelope 시나리오를 검증한다."""
    fixture = _load_fixture("patent_search.json")
    responses = [_FakeResponse(fixture)]
    adapter = _create_adapter(responses)

    dataset = adapter.get_dataset("patent_search")
    query = Query(page=1, page_size=3)
    batch = adapter.query_records(dataset, query)

    assert batch.total_count == 3
    assert batch.next_page is None
    assert len(batch.items) == 3