"""Logging coverage tests — assert structured DEBUG records are emitted."""

from __future__ import annotations

import logging
from typing import Any

import pytest

from kpubdata.catalog import Catalog
from kpubdata.client import Client
from kpubdata.core.capability import Operation
from kpubdata.core.dataset import Dataset
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.core.representation import Representation
from kpubdata.exceptions import DatasetNotFoundError, ProviderNotRegisteredError
from kpubdata.registry import ProviderRegistry
from kpubdata.transport.decode import decode_json, decode_xml, detect_content_type


class _FakeAdapter:
    """
    _FakeAdapter 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/test_logging.py`` 모듈 안에서 _FakeAdapter의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__, list_datasets, search_datasets, get_dataset, query_records.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    name = "fake"

    def __init__(self) -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self.ref: DatasetRef = DatasetRef(
            id="fake.demo",
            provider="fake",
            dataset_key="demo",
            name="Demo Dataset",
            operations=frozenset({Operation.LIST}),
            representation=Representation.API_JSON,
        )

    def list_datasets(self) -> list[DatasetRef]:
        """
        list datasets 동작을 수행한다.

        반환값:
            list[DatasetRef]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return [self.ref]

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
        return [self.ref] if text.lower() in self.ref.id else []

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
        if dataset_key != "demo":
            raise DatasetNotFoundError(
                f"Dataset not found: fake.{dataset_key}",
                provider="fake",
                dataset_id=f"fake.{dataset_key}",
            )
        return self.ref

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
        return RecordBatch(items=[{"id": 1}], dataset=dataset, total_count=1, raw=None)

    def get_schema(self, dataset: DatasetRef) -> SchemaDescriptor | None:
        """
        get schema 동작을 수행한다.

        매개변수:
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.

        반환값:
            SchemaDescriptor | None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

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
        return {"operation": operation, "params": params}


def _records(caplog: pytest.LogCaptureFixture, name: str) -> list[logging.LogRecord]:
    """
    내부 헬퍼로서 records 처리를 담당한다.

    매개변수:
        caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.
        name (str): 호출자가 제공하는 입력 값이다.

    반환값:
        list[logging.LogRecord]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    return [r for r in caplog.records if r.name == name]


def _by_message(records: list[logging.LogRecord], message: str) -> logging.LogRecord:
    """
    내부 헬퍼로서 by message 처리를 담당한다.

    매개변수:
        records (list[logging.LogRecord]): 호출자가 제공하는 입력 값이다.
        message (str): 호출자가 제공하는 입력 값이다.

    반환값:
        logging.LogRecord: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    for record in records:
        if record.getMessage() == message:
            return record
    raise AssertionError(f"No log record with message {message!r}")


@pytest.fixture
def fake_client(caplog: pytest.LogCaptureFixture) -> Client:
    """
    fake client 동작을 수행한다.

    매개변수:
        caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

    반환값:
        Client: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    caplog.set_level(logging.DEBUG, logger="kpubdata")
    client = Client()
    client.register_provider(_FakeAdapter())
    return client


class TestClientLogging:
    """
    TestClientLogging 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/test_logging.py`` 모듈 안에서 TestClientLogging의 상태와 동작을 함께 관리한다.
    주요 메서드: test_init_emits_debug, test_close_emits_debug, test_dataset_binding_logs.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    # test init emits debug 테스트가 검증하는 시나리오를 설명한다.
    def test_init_emits_debug(self, caplog: pytest.LogCaptureFixture) -> None:
        """
        test init emits debug 시나리오를 검증한다.

        매개변수:
            caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        caplog.set_level(logging.DEBUG, logger="kpubdata.client")
        _ = Client()
        records = _records(caplog, "kpubdata.client")
        record = _by_message(records, "Client initialized")
        assert isinstance(record.providers, list)  # type: ignore[attr-defined]
        assert "datago" in record.providers  # type: ignore[attr-defined]

    # test close emits debug 테스트가 검증하는 시나리오를 설명한다.
    def test_close_emits_debug(self, caplog: pytest.LogCaptureFixture) -> None:
        """
        test close emits debug 시나리오를 검증한다.

        매개변수:
            caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        caplog.set_level(logging.DEBUG, logger="kpubdata.client")
        client = Client()
        caplog.clear()
        client.close()
        records = _records(caplog, "kpubdata.client")
        _ = _by_message(records, "Client closing")

    # test dataset binding logs 테스트가 검증하는 시나리오를 설명한다.
    def test_dataset_binding_logs(
        self, fake_client: Client, caplog: pytest.LogCaptureFixture
    ) -> None:
        """
        test dataset binding logs 시나리오를 검증한다.

        매개변수:
            fake_client (Client): 호출자가 제공하는 입력 값이다.
            caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        caplog.clear()
        caplog.set_level(logging.DEBUG, logger="kpubdata.client")
        _ = fake_client.dataset("fake.demo")
        records = _records(caplog, "kpubdata.client")
        _ = _by_message(records, "Binding dataset")
        bound = _by_message(records, "Dataset bound")
        assert bound.dataset_id == "fake.demo"  # type: ignore[attr-defined]


