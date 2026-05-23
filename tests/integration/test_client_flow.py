"""테스트 모듈.

이 파일은 ``tests/integration/test_client_flow.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

import pytest

from kpubdata.client import Client
from kpubdata.core.capability import Operation
from kpubdata.core.dataset import Dataset
from kpubdata.core.models import DatasetRef, Query, RecordBatch
from kpubdata.core.representation import Representation
from kpubdata.exceptions import (
    DatasetNotFoundError,
    ProviderNotRegisteredError,
)


class FakeAdapter:
    """
    FakeAdapter 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/integration/test_client_flow.py`` 모듈 안에서 FakeAdapter의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__, name, list_datasets, search_datasets, get_dataset.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    def __init__(self) -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self._datasets: dict[str, DatasetRef] = {
            "weather": DatasetRef(
                id="fake.weather",
                provider="fake",
                dataset_key="weather",
                name="Weather Data",
                representation=Representation.API_JSON,
                operations=frozenset({Operation.LIST, Operation.RAW}),
            ),
            "stations": DatasetRef(
                id="fake.stations",
                provider="fake",
                dataset_key="stations",
                name="Station List",
                representation=Representation.API_JSON,
                operations=frozenset({Operation.LIST, Operation.RAW}),
            ),
        }
        self.last_query: tuple[DatasetRef, Query] | None = None
        self.last_raw_call: tuple[DatasetRef, str, dict[str, object]] | None = None

    @property
    def name(self) -> str:
        """
        name 동작을 수행한다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return "fake"

    def list_datasets(self) -> list[DatasetRef]:
        """
        list datasets 동작을 수행한다.

        반환값:
            list[DatasetRef]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return [self._datasets["weather"], self._datasets["stations"]]

    def search_datasets(self, text: str) -> list[DatasetRef]:
        """
        search datasets 동작을 수행한다.

        매개변수:
            text (str): 호출자가 제공하는 입력 값이다.

        반환값:
            list[DatasetRef]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        needle = text.casefold()
        return [
            dataset_ref
            for dataset_ref in self._datasets.values()
            if needle in dataset_ref.name.casefold()
        ]

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        """
        get dataset 동작을 수행한다.

        매개변수:
            dataset_key (str): 호출자가 제공하는 입력 값이다.

        반환값:
            DatasetRef: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        try:
            return self._datasets[dataset_key]
        except KeyError as exc:
            raise DatasetNotFoundError(f"Dataset not found: {dataset_key}") from exc

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        """
        query records 동작을 수행한다.

        매개변수:
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.
            query (Query): 호출자가 제공하는 입력 값이다.

        반환값:
            RecordBatch: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self.last_query = (dataset, query)
        return RecordBatch(
            items=[
                {"id": "w-001", "value": "sunny"},
                {"id": "w-002", "value": "rain"},
            ],
            dataset=dataset,
            total_count=2,
        )

    def get_schema(self, _dataset: DatasetRef) -> None:
        """
        get schema 동작을 수행한다.

        매개변수:
            _dataset (DatasetRef): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return None

    def call_raw(self, dataset: DatasetRef, operation: str, params: dict[str, object]) -> object:
        """
        call raw 동작을 수행한다.

        매개변수:
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.
            operation (str): 호출자가 제공하는 입력 값이다.
            params (dict[str, object]): 호출자가 제공하는 입력 값이다.

        반환값:
            object: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self.last_raw_call = (dataset, operation, params)
        return {"ok": True, "dataset": dataset.id, "operation": operation, "params": params}


def _build_client() -> tuple[Client, FakeAdapter]:
    """
    내부 헬퍼로서 build client 처리를 담당한다.

    반환값:
        tuple[Client, FakeAdapter]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    client = Client(provider_keys={"fake": "test-key"})
    fake = FakeAdapter()
    client.register_provider(fake)
    return client, fake


