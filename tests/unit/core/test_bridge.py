"""core/bridge.py 단위 테스트 — composite 병합·라우팅·레지스트리 통합 검증.

FakeInnerAdapter는 카탈로그 기반 내장 어댑터의 프로토콜 표면을 흉내내고,
spec 쪽은 번들 골든 spec + FakeTransport 실행기를 사용해 실제 병합 동작을 검증한다.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

from kpubdata import Client
from kpubdata.config import KPubDataConfig
from kpubdata.core.bridge import CompositeProviderAdapter
from kpubdata.core.executor import SpecDatasetAdapter, SpecExecutor
from kpubdata.core.models import DatasetRef, Query, RecordBatch
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.core.representation import Representation
from kpubdata.core.spec import SpecDefinition, load_spec_file
from kpubdata.exceptions import DatasetNotFoundError
from kpubdata.registry import ProviderRegistry
from kpubdata.transport.http import HttpTransport

SPECS_DIR = Path(__file__).resolve().parents[3] / "src" / "kpubdata" / "specs"


class FakeResponse:
    """httpx.Response의 최소 인터페이스를 흉내낸다."""

    def __init__(self, content: bytes) -> None:
        self.content = content
        self.headers = {"content-type": "application/json"}


class FakeTransport:
    """호출을 기록하고 표준 envelope 응답을 반환한다."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

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
        secret_values: tuple[str, ...] = (),
    ) -> FakeResponse:
        self.calls.append({"url": url, "params": dict(params or {})})
        payload = {
            "response": {
                "header": {"resultCode": "00", "resultMsg": "OK"},
                "body": {
                    "items": {"item": [{"from": "spec"}]},
                    "totalCount": "1",
                },
            }
        }
        return FakeResponse(json.dumps(payload).encode())


class FakeConfig(KPubDataConfig):
    """키 조회를 고정값으로 대체한 설정."""

    def get_provider_key(self, provider: str) -> str | None:
        return f"test-key-{provider}"

    def require_provider_key(self, provider: str) -> str:
        return f"test-key-{provider}"


class FakeInnerAdapter:
    """카탈로그 어댑터 흉내 — spec 키 1개(apt_trade)와 카탈로그 전용 키 2개 제공."""

    def __init__(self) -> None:
        self.query_calls: list[str] = []
        self.raw_calls: list[str] = []

    @property
    def name(self) -> str:
        return "datago"

    requires_api_key = True

    @staticmethod
    def _ref(key: str, name: str) -> DatasetRef:
        from kpubdata.core.capability import Operation

        return DatasetRef(
            id=f"datago.{key}",
            provider="datago",
            dataset_key=key,
            name=name,
            representation=Representation.API_JSON,
            operations=frozenset({Operation.LIST, Operation.RAW}),
        )

    def list_datasets(self) -> list[DatasetRef]:
        return [self._ref("apt_trade", "카탈로그 아파트"), self._ref("air_quality", "대기오염")]

    def search_datasets(self, text: str) -> list[DatasetRef]:
        return [ref for ref in self.list_datasets() if text in ref.name]

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        for ref in self.list_datasets():
            if ref.dataset_key == dataset_key:
                return ref
        raise DatasetNotFoundError(f"unknown: {dataset_key}", provider="datago")

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        self.query_calls.append(dataset.dataset_key)
        return RecordBatch(items=[{"from": "inner"}], dataset=dataset)

    def get_schema(self, dataset: DatasetRef) -> None:
        return None

    def call_raw(self, dataset: DatasetRef, operation: str, params: dict[str, object]) -> object:
        self.raw_calls.append(dataset.dataset_key)
        return {"from": "inner"}


def _golden(key: str) -> SpecDefinition:
    return load_spec_file(SPECS_DIR / "datago" / f"{key}.yaml")


@pytest.fixture()
def transport() -> FakeTransport:
    return FakeTransport()


@pytest.fixture()
def spec_adapter(transport: FakeTransport) -> SpecDatasetAdapter:
    executor = SpecExecutor(transport, FakeConfig())
    return SpecDatasetAdapter("datago", [_golden("apt_trade"), _golden("village_fcst")], executor)


@pytest.fixture()
def inner() -> FakeInnerAdapter:
    return FakeInnerAdapter()


@pytest.fixture()
def composite(
    inner: FakeInnerAdapter, spec_adapter: SpecDatasetAdapter
) -> CompositeProviderAdapter:
    return CompositeProviderAdapter(inner, spec_adapter)


# ----------------------------------------------------------------------
# 병합 규칙
# ----------------------------------------------------------------------


def test_list_datasets_spec_wins_and_appends(
    composite: CompositeProviderAdapter, inner: FakeInnerAdapter
) -> None:
    """겹치는 키는 spec 참조로 교체되고, spec 전용 키는 끝에 추가된다."""
    refs = composite.list_datasets()
    by_key = {ref.dataset_key: ref for ref in refs}

    assert set(by_key) == {"apt_trade", "air_quality", "village_fcst"}
    # apt_trade는 카탈로그에도 있지만 spec이 이긴다(제목으로 구분).
    assert by_key["apt_trade"].name == _golden("apt_trade").title
    # 카탈로그 전용 키는 그대로(동일 내용).
    assert by_key["air_quality"].name == "대기오염"


def test_search_datasets_merges_without_duplicates(composite: CompositeProviderAdapter) -> None:
    """검색 결과 병합에서도 키 중복이 없다(spec 우선)."""
    hits = composite.search_datasets("아파트")
    keys = [ref.dataset_key for ref in hits]
    assert keys.count("apt_trade") == 1
    # spec의 제목 "아파트매매 실거래가"와 카탈로그의 "카탈로그 아파트" 둘 다 매치되어도 1건.
    assert "apt_trade" in keys


