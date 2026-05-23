"""테스트 모듈.

이 파일은 ``tests/unit/test_failure_path_logging.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

import logging

import pytest

from kpubdata.catalog import Catalog
from kpubdata.config import KPubDataConfig
from kpubdata.core.dataset import Dataset
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.core.representation import Representation
from kpubdata.exceptions import ConfigError, DatasetNotFoundError, UnsupportedCapabilityError
from kpubdata.registry import ProviderRegistry


class _FakeAdapter:
    """
    _FakeAdapter 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/test_failure_path_logging.py`` 모듈 안에서 _FakeAdapter의 상태와 동작을 함께 관리한다.
    주요 메서드: list_datasets, search_datasets, get_dataset, query_records, get_schema.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    name = "fake"

    def list_datasets(self) -> list[DatasetRef]:
        """
        list datasets 동작을 수행한다.

        반환값:
            list[DatasetRef]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return []

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
        _ = text
        return []

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
        raise DatasetNotFoundError(
            f"Dataset not found: fake.{dataset_key}",
            provider="fake",
            dataset_id=f"fake.{dataset_key}",
        )

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
        _ = dataset, query
        raise AssertionError("query_records should not be called")

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
        _ = dataset
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
        _ = dataset, operation, params
        return None


# test catalog resolve failure logs debug 테스트가 검증하는 시나리오를 설명한다.
def test_catalog_resolve_failure_logs_debug(caplog: pytest.LogCaptureFixture) -> None:
    """
    test catalog resolve failure logs debug 시나리오를 검증한다.

    매개변수:
        caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    registry = ProviderRegistry()
    registry.register(_FakeAdapter())
    catalog = Catalog(registry)

    caplog.set_level(logging.DEBUG, logger="kpubdata.catalog")
    with pytest.raises(DatasetNotFoundError):
        _ = catalog.resolve("fake.nope")

    record = next(
        record
        for record in caplog.records
        if record.getMessage() == "Catalog resolve failed: dataset not found"
    )
    assert record.__dict__["dataset_id"] == "fake.nope"
    assert record.__dict__["provider"] == "fake"


# test dataset list unsupported logs debug 테스트가 검증하는 시나리오를 설명한다.
def test_dataset_list_unsupported_logs_debug(caplog: pytest.LogCaptureFixture) -> None:
    """
    test dataset list unsupported logs debug 시나리오를 검증한다.

    매개변수:
        caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    dataset = Dataset(
        ref=DatasetRef(
            id="fake.raw_only",
            provider="fake",
            dataset_key="raw_only",
            name="Raw Only",
            operations=frozenset(),
            representation=Representation.API_JSON,
        ),
        adapter=_FakeAdapter(),
    )

    caplog.set_level(logging.DEBUG, logger="kpubdata.dataset")
    with pytest.raises(UnsupportedCapabilityError):
        _ = dataset.list()

    record = next(
        record
        for record in caplog.records
        if record.getMessage() == "Dataset does not support LIST"
    )
    assert record.__dict__["dataset_id"] == "fake.raw_only"
    assert record.__dict__["provider"] == "fake"
    assert record.__dict__["operation"] == "list"


# test missing provider key logs debug 테스트가 검증하는 시나리오를 설명한다.
def test_missing_provider_key_logs_debug(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    test missing provider key logs debug 시나리오를 검증한다.

    매개변수:
        caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.
        monkeypatch (pytest.MonkeyPatch): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    monkeypatch.delenv("KPUBDATA_DATAGO_API_KEY", raising=False)
    monkeypatch.delenv("DATAGO_API_KEY", raising=False)
    cfg = KPubDataConfig()

    caplog.set_level(logging.DEBUG, logger="kpubdata.config")
    with pytest.raises(ConfigError):
        cfg.require_provider_key("datago")

    record = next(
        record for record in caplog.records if record.getMessage() == "Missing provider API key"
    )
    assert record.__dict__["provider"] == "datago"
