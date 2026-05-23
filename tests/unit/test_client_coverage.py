"""테스트 모듈.

이 파일은 ``tests/unit/test_client_coverage.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from kpubdata.client import Client
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor


class _Adapter:
    """
    _Adapter 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/test_client_coverage.py`` 모듈 안에서 _Adapter의 상태와 동작을 함께 관리한다.
    주요 메서드: name, list_datasets, search_datasets, get_dataset, query_records.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    @property
    def name(self) -> str:
        """
        name 동작을 수행한다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return "alpha"

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


# test enter delegates to transport and returns self 테스트가 검증하는 시나리오를 설명한다.
def test_enter_delegates_to_transport_and_returns_self() -> None:
    """
    test enter delegates to transport and returns self 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    client = Client()
    transport = MagicMock()
    client._transport = transport

    entered = client.__enter__()

    transport.__enter__.assert_called_once_with()
    assert entered is client


# test close delegates to transport close 테스트가 검증하는 시나리오를 설명한다.
def test_close_delegates_to_transport_close() -> None:
    """
    test close delegates to transport close 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    client = Client()
    transport = MagicMock()
    client._transport = transport

    client.close()

    transport.close.assert_called_once_with()


# test exit calls close 테스트가 검증하는 시나리오를 설명한다.
def test_exit_calls_close() -> None:
    """
    test exit calls close 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    client = Client()
    client.close = MagicMock()

    client.__exit__(None, None, None)

    client.close.assert_called_once_with()


# test repr includes registered provider names 테스트가 검증하는 시나리오를 설명한다.
def test_repr_includes_registered_provider_names() -> None:
    """
    test repr includes registered provider names 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    client = Client()
    client.register_provider(_Adapter())

    rendered = repr(client)

    assert "alpha" in rendered
    assert "datago" in rendered
    assert "bok" in rendered
    assert "kosis" in rendered


# test builtin providers registered by default 테스트가 검증하는 시나리오를 설명한다.
def test_builtin_providers_registered_by_default() -> None:
    """
    test builtin providers registered by default 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    client = Client()

    assert "datago" in client._registry
    assert "bok" in client._registry
    assert "kosis" in client._registry


# test builtin providers datasets discoverable 테스트가 검증하는 시나리오를 설명한다.
def test_builtin_providers_datasets_discoverable() -> None:
    """
    test builtin providers datasets discoverable 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    client = Client()

    datasets = client.datasets.list()

    assert len(datasets) > 0
    provider_names = {ds.provider for ds in datasets}
    assert "datago" in provider_names
    assert "bok" in provider_names
    assert "kosis" in provider_names


# test builtin dataset binding works 테스트가 검증하는 시나리오를 설명한다.
def test_builtin_dataset_binding_works() -> None:
    """
    test builtin dataset binding works 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    client = Client()

    ds = client.dataset("datago.village_fcst")

    assert ds.id == "datago.village_fcst"
    assert ds.provider == "datago"


# test user adapter overrides builtin 테스트가 검증하는 시나리오를 설명한다.
def test_user_adapter_overrides_builtin() -> None:
    """
    test user adapter overrides builtin 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    class _DatagoOverride(_Adapter):
        """
        _DatagoOverride 관련 역할을 캡슐화하는 클래스.

        이 클래스는 ``tests/unit/test_client_coverage.py`` 모듈 안에서 _DatagoOverride의 상태와 동작을 함께 관리한다.
        주요 메서드: name.

        속성 설명:
            생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
        """
        @property
        def name(self) -> str:
            """
            name 동작을 수행한다.

            반환값:
                str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

            예외:
                구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
            """
            return "datago"

    client = Client()
    client._registry._lazy.pop("datago", None)
    client.register_provider(_DatagoOverride())

    adapter = client._registry.get("datago")
    assert isinstance(adapter, _DatagoOverride)
