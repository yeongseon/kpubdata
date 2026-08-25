"""Korean Provider 단위 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.exceptions import DatasetNotFoundError, InvalidRequestError, ParseError
from kpubdata.transport.http import HttpTransport


def _fixture_path(name: str) -> Path:
    """내부 헬퍼로서 fixture path 처리를 담당한다."""
    return Path(__file__).resolve().parents[2] / "fixtures" / "korean" / name


def _load_fixture(name: str) -> dict[str, object]:
    """내부 헬퍼로서 load fixture 처리를 담당한다."""
    from kpubdata.transport.decode import decode_json

    return decode_json(_fixture_path(name).read_bytes())


def _import_adapter() -> type[ProviderAdapter]:
    """어댑터 클래스를 동적으로 임포트한다."""
    from kpubdata.providers.korean.adapter import KoreanAdapter

    return KoreanAdapter


def test_adapter_implements_protocol() -> None:
    """adapter implements protocol 시나리오를 검증한다."""
    KoreanAdapter = _import_adapter()
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
    KoreanAdapter = _import_adapter()

    adapter = KoreanAdapter(config=KPubDataConfig(api_key="test_key"))
    datasets = adapter.list_datasets()

    assert len(datasets) == 3
    for dataset in datasets:
        assert isinstance(dataset, DatasetRef)
        assert dataset.provider == "korean"
        assert dataset.id.startswith("korean.")
        assert dataset.dataset_key


def test_get_dataset_returns_valid_ref() -> None:
    """get dataset returns valid ref 시나리오를 검증한다."""
    KoreanAdapter = _import_adapter()

    adapter = KoreanAdapter(config=KPubDataConfig(api_key="test_key"))
    dataset = adapter.get_dataset("dictionary_search")

    assert isinstance(dataset, DatasetRef)
    assert dataset.provider == "korean"
    assert dataset.id == "korean.dictionary_search"
    assert dataset.dataset_key == "dictionary_search"
    assert "사전" in dataset.name


def test_get_dataset_invalid_key_raises_error() -> None:
    """get dataset invalid key raises error 시나리오를 검증한다."""
    KoreanAdapter = _import_adapter()

    adapter = KoreanAdapter(config=KPubDataConfig(api_key="test_key"))

    with pytest.raises(DatasetNotFoundError) as exc_info:
        adapter.get_dataset("invalid_dataset")

    assert exc_info.value.dataset_id == "korean.invalid_dataset"
    assert exc_info.value.provider_id == "korean"


def test_provider_id_and_name() -> None:
    """provider id and name 시나리오를 검증한다."""
    KoreanAdapter = _import_adapter()

    adapter = KoreanAdapter(config=KPubDataConfig(api_key="test_key"))

    assert adapter.provider_id == "korean"
    assert "국립국어원" in adapter.name


def test_search_datasets_filters_correctly() -> None:
    """search datasets filters correctly 시나리오를 검증한다."""
    KoreanAdapter = _import_adapter()

    adapter = KoreanAdapter(config=KPubDataConfig(api_key="test_key"))

    results = adapter.search_datasets("사전")
    assert len(results) > 0
    assert all("사전" in result.name for result in results)

    exact_results = adapter.search_datasets("dictionary_search")
    assert len(exact_results) == 1
    assert exact_results[0].dataset_key == "dictionary_search"


def test_search_datasets_case_insensitive() -> None:
    """search datasets case insensitive 시나리오를 검증한다."""
    KoreanAdapter = _import_adapter()

    adapter = KoreanAdapter(config=KPubDataConfig(api_key="test_key"))

    lower_results = adapter.search_datasets("spell")
    upper_results = adapter.search_datasets("SPELL")

    assert len(lower_results) == len(upper_results)


def test_requires_api_key_attribute() -> None:
    """requires api key attribute 시나리오를 검증한다."""
    KoreanAdapter = _import_adapter()

    assert hasattr(KoreanAdapter, "requires_api_key")
    assert KoreanAdapter.requires_api_key is True


def test_custom_catalogue_replaces_default() -> None:
    """custom catalogue replaces default 시나리오를 검증한다."""
    KoreanAdapter = _import_adapter()

    custom_dataset = DatasetRef(
        id="korean.custom",
        name="Custom Dataset",
        description="Test",
        provider="korean",
        dataset_key="custom",
        representation="api_json",
    )

    adapter = KoreanAdapter(config=KPubDataConfig(api_key="test_key"), catalogue=(custom_dataset,))

    datasets = adapter.list_datasets()
    assert len(datasets) == 1
    assert datasets[0].dataset_key == "custom"


def test_validate_query_invalid_page_raises_error() -> None:
    """validate query invalid page raises error 시나리오를 검증한다."""
    KoreanAdapter = _import_adapter()

    adapter = KoreanAdapter(config=KPubDataConfig(api_key="test_key"))

    with pytest.raises(InvalidRequestError):
        query = Query(page=0, page_size=10)
        adapter._validate_query(query)

    with pytest.raises(InvalidRequestError):
        query = Query(page=-1, page_size=10)
        adapter._validate_query(query)


def test_validate_query_invalid_page_size_raises_error() -> None:
    """validate query invalid page size raises error 시나리오를 검증한다."""
    KoreanAdapter = _import_adapter()

    adapter = KoreanAdapter(config=KPubDataConfig(api_key="test_key"))

    with pytest.raises(InvalidRequestError):
        query = Query(page=1, page_size=0)
        adapter._validate_query(query)

    with pytest.raises(InvalidRequestError):
        query = Query(page=1, page_size=-5)
        adapter._validate_query(query)


def test_get_base_url_from_dataset_metadata() -> None:
    """get base url from dataset metadata 시나리오를 검증한다."""
    KoreanAdapter = _import_adapter()

    adapter = KoreanAdapter(config=KPubDataConfig(api_key="test_key"))
    dataset = adapter.get_dataset("dictionary_search")

    base_url = adapter._get_base_url(dataset)

    assert "korean.go.kr" in base_url or "pusan.ac.kr" in base_url


def test_get_base_url_no_metadata_raises_error() -> None:
    """get base url no metadata raises error 시나리오를 검증한다."""
    KoreanAdapter = _import_adapter()

    adapter = KoreanAdapter(config=KPubDataConfig(api_key="test_key"))

    dataset = DatasetRef(
        id="korean.no_metadata",
        name="No Metadata",
        description="Test",
        provider="korean",
        dataset_key="no_metadata",
        raw_metadata={},
    )

    with pytest.raises(ValueError) as exc_info:
        adapter._get_base_url(dataset)

    assert "base_url" in str(exc_info.value)