def test_provider_name_mismatch_rejected(
    inner: FakeInnerAdapter, spec_adapter: SpecDatasetAdapter
) -> None:
    """서로 다른 Provider 병합은 거부된다."""
    other = SpecDatasetAdapter("seoul", [], SpecExecutor(FakeTransport(), FakeConfig()))
    with pytest.raises(ValueError, match="같은 Provider"):
        CompositeProviderAdapter(inner, other)


# ----------------------------------------------------------------------
# 라우팅
# ----------------------------------------------------------------------


def test_get_dataset_routes_spec_first(composite: CompositeProviderAdapter) -> None:
    """spec 소유 키는 spec 참조를 반환한다."""
    ref = composite.get_dataset("apt_trade")
    assert ref.name == _golden("apt_trade").title
    catalogue_only = composite.get_dataset("air_quality")
    assert catalogue_only.name == "대기오염"
    with pytest.raises(DatasetNotFoundError):
        composite.get_dataset("nope")


def test_query_records_routes_by_owner(
    composite: CompositeProviderAdapter,
    inner: FakeInnerAdapter,
    transport: FakeTransport,
) -> None:
    """spec 소유 질의는 실행기로, 카탈로그 소유 질의는 내장 어댑터로 간다."""
    spec_ref = composite.get_dataset("apt_trade")
    batch = composite.query_records(spec_ref, Query())
    assert batch.items == [{"from": "spec"}]
    assert inner.query_calls == []

    inner_ref = composite.get_dataset("air_quality")
    inner_batch = composite.query_records(inner_ref, Query())
    assert inner_batch.items == [{"from": "inner"}]
    assert inner.query_calls == ["air_quality"]


def test_call_raw_routes_by_owner(
    composite: CompositeProviderAdapter, inner: FakeInnerAdapter
) -> None:
    """raw 비상구도 소유자 규칙을 따른다."""
    spec_ref = composite.get_dataset("village_fcst")
    raw = composite.call_raw(spec_ref, "raw", {})
    assert isinstance(raw, dict) and "response" in raw
    assert inner.raw_calls == []

    inner_raw = composite.call_raw(composite.get_dataset("air_quality"), "raw", {})
    assert inner_raw == {"from": "inner"}


def test_requires_api_key_or_semantics(inner: FakeInnerAdapter) -> None:
    """requires_api_key는 논리합이다."""
    no_key_spec = SpecDatasetAdapter("datago", [], SpecExecutor(FakeTransport(), FakeConfig()))
    inner.requires_api_key = False
    composite = CompositeProviderAdapter(inner, no_key_spec)
    assert composite.requires_api_key is False
    inner.requires_api_key = True
    assert CompositeProviderAdapter(inner, no_key_spec).requires_api_key is True


# ----------------------------------------------------------------------
# 레지스트리 통합
# ----------------------------------------------------------------------


def test_registry_accepts_composite(composite: CompositeProviderAdapter) -> None:
    """composite은 등록 시점 프로토콜·capability 검증을 통과한다."""
    registry = ProviderRegistry()
    registry.register(composite)
    assert "datago" in registry
    adapter = registry.get("datago")
    assert isinstance(adapter, CompositeProviderAdapter)
    assert isinstance(adapter, ProviderAdapter)  # runtime_checkable 프로토콜


def test_client_resolves_spec_dataset_end_to_end() -> None:
    """Client → composite → spec 실행기 경로가 실제 클라이언트에서 동작한다."""
    payload = {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "OK"},
            "body": {"items": {"item": {"category": "T1H"}}, "totalCount": "1"},
        }
    }
    mock_response = httpx.Response(
        status_code=200,
        content=json.dumps(payload).encode(),
        request=httpx.Request("GET", "http://example.com"),
    )
    with patch.object(HttpTransport, "request", return_value=mock_response) as mock_request:
        client = Client(provider_keys={"datago": "test-key"}, cache=False)
        dataset = client.dataset("datago.village_fcst")
        batch = dataset.list()
        assert isinstance(batch, RecordBatch)
        assert batch.items == [{"category": "T1H"}]
        assert mock_request.call_count == 1
        # spec 경로 증명: format_param 값이 spec의 대문자 "JSON"(어댑터는 소문자 "json").
        kwargs = mock_request.call_args.kwargs
        assert kwargs["params"]["dataType"] == "JSON"


def test_client_catalogue_dataset_unaffected() -> None:
    """spec에 없는 카탈로그 데이터셋은 기존 어댑터 경로를 그대로 쓴다."""
    payload = {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "OK"},
            "body": {"items": {"item": {"a": 1}}, "totalCount": "1"},
        }
    }
    mock_response = httpx.Response(
        status_code=200,
        content=json.dumps(payload).encode(),
        request=httpx.Request("GET", "http://example.com"),
    )
    with patch.object(HttpTransport, "request", return_value=mock_response) as mock_request:
        client = Client(provider_keys={"datago": "test-key"}, cache=False)
        dataset = client.dataset("datago.air_quality")
        batch = dataset.list()
        assert len(batch.items) == 1
        kwargs = mock_request.call_args.kwargs
        params = kwargs["params"]
        # 어댑터 경로 증명: format 파라미터 값이 소문자 "json"(spec 실행기는 대문자).
        format_values = {value for value in params.values() if value in {"json", "JSON", "xml", "XML"}}
        assert format_values == {"json"}