# test register and list datasets 테스트가 검증하는 시나리오를 설명한다.
def test_register_and_list_datasets() -> None:
    """
    test register and list datasets 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    client, _fake = _build_client()

    refs = client.datasets.list()

    fake_refs = [ref for ref in refs if ref.provider == "fake"]
    assert len(fake_refs) == 2
    assert {ref.id for ref in fake_refs} == {"fake.weather", "fake.stations"}


# test register and search datasets 테스트가 검증하는 시나리오를 설명한다.
def test_register_and_search_datasets() -> None:
    """
    test register and search datasets 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    client, _fake = _build_client()

    refs = client.datasets.search("weather")

    matched_ids = {ref.id for ref in refs}
    assert "fake.weather" in matched_ids


# test dataset resolves to bound dataset 테스트가 검증하는 시나리오를 설명한다.
def test_dataset_resolves_to_bound_dataset() -> None:
    """
    test dataset resolves to bound dataset 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    client, _fake = _build_client()

    dataset = client.dataset("fake.weather")

    assert isinstance(dataset, Dataset)
    assert dataset.id == "fake.weather"
    assert dataset.name == "Weather Data"
    assert dataset.provider == "fake"
    assert dataset.operations == frozenset({Operation.LIST, Operation.RAW})


# test dataset list delegates to query records 테스트가 검증하는 시나리오를 설명한다.
def test_dataset_list_delegates_to_query_records() -> None:
    """
    test dataset list delegates to query records 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    client, fake = _build_client()

    result = client.dataset("fake.weather").list(stationName="종로구")

    assert isinstance(result, RecordBatch)
    assert len(result.items) == 2
    assert fake.last_query is not None
    queried_dataset, query = fake.last_query
    assert queried_dataset.id == "fake.weather"
    assert query.filters == {"stationName": "종로구"}


# test dataset call raw delegates to adapter 테스트가 검증하는 시나리오를 설명한다.
def test_dataset_call_raw_delegates_to_adapter() -> None:
    """
    test dataset call raw delegates to adapter 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    client, fake = _build_client()

    result = client.dataset("fake.weather").call_raw("getWeather", param1="value1")

    assert result == {
        "ok": True,
        "dataset": "fake.weather",
        "operation": "getWeather",
        "params": {"param1": "value1"},
    }
    assert fake.last_raw_call is not None
    raw_dataset, raw_operation, raw_params = fake.last_raw_call
    assert raw_dataset.id == "fake.weather"
    assert raw_operation == "getWeather"
    assert raw_params == {"param1": "value1"}


# test dataset schema returns none 테스트가 검증하는 시나리오를 설명한다.
def test_dataset_schema_returns_none() -> None:
    """
    test dataset schema returns none 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    client, _fake = _build_client()

    result = client.dataset("fake.weather").schema()

    assert result is None


# test unknown provider raises 테스트가 검증하는 시나리오를 설명한다.
def test_unknown_provider_raises() -> None:
    """
    test unknown provider raises 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    client = Client(provider_keys={"fake": "test-key"})

    with pytest.raises(ProviderNotRegisteredError):
        _ = client.dataset("unknown.ds")


# test unknown dataset raises 테스트가 검증하는 시나리오를 설명한다.
def test_unknown_dataset_raises() -> None:
    """
    test unknown dataset raises 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    client, _fake = _build_client()

    with pytest.raises(DatasetNotFoundError):
        _ = client.dataset("fake.nonexistent")


# test from env creates client 테스트가 검증하는 시나리오를 설명한다.
def test_from_env_creates_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    test from env creates client 시나리오를 검증한다.

    매개변수:
        monkeypatch (pytest.MonkeyPatch): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    monkeypatch.setenv("KPUBDATA_TIMEOUT", "15")
    client = Client.from_env()
    fake = FakeAdapter()

    client.register_provider(fake)

    assert client.dataset("fake.weather").id == "fake.weather"