class TestRegistryLogging:
    """
    TestRegistryLogging 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/test_logging.py`` 모듈 안에서 TestRegistryLogging의 상태와 동작을 함께 관리한다.
    주요 메서드: test_register_logs, test_lookup_failure_logs, test_lazy_register_and_materialize_logs.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    # test register logs 테스트가 검증하는 시나리오를 설명한다.
    def test_register_logs(self, caplog: pytest.LogCaptureFixture) -> None:
        """
        test register logs 시나리오를 검증한다.

        매개변수:
            caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        caplog.set_level(logging.DEBUG, logger="kpubdata.registry")
        registry = ProviderRegistry()
        registry.register(_FakeAdapter())
        records = _records(caplog, "kpubdata.registry")
        record = _by_message(records, "Registered eager provider adapter")
        assert record.provider == "fake"  # type: ignore[attr-defined]

    # test lookup failure logs 테스트가 검증하는 시나리오를 설명한다.
    def test_lookup_failure_logs(self, caplog: pytest.LogCaptureFixture) -> None:
        """
        test lookup failure logs 시나리오를 검증한다.

        매개변수:
            caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        caplog.set_level(logging.DEBUG, logger="kpubdata.registry")
        registry = ProviderRegistry()
        with pytest.raises(ProviderNotRegisteredError):
            registry.get("missing")
        records = _records(caplog, "kpubdata.registry")
        record = _by_message(records, "Provider lookup failed")
        assert record.provider == "missing"  # type: ignore[attr-defined]

    # test lazy register and materialize logs 테스트가 검증하는 시나리오를 설명한다.
    def test_lazy_register_and_materialize_logs(self, caplog: pytest.LogCaptureFixture) -> None:
        """
        test lazy register and materialize logs 시나리오를 검증한다.

        매개변수:
            caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        caplog.set_level(logging.DEBUG, logger="kpubdata.registry")
        registry = ProviderRegistry()
        registry.register_lazy("fake", _FakeAdapter)
        adapter = registry.get("fake")
        assert isinstance(adapter, _FakeAdapter)
        records = _records(caplog, "kpubdata.registry")
        _ = _by_message(records, "Registered lazy provider adapter")
        _ = _by_message(records, "Materializing lazy provider adapter")
        _ = _by_message(records, "Materialized lazy provider adapter")


