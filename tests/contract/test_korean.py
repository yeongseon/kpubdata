"""Korean Provider 계약 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.providers.korean.envelope import extract_items, validate_envelope


def _fixture_path(name: str) -> Path:
    """내부 헬퍼로서 fixture path 처리를 담당한다."""
    return Path(__file__).resolve().parents[1] / "fixtures" / "korean" / name


def _load_fixture(name: str) -> dict[str, object]:
    """내부 헬퍼로서 load fixture 처리를 담당한다."""
    from kpubdata.transport.decode import decode_json

    return decode_json(_fixture_path(name).read_bytes())


class _FakeResponse:
    """_FakeResponse 관련 역할을 캡슐화하는 클래스."""

    def __init__(self, data: dict[str, object], content_type: str = "application/json") -> None:
        """인스턴스가 사용할 내부 상태를 초기화한다."""
        self.headers: dict[str, str] = {"content-type": content_type}
        self._data = data

    def json(self) -> dict[str, object]:
        """json을 반환한다."""
        return self._data

    @property
    def content(self) -> bytes:
        """content를 반환한다."""
        import json

        return json.dumps(self._data).encode("utf-8")


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


def _create_adapter(responses: list[_FakeResponse]) -> object:
    """테스트용 Korean 어댑터 인스턴스를 생성한다."""
    from kpubdata.providers.korean.adapter import KoreanAdapter

    transport = _FakeHttpTransport(responses)
    config = KPubDataConfig()
    return KoreanAdapter(config=config, transport=transport)


def test_adapter_implements_protocol() -> None:
    """adapter implements protocol 시나리오를 검증한다."""
    from kpubdata.providers.korean.adapter import KoreanAdapter

    assert isinstance(KoreanAdapter, type)
    assert hasattr(KoreanAdapter, "requires_api_key")
    assert hasattr(KoreanAdapter, "name")
    assert hasattr(KoreanAdapter, "list_datasets")
    assert hasattr(KoreanAdapter, "search_datasets")
    assert hasattr(KoreanAdapter, "get_dataset")
    assert hasattr(KoreanAdapter, "query_records")
    assert hasattr(KoreanAdapter, "get_schema")
    assert hasattr(KoreanAdapter, "call_raw")


def test_list_datasets_returns_valid_refs() -> None:
    """list datasets returns valid refs 시나리오를 검증한다."""
    fixture = _load_fixture("dictionary_search.json")
    responses = [_FakeResponse(fixture)]
    adapter = _create_adapter(responses)

    datasets = adapter.list_datasets()

    assert len(datasets) == 3
    for dataset in datasets:
        assert isinstance(dataset, DatasetRef)
        assert dataset.provider == "korean"
        assert dataset.id.startswith("korean.")
        assert dataset.dataset_key


def test_get_dataset_returns_valid_ref() -> None:
    """get dataset returns valid ref 시나리오를 검증한다."""
    fixture = _load_fixture("dictionary_search.json")
    responses = [_FakeResponse(fixture)]
    adapter = _create_adapter(responses)

    dataset = adapter.get_dataset("dictionary_search")

    assert isinstance(dataset, DatasetRef)
    assert dataset.provider == "korean"
    assert dataset.id == "korean.dictionary_search"
    assert dataset.dataset_key == "dictionary_search"
    assert "사전" in dataset.name


def test_envelope_parsing() -> None:
    """envelope parsing 시나리오를 검증한다."""
    fixture = _load_fixture("dictionary_search.json")

    items = extract_items(fixture)

    assert len(items) == 3
    assert all(isinstance(item, dict) for item in items)
    assert items[0].get("word") == "한국어"
    assert items[0].get("definition") == "한민족의 언어. 대한민국과 조선민주주의인민공화국의 공용어이다."


def test_envelope_validation_success() -> None:
    """envelope validation success 시나리오를 검증한다."""
    fixture = _load_fixture("dictionary_search.json")

    envelope = validate_envelope(fixture)

    assert "items" in envelope
    assert envelope["total_count"] == 3
    assert len(envelope["items"]) == 3


def test_envelope_validation_error() -> None:
    """envelope validation error 시나리오를 검증한다."""
    error_response = {
        "errorMessage": "API authentication failed",
    }

    with pytest.raises(ValueError) as exc_info:
        validate_envelope(error_response)

    assert "authentication failed" in str(exc_info.value).lower()


def test_empty_response_handling() -> None:
    """empty response handling 시나리오를 검증한다."""
    with pytest.raises(ValueError):
        validate_envelope({})


def test_empty_items_handling() -> None:
    """empty items handling 시나리오를 검증한다."""
    empty_response = {"total": 0, "item": []}

    envelope = validate_envelope(empty_response)

    assert envelope["items"] == []
    assert envelope["total_count"] == 0


def test_single_item_handling() -> None:
    """single item handling 시나리오를 검증한다."""
    single_item_response = {
        "total": 1,
        "item": {
            "word": "단어",
            "definition": "단 하나의 말",
            "partOfSpeech": "명사",
        },
    }

    items = extract_items(single_item_response)

    assert len(items) == 1
    assert items[0]["word"] == "단어"


def test_provider_contract_compliance() -> None:
    """provider contract compliance 시나리오를 검증한다."""
    from kpubdata.providers.korean.adapter import KoreanAdapter

    assert hasattr(KoreanAdapter, "requires_api_key")
    assert KoreanAdapter.requires_api_key is True

    assert hasattr(KoreanAdapter, "provider_id")
    assert hasattr(KoreanAdapter, "name")


def test_schema_generation_from_first_item() -> None:
    """schema generation from first item 시나리오를 검증한다."""
    fixture = _load_fixture("dictionary_search.json")
    responses = [_FakeResponse(fixture)]
    adapter = _create_adapter(responses)

    dataset = adapter.get_dataset("dictionary_search")
    schema = adapter.get_schema(dataset)

    assert schema is not None
    assert hasattr(schema, "fields")


def test_pagination_info_in_envelope() -> None:
    """pagination info in envelope 시나리오를 검증한다."""
    fixture = _load_fixture("dictionary_search.json")
    responses = [_FakeResponse(fixture)]
    adapter = _create_adapter(responses)

    dataset = adapter.get_dataset("dictionary_search")
    query = Query(page=1, page_size=3)
    batch = adapter.query_records(dataset, query)

    assert batch.total_count == 3
    assert batch.next_page is None
    assert len(batch.items) == 3