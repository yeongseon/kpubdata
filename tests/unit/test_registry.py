"""Tests for provider registry."""

from __future__ import annotations

import pytest

from kpubdata.exceptions import ProviderNotRegisteredError
from kpubdata.registry import ProviderRegistry


class FakeAdapter:
    """Minimal adapter satisfying the protocol for testing."""

    def __init__(self, provider_name: str = "fake") -> None:
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

    def list_datasets(self) -> list[object]:
        """
        list datasets 동작을 수행한다.

        반환값:
            list[object]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return []

    def search_datasets(self, text: str) -> list[object]:
        """
        search datasets 동작을 수행한다.

        매개변수:
            text (str): 호출자가 제공하는 입력 값이다.

        반환값:
            list[object]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        _ = text
        return []

    def get_dataset(self, dataset_key: str) -> object:
        """
        get dataset 동작을 수행한다.

        매개변수:
            dataset_key (str): 호출자가 제공하는 입력 값이다.

        반환값:
            object: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return None

    def query_records(self, dataset: object, query: object) -> object:
        """
        query records 동작을 수행한다.

        매개변수:
            dataset (object): 호출자가 제공하는 입력 값이다.
            query (object): 호출자가 제공하는 입력 값이다.

        반환값:
            object: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return None

    def get_schema(self, dataset: object) -> object:
        """
        get schema 동작을 수행한다.

        매개변수:
            dataset (object): 호출자가 제공하는 입력 값이다.

        반환값:
            object: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return None

    def call_raw(self, dataset: object, operation: str, params: dict[str, object]) -> object:
        """
        call raw 동작을 수행한다.

        매개변수:
            dataset (object): 호출자가 제공하는 입력 값이다.
            operation (str): 호출자가 제공하는 입력 값이다.
            params (dict[str, object]): 호출자가 제공하는 입력 값이다.

        반환값:
            object: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        _ = dataset, operation, params
        return None


class TestProviderRegistry:
    """
    TestProviderRegistry 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/test_registry.py`` 모듈 안에서 TestProviderRegistry의 상태와 동작을 함께 관리한다.
    주요 메서드: test_register_and_get, test_contains, test_iter, test_duplicate_raises, test_missing_raises.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    # test register and get 테스트가 검증하는 시나리오를 설명한다.
    def test_register_and_get(self) -> None:
        """
        test register and get 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        reg = ProviderRegistry()
        adapter = FakeAdapter("test")
        reg.register(adapter)
        assert reg.get("test") is adapter

    # test contains 테스트가 검증하는 시나리오를 설명한다.
    def test_contains(self) -> None:
        """
        test contains 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        reg = ProviderRegistry()
        reg.register(FakeAdapter("test"))
        assert "test" in reg
        assert "other" not in reg

    # test iter 테스트가 검증하는 시나리오를 설명한다.
    def test_iter(self) -> None:
        """
        test iter 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        reg = ProviderRegistry()
        reg.register(FakeAdapter("b"))
        reg.register(FakeAdapter("a"))
        assert list(reg) == ["a", "b"]

    # test duplicate raises 테스트가 검증하는 시나리오를 설명한다.
    def test_duplicate_raises(self) -> None:
        """
        test duplicate raises 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        reg = ProviderRegistry()
        reg.register(FakeAdapter("dup"))
        with pytest.raises(ValueError, match="already registered"):
            reg.register(FakeAdapter("dup"))

    # test missing raises 테스트가 검증하는 시나리오를 설명한다.
    def test_missing_raises(self) -> None:
        """
        test missing raises 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        reg = ProviderRegistry()
        with pytest.raises(ProviderNotRegisteredError):
            reg.get("nonexistent")

    # test lazy register 테스트가 검증하는 시나리오를 설명한다.
    def test_lazy_register(self) -> None:
        """
        test lazy register 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        reg = ProviderRegistry()
        reg.register_lazy("lazy", lambda: FakeAdapter("lazy"))
        assert "lazy" in reg
        adapter = reg.get("lazy")
        assert adapter.name == "lazy"

    # test validate rejects bad adapter 테스트가 검증하는 시나리오를 설명한다.
    def test_validate_rejects_bad_adapter(self) -> None:
        """
        test validate rejects bad adapter 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        reg = ProviderRegistry()
        with pytest.raises(TypeError):
            reg.register(object())  # type: ignore[arg-type]
