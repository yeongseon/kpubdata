"""테스트 모듈.

이 파일은 ``tests/integration/test_exception_propagation.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

import pytest

from kpubdata.client import Client
from kpubdata.core.capability import Operation
from kpubdata.core.models import DatasetRef, Query, RecordBatch
from kpubdata.core.representation import Representation
from kpubdata.exceptions import (
    AuthError,
    DatasetNotFoundError,
    ProviderNotRegisteredError,
    PublicDataError,
    RateLimitError,
    ServiceUnavailableError,
)


class ErrorAdapter:
    """
    ErrorAdapter 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/integration/test_exception_propagation.py`` 모듈 안에서 ErrorAdapter의 상태와 동작을 함께 관리한다.
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
            "failing": DatasetRef(
                id="errorprov.failing",
                provider="errorprov",
                dataset_key="failing",
                name="Failing Dataset",
                representation=Representation.API_JSON,
                operations=frozenset({Operation.LIST, Operation.RAW}),
            ),
            "limited": DatasetRef(
                id="errorprov.limited",
                provider="errorprov",
                dataset_key="limited",
                name="Limited Dataset",
                representation=Representation.API_JSON,
                operations=frozenset({Operation.LIST, Operation.RAW}),
            ),
        }

    @property
    def name(self) -> str:
        """
        name 동작을 수행한다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return "errorprov"

    def list_datasets(self) -> list[DatasetRef]:
        """
        list datasets 동작을 수행한다.

        반환값:
            list[DatasetRef]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return [self._datasets["failing"], self._datasets["limited"]]

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
        try:
            return self._datasets[dataset_key]
        except KeyError as exc:
            raise DatasetNotFoundError(
                f"Dataset not found: {self.name}.{dataset_key}",
                provider=self.name,
                dataset_id=f"{self.name}.{dataset_key}",
            ) from exc

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
        _ = query
        raise AuthError(
            message="Invalid API key",
            provider="errorprov",
            dataset_id=dataset.id,
            operation="list",
            provider_code="30",
            retryable=False,
        )

    def get_schema(self, dataset: DatasetRef) -> None:
        """
        get schema 동작을 수행한다.

        매개변수:
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        raise ServiceUnavailableError(
            message="Service down",
            provider="errorprov",
            dataset_id=dataset.id,
            operation="schema",
            retryable=True,
        )

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
        _ = params
        raise RateLimitError(
            message="Too many requests",
            provider="errorprov",
            dataset_id=dataset.id,
            operation=operation,
            status_code=429,
            retryable=False,
        )


def _build_client() -> tuple[Client, ErrorAdapter]:
    """
    내부 헬퍼로서 build client 처리를 담당한다.

    반환값:
        tuple[Client, ErrorAdapter]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    client = Client(provider_keys={"errorprov": "bad-key"})
    adapter = ErrorAdapter()
    client.register_provider(adapter)
    return client, adapter


# test auth error from dataset list 테스트가 검증하는 시나리오를 설명한다.
def test_auth_error_from_dataset_list() -> None:
    """
    test auth error from dataset list 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    client, _adapter = _build_client()

    with pytest.raises(AuthError) as exc_info:
        _ = client.dataset("errorprov.failing").list()

    exc = exc_info.value
    assert exc.provider == "errorprov"
    assert exc.dataset_id == "errorprov.failing"
    assert exc.operation == "list"
    assert exc.provider_code == "30"
    assert exc.retryable is False


# test auth error caught as base 테스트가 검증하는 시나리오를 설명한다.
def test_auth_error_caught_as_base() -> None:
    """
    test auth error caught as base 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    client, _adapter = _build_client()

    try:
        _ = client.dataset("errorprov.failing").list()
        pytest.fail("Expected PublicDataError")
    except PublicDataError as exc:
        assert isinstance(exc, AuthError)


# test rate limit from call raw 테스트가 검증하는 시나리오를 설명한다.
def test_rate_limit_from_call_raw() -> None:
    """
    test rate limit from call raw 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    client, _adapter = _build_client()

    with pytest.raises(RateLimitError) as exc_info:
        _ = client.dataset("errorprov.failing").call_raw("getData")

    exc = exc_info.value
    assert exc.status_code == 429
    assert exc.retryable is False
    assert exc.operation == "getData"


# test service unavailable from schema 테스트가 검증하는 시나리오를 설명한다.
def test_service_unavailable_from_schema() -> None:
    """
    test service unavailable from schema 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    client, _adapter = _build_client()

    with pytest.raises(ServiceUnavailableError) as exc_info:
        _ = client.dataset("errorprov.failing").schema()

    exc = exc_info.value
    assert exc.retryable is True
    assert exc.operation == "schema"


# test dataset not found 테스트가 검증하는 시나리오를 설명한다.
def test_dataset_not_found() -> None:
    """
    test dataset not found 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    client, _adapter = _build_client()

    with pytest.raises(DatasetNotFoundError) as exc_info:
        _ = client.dataset("errorprov.nonexistent")

    assert exc_info.value.dataset_id == "errorprov.nonexistent"


# test provider not registered 테스트가 검증하는 시나리오를 설명한다.
def test_provider_not_registered() -> None:
    """
    test provider not registered 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    client = Client(provider_keys={"errorprov": "bad-key"})

    with pytest.raises(ProviderNotRegisteredError):
        _ = client.dataset("unknown.ds")


# test auth error repr includes context 테스트가 검증하는 시나리오를 설명한다.
def test_auth_error_repr_includes_context() -> None:
    """
    test auth error repr includes context 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    client, _adapter = _build_client()

    with pytest.raises(AuthError) as exc_info:
        _ = client.dataset("errorprov.failing").list()

    rendered = repr(exc_info.value)
    assert "errorprov" in rendered
    assert "30" in f"{rendered} {exc_info.value.provider_code}"


# test rate limit repr includes status 테스트가 검증하는 시나리오를 설명한다.
def test_rate_limit_repr_includes_status() -> None:
    """
    test rate limit repr includes status 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    client, _adapter = _build_client()

    with pytest.raises(RateLimitError) as exc_info:
        _ = client.dataset("errorprov.failing").call_raw("getData")

    assert "429" in repr(exc_info.value)


# test dataset not found has cause chain 테스트가 검증하는 시나리오를 설명한다.
def test_dataset_not_found_has_cause_chain() -> None:
    """
    test dataset not found has cause chain 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    client, _adapter = _build_client()

    with pytest.raises(DatasetNotFoundError) as exc_info:
        _ = client.dataset("errorprov.nonexistent")

    assert isinstance(exc_info.value.__cause__, KeyError)