class TestCatalogLogging:
    """
    TestCatalogLogging 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/test_logging.py`` 모듈 안에서 TestCatalogLogging의 상태와 동작을 함께 관리한다.
    주요 메서드: test_list_logs, test_search_logs, test_resolve_failure_logs, test_invalid_id_logs.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    # test list logs 테스트가 검증하는 시나리오를 설명한다.
    def test_list_logs(self, fake_client: Client, caplog: pytest.LogCaptureFixture) -> None:
        """
        test list logs 시나리오를 검증한다.

        매개변수:
            fake_client (Client): 호출자가 제공하는 입력 값이다.
            caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        caplog.clear()
        caplog.set_level(logging.DEBUG, logger="kpubdata.catalog")
        result = fake_client.datasets.list()
        assert len(result) >= 1
        records = _records(caplog, "kpubdata.catalog")
        _ = _by_message(records, "Catalog list")
        _ = _by_message(records, "Catalog list result")

    # test search logs 테스트가 검증하는 시나리오를 설명한다.
    def test_search_logs(self, fake_client: Client, caplog: pytest.LogCaptureFixture) -> None:
        """
        test search logs 시나리오를 검증한다.

        매개변수:
            fake_client (Client): 호출자가 제공하는 입력 값이다.
            caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        caplog.clear()
        caplog.set_level(logging.DEBUG, logger="kpubdata.catalog")
        _ = fake_client.datasets.search("fake")
        records = _records(caplog, "kpubdata.catalog")
        record = _by_message(records, "Catalog search")
        assert record.text == "fake"  # type: ignore[attr-defined]

    # test resolve failure logs 테스트가 검증하는 시나리오를 설명한다.
    def test_resolve_failure_logs(
        self, fake_client: Client, caplog: pytest.LogCaptureFixture
    ) -> None:
        """
        test resolve failure logs 시나리오를 검증한다.

        매개변수:
            fake_client (Client): 호출자가 제공하는 입력 값이다.
            caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        caplog.clear()
        caplog.set_level(logging.DEBUG, logger="kpubdata.catalog")
        with pytest.raises(DatasetNotFoundError):
            _ = fake_client.dataset("fake.nope")
        records = _records(caplog, "kpubdata.catalog")
        _ = _by_message(records, "Catalog resolve failed: dataset not found")

    # test invalid id logs 테스트가 검증하는 시나리오를 설명한다.
    def test_invalid_id_logs(self, caplog: pytest.LogCaptureFixture) -> None:
        """
        test invalid id logs 시나리오를 검증한다.

        매개변수:
            caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        caplog.set_level(logging.DEBUG, logger="kpubdata.catalog")
        registry = ProviderRegistry()
        catalog = Catalog(registry)
        with pytest.raises(DatasetNotFoundError):
            _ = catalog.resolve("invalid_id_no_dot")


class TestDatasetLogging:
    """
    TestDatasetLogging 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/test_logging.py`` 모듈 안에서 TestDatasetLogging의 상태와 동작을 함께 관리한다.
    주요 메서드: test_list_logs, test_call_raw_logs, test_list_all_logs_iterations.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    # test list logs 테스트가 검증하는 시나리오를 설명한다.
    def test_list_logs(self, fake_client: Client, caplog: pytest.LogCaptureFixture) -> None:
        """
        test list logs 시나리오를 검증한다.

        매개변수:
            fake_client (Client): 호출자가 제공하는 입력 값이다.
            caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        ds = fake_client.dataset("fake.demo")
        caplog.clear()
        caplog.set_level(logging.DEBUG, logger="kpubdata.dataset")
        _ = ds.list(page=1, page_size=10, custom_filter="x")
        records = _records(caplog, "kpubdata.dataset")
        dispatch = _by_message(records, "Dataset.list dispatching")
        assert dispatch.page == 1  # type: ignore[attr-defined]
        assert dispatch.page_size == 10  # type: ignore[attr-defined]
        assert "custom_filter" in dispatch.filter_keys  # type: ignore[attr-defined]
        completed = _by_message(records, "Dataset.list completed")
        assert completed.item_count == 1  # type: ignore[attr-defined]

    # test call raw logs 테스트가 검증하는 시나리오를 설명한다.
    def test_call_raw_logs(self, fake_client: Client, caplog: pytest.LogCaptureFixture) -> None:
        """
        test call raw logs 시나리오를 검증한다.

        매개변수:
            fake_client (Client): 호출자가 제공하는 입력 값이다.
            caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        ds = fake_client.dataset("fake.demo")
        caplog.clear()
        caplog.set_level(logging.DEBUG, logger="kpubdata.dataset")
        _ = ds.call_raw("op", a=1, b=2)
        records = _records(caplog, "kpubdata.dataset")
        record = _by_message(records, "Dataset.call_raw dispatching")
        assert record.operation == "op"  # type: ignore[attr-defined]
        assert record.param_keys == ["a", "b"]  # type: ignore[attr-defined]

    # test list all logs iterations 테스트가 검증하는 시나리오를 설명한다.
    def test_list_all_logs_iterations(self, caplog: pytest.LogCaptureFixture) -> None:
        """
        test list all logs iterations 시나리오를 검증한다.

        매개변수:
            caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        ref = DatasetRef(
            id="fake.demo",
            provider="fake",
            dataset_key="demo",
            name="Demo",
            operations=frozenset({Operation.LIST}),
            representation=Representation.API_JSON,
        )

        class _PagedAdapter:
            """
            _PagedAdapter 관련 역할을 캡슐화하는 클래스.

            이 클래스는 ``tests/unit/test_logging.py`` 모듈 안에서 _PagedAdapter의 상태와 동작을 함께 관리한다.
            주요 메서드: __init__, query_records, get_schema, call_raw.

            속성 설명:
                생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
            """
            name = "fake"

            def __init__(self) -> None:
                """
                인스턴스가 사용할 내부 상태를 초기화한다.

                반환값:
                    None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

                예외:
                    구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
                """
                self.calls = 0

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
                self.calls += 1
                next_page = 2 if self.calls == 1 else None
                return RecordBatch(
                    items=[{"i": self.calls}],
                    dataset=dataset,
                    total_count=2,
                    next_page=next_page,
                    raw=None,
                )

            def get_schema(self, dataset: DatasetRef) -> SchemaDescriptor | None:
                """
                get schema 동작을 수행한다.

                매개변수:
                    dataset (DatasetRef): 호출자가 제공하는 입력 값이다.

                반환값:
                    SchemaDescriptor | None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

                예외:
                    구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
                """
                return None

            def call_raw(
                self, dataset: DatasetRef, operation: str, params: dict[str, object]
            ) -> object:
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
                return None

        adapter: Any = _PagedAdapter()
        ds = Dataset(ref=ref, adapter=adapter)
        caplog.set_level(logging.DEBUG, logger="kpubdata.dataset")
        batches = list(ds.list_all())
        assert len(batches) == 2
        records = _records(caplog, "kpubdata.dataset")
        _ = _by_message(records, "Dataset.list_all starting")
        _ = _by_message(records, "Dataset.list_all advancing")
        completed = _by_message(records, "Dataset.list_all completed")
        assert completed.iterations == 2  # type: ignore[attr-defined]


class TestDecodeLogging:
    """
    TestDecodeLogging 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/test_logging.py`` 모듈 안에서 TestDecodeLogging의 상태와 동작을 함께 관리한다.
    주요 메서드: test_json_parse_failure_logs, test_xml_parse_failure_logs, test_unrecognized_content_type_logs.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    # test json parse failure logs 테스트가 검증하는 시나리오를 설명한다.
    def test_json_parse_failure_logs(self, caplog: pytest.LogCaptureFixture) -> None:
        """
        test json parse failure logs 시나리오를 검증한다.

        매개변수:
            caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        from kpubdata.exceptions import ParseError

        caplog.set_level(logging.DEBUG, logger="kpubdata.transport.decode")
        with pytest.raises(ParseError):
            _ = decode_json(b"{not json}")
        records = _records(caplog, "kpubdata.transport.decode")
        _ = _by_message(records, "JSON parse failed")

    # test xml parse failure logs 테스트가 검증하는 시나리오를 설명한다.
    def test_xml_parse_failure_logs(self, caplog: pytest.LogCaptureFixture) -> None:
        """
        test xml parse failure logs 시나리오를 검증한다.

        매개변수:
            caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        from kpubdata.exceptions import ParseError

        caplog.set_level(logging.DEBUG, logger="kpubdata.transport.decode")
        with pytest.raises(ParseError):
            _ = decode_xml(b"<broken")
        records = _records(caplog, "kpubdata.transport.decode")
        _ = _by_message(records, "XML parse failed")

    # test unrecognized content type logs 테스트가 검증하는 시나리오를 설명한다.
    def test_unrecognized_content_type_logs(self, caplog: pytest.LogCaptureFixture) -> None:
        """
        test unrecognized content type logs 시나리오를 검증한다.

        매개변수:
            caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        import httpx

        caplog.set_level(logging.DEBUG, logger="kpubdata.transport.decode")
        response = httpx.Response(
            200, content=b"x", headers={"content-type": "application/octet-stream"}
        )
        assert detect_content_type(response) == "other"
        records = _records(caplog, "kpubdata.transport.decode")
        _ = _by_message(records, "Unrecognized content-type, defaulting to 'other'")
