"""테스트 모듈.

이 파일은 ``tests/unit/providers/law/test_law_adapter.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

import json
from importlib import import_module
from pathlib import Path
from typing import Protocol, cast

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query, RecordBatch
from kpubdata.transport.http import HttpTransport


def _fixture_path(name: str) -> Path:
    """
    내부 헬퍼로서 fixture path 처리를 담당한다.

    매개변수:
        name (str): 호출자가 제공하는 입력 값이다.

    반환값:
        Path: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    return Path(__file__).resolve().parents[3] / "fixtures" / "law" / name


def _load_fixture(name: str) -> dict[str, object]:
    """
    내부 헬퍼로서 load fixture 처리를 담당한다.

    매개변수:
        name (str): 호출자가 제공하는 입력 값이다.

    반환값:
        dict[str, object]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    payload = cast(object, json.loads(_fixture_path(name).read_text(encoding="utf-8")))
    if isinstance(payload, dict):
        return cast(dict[str, object], payload)
    raise ValueError(f"Fixture must be object: {name}")


class FakeResponse:
    """
    FakeResponse 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/providers/law/test_law_adapter.py`` 모듈 안에서 FakeResponse의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    def __init__(self, payload: dict[str, object]) -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        매개변수:
            payload (dict[str, object]): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self.headers: dict[str, str] = {"content-type": "application/json"}
        self.text: str = json.dumps(payload, ensure_ascii=False)
        self.content: bytes = self.text.encode("utf-8")


class FakeTransport:
    """
    FakeTransport 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/providers/law/test_law_adapter.py`` 모듈 안에서 FakeTransport의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__, request.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    def __init__(self, responses: list[FakeResponse]) -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        매개변수:
            responses (list[FakeResponse]): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self._responses: list[FakeResponse] = list(responses)
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> FakeResponse:
        """
        request 동작을 수행한다.

        매개변수:
            method (str): 호출자가 제공하는 입력 값이다.
            url (str): 호출자가 제공하는 입력 값이다.
            **kwargs (object): 호출자가 제공하는 입력 값이다.

        반환값:
            FakeResponse: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self.calls.append({"method": method, "url": url, **kwargs})
        return self._responses.pop(0)


class _AdapterFactory(Protocol):
    """
    _AdapterFactory 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/providers/law/test_law_adapter.py`` 모듈 안에서 _AdapterFactory의 상태와 동작을 함께 관리한다.
    주요 메서드: __call__.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    def __call__(
        self,
        *,
        config: KPubDataConfig | None = None,
        transport: HttpTransport | None = None,
    ) -> _LawAdapterProtocol: ...


class _LawAdapterProtocol(Protocol):
    """
    _LawAdapterProtocol 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/providers/law/test_law_adapter.py`` 모듈 안에서 _LawAdapterProtocol의 상태와 동작을 함께 관리한다.
    주요 메서드: get_dataset, list_datasets, query_records, call_raw.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    def get_dataset(self, dataset_key: str) -> DatasetRef: ...

    def list_datasets(self) -> list[DatasetRef]: ...

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch: ...

    def call_raw(
        self, dataset: DatasetRef, operation: str, params: dict[str, object]
    ) -> object: ...


