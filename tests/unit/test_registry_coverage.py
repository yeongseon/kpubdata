"""테스트 모듈.

이 파일은 ``tests/unit/test_registry_coverage.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

from typing import Any

import pytest

from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.registry import ProviderRegistry


class _ValidAdapter:
    """
    _ValidAdapter 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/test_registry_coverage.py`` 모듈 안에서 _ValidAdapter의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__, name, list_datasets, search_datasets, get_dataset.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    def __init__(self, provider_name: str) -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        매개변수:
            provider_name (str): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self._name: str = provider_name

    @property
    def name(self) -> str:
        """
        name 동작을 수행한다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return self._name

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
        raise LookupError(dataset_key)

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
        return RecordBatch(items=[], dataset=dataset)

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
        return None


class _NameOnlyAdapter:
    """
    _NameOnlyAdapter 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/test_registry_coverage.py`` 모듈 안에서 _NameOnlyAdapter의 상태와 동작을 함께 관리한다.
    주요 메서드: 없음.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    name: str = "broken"


def _build_non_callable_adapter() -> Any:
    """
    내부 헬퍼로서 build non callable adapter 처리를 담당한다.

    반환값:
        Any: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    return type(
        "BrokenAdapter",
        (),
        {
            "name": "ok",
            "list_datasets": None,
            "search_datasets": lambda self, text: [],
            "get_dataset": lambda self, dataset_key: None,
            "query_records": lambda self, dataset, query: None,
            "get_schema": lambda self, dataset: None,
            "call_raw": lambda self, dataset, operation, params: None,
        },
    )()


# test repr lists eager and lazy names 테스트가 검증하는 시나리오를 설명한다.
def test_repr_lists_eager_and_lazy_names() -> None:
    """
    test repr lists eager and lazy names 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    registry = ProviderRegistry()
    registry.register(_ValidAdapter("eager"))
    registry.register_lazy("lazy", lambda: _ValidAdapter("lazy"))

    rendered = repr(registry)

    assert rendered == "ProviderRegistry(eager=['eager'], lazy=['lazy'])"


# test register lazy rejects empty name 테스트가 검증하는 시나리오를 설명한다.
def test_register_lazy_rejects_empty_name() -> None:
    """
    test register lazy rejects empty name 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    registry = ProviderRegistry()

    with pytest.raises(ValueError, match="cannot be empty"):
        registry.register_lazy("   ", lambda: _ValidAdapter("x"))


# test register lazy rejects non callable factory 테스트가 검증하는 시나리오를 설명한다.
def test_register_lazy_rejects_non_callable_factory() -> None:
    """
    test register lazy rejects non callable factory 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    registry = ProviderRegistry()

    with pytest.raises(TypeError, match="must be callable"):
        registry.register_lazy("x", object())


# test register lazy rejects duplicate name 테스트가 검증하는 시나리오를 설명한다.
def test_register_lazy_rejects_duplicate_name() -> None:
    """
    test register lazy rejects duplicate name 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    registry = ProviderRegistry()
    registry.register_lazy("dup", lambda: _ValidAdapter("dup"))

    with pytest.raises(ValueError, match="already registered"):
        registry.register_lazy("dup", lambda: _ValidAdapter("dup"))


# test get rejects lazy adapter name mismatch 테스트가 검증하는 시나리오를 설명한다.
def test_get_rejects_lazy_adapter_name_mismatch() -> None:
    """
    test get rejects lazy adapter name mismatch 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    registry = ProviderRegistry()
    registry.register_lazy("expected", lambda: _ValidAdapter("actual"))

    with pytest.raises(TypeError, match="name mismatch"):
        registry.get("expected")


# test validate adapter rejects missing methods 테스트가 검증하는 시나리오를 설명한다.
def test_validate_adapter_rejects_missing_methods() -> None:
    """
    test validate adapter rejects missing methods 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    with pytest.raises(TypeError, match="missing required methods"):
        ProviderRegistry._validate_adapter(_NameOnlyAdapter())


# test validate adapter rejects non callable methods 테스트가 검증하는 시나리오를 설명한다.
def test_validate_adapter_rejects_non_callable_methods() -> None:
    """
    test validate adapter rejects non callable methods 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    with pytest.raises(TypeError, match="non-callable required methods"):
        ProviderRegistry._validate_adapter(_build_non_callable_adapter())