def _build_adapter_with_transport(
    dataset_key: str,
    responses: list[FakeResponse],
) -> tuple[_LawAdapterProtocol, DatasetRef, FakeTransport]:
    """
    내부 헬퍼로서 build adapter with transport 처리를 담당한다.

    매개변수:
        dataset_key (str): 호출자가 제공하는 입력 값이다.
        responses (list[FakeResponse]): 호출자가 제공하는 입력 값이다.

    반환값:
        tuple[_LawAdapterProtocol, DatasetRef, FakeTransport]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    transport = FakeTransport(responses)
    adapter_module = import_module("kpubdata.providers.law.adapter")
    adapter_class_obj = cast(object, adapter_module.LawAdapter)
    adapter_class = cast(_AdapterFactory, adapter_class_obj)
    adapter = adapter_class(
        config=KPubDataConfig(provider_keys={"law": "test-law-key"}),
        transport=cast(HttpTransport, cast(object, transport)),
    )
    dataset = adapter.get_dataset(dataset_key)
    return adapter, dataset, transport


# test query records parses law search fixture 테스트가 검증하는 시나리오를 설명한다.
def test_query_records_parses_law_search_fixture() -> None:
    """
    test query records parses law search fixture 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    payload = _load_fixture("success_law_search.json")
    adapter, dataset, transport = _build_adapter_with_transport(
        "law_search", [FakeResponse(payload)]
    )

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert batch.total_count == 2
    assert batch.next_page is None
    assert batch.raw == payload
    assert batch.items[0]["법령명한글"] == "주택임대차보호법"
    assert len(transport.calls) == 1


# test query records sets next page and uses law params 테스트가 검증하는 시나리오를 설명한다.
def test_query_records_sets_next_page_and_uses_law_params() -> None:
    """
    test query records sets next page and uses law params 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    payload = _load_fixture("success_law_search.json")
    adapter, dataset, transport = _build_adapter_with_transport(
        "law_search", [FakeResponse(payload)]
    )

    batch = adapter.query_records(
        dataset,
        Query(page=1, page_size=1, filters={"query": "임대차", "search": "1"}),
    )

    request_url = cast(str, transport.calls[0]["url"])
    assert batch.next_page == 2
    assert "OC=test-law-key" in request_url
    assert "target=law" in request_url
    assert "type=JSON" in request_url
    assert "display=1" in request_url
    assert "page=1" in request_url
    assert "query=%EC%9E%84%EB%8C%80%EC%B0%A8" in request_url
    assert "search=1" in request_url


# test query records parses ordin search fixture 테스트가 검증하는 시나리오를 설명한다.
def test_query_records_parses_ordin_search_fixture() -> None:
    """
    test query records parses ordin search fixture 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    payload = _load_fixture("success_ordin_search.json")
    adapter, dataset, transport = _build_adapter_with_transport(
        "ordin_search", [FakeResponse(payload)]
    )

    batch = adapter.query_records(dataset, Query(page=1, page_size=2))

    request_url = cast(str, transport.calls[0]["url"])
    assert len(batch.items) == 2
    assert batch.total_count == 2
    assert batch.items[0]["자치법규명"] == "서울특별시 주택 임대차분쟁조정 지원 조례"
    assert "target=ordin" in request_url
    assert "display=2" in request_url


# test call raw returns law detail payload 테스트가 검증하는 시나리오를 설명한다.
def test_call_raw_returns_law_detail_payload() -> None:
    """
    test call raw returns law detail payload 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    payload = _load_fixture("success_law_detail.json")
    adapter, dataset, transport = _build_adapter_with_transport(
        "law_detail", [FakeResponse(payload)]
    )

    raw = adapter.call_raw(dataset, "lawService", {"MST": "17523"})

    request_url = cast(str, transport.calls[0]["url"])
    assert raw == payload
    assert "OC=test-law-key" in request_url
    assert "target=law" in request_url
    assert "type=JSON" in request_url
    assert "MST=17523" in request_url


# test adapter lists all datasets 테스트가 검증하는 시나리오를 설명한다.
def test_adapter_lists_all_datasets() -> None:
    """
    test adapter lists all datasets 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter_module = import_module("kpubdata.providers.law.adapter")
    adapter_class_obj = cast(object, adapter_module.LawAdapter)
    adapter_class = cast(_AdapterFactory, adapter_class_obj)
    adapter = adapter_class(config=KPubDataConfig(provider_keys={"law": "test-law-key"}))

    datasets = adapter.list_datasets()

    assert [dataset.dataset_key for dataset in datasets] == [
        "law_search",
        "law_detail",
        "ordin_search",
    ]
