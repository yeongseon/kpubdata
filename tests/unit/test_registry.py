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


class TestCapabilityContractValidation:
    """등록 시점 capability 계약 검증(#231)에 대한 테스트."""

    def _ds(self, key: str, *, operations: tuple[str, ...] = ("list", "raw")) -> object:
        """테스트용 DatasetRef를 만든다."""
        from kpubdata.core.capability import Operation
        from kpubdata.core.models import DatasetRef
        from kpubdata.core.representation import Representation

        return DatasetRef(
            id=f"fake.{key}",
            provider="fake",
            dataset_key=key,
            name=key,
            representation=Representation.API_JSON,
            operations=frozenset(Operation(op) for op in operations),
        )

    def test_registration_calls_list_datasets_and_passes_for_honest_adapter(self) -> None:
        """list_datasets가 비어 있지 않고 operations가 채워져 있으면 통과한다."""
        from kpubdata.registry import ProviderRegistry

        honest = FakeAdapter("honest")
        honest_datasets = [self._ds("a"), self._ds("b")]
        honest.list_datasets = lambda: honest_datasets  # type: ignore[method-assign]

        reg = ProviderRegistry()
        reg.register(honest)  # 예외가 발생하지 않아야 한다.
        assert "honest" in reg

    def test_registration_rejects_adapter_whose_list_datasets_crashes(self) -> None:
        """list_datasets가 예외를 던지면 CapabilityContractError로 빠르게 실패한다."""
        from kpubdata.exceptions import CapabilityContractError
        from kpubdata.registry import ProviderRegistry

        broken = FakeAdapter("broken")

        def boom() -> list[object]:
            raise RuntimeError("catalogue not loaded")

        broken.list_datasets = boom  # type: ignore[method-assign]

        reg = ProviderRegistry()
        with pytest.raises(CapabilityContractError, match="failed to enumerate datasets"):
            reg.register(broken)
        assert "broken" not in reg

    def test_registration_rejects_dataset_with_empty_operations(self) -> None:
        """operations가 빈 집합인 dataset은 "지원 거짓 표시"로 간주해 거부한다."""
        from kpubdata.exceptions import CapabilityContractError
        from kpubdata.registry import ProviderRegistry

        dishonest = FakeAdapter("dishonest")
        dishonest_datasets = [self._ds("a", operations=())]
        dishonest.list_datasets = lambda: dishonest_datasets  # type: ignore[method-assign]

        reg = ProviderRegistry()
        with pytest.raises(CapabilityContractError, match="empty operations"):
            reg.register(dishonest)

    def test_registration_rejects_non_list_return_value(self) -> None:
        """list_datasets가 list가 아닌 값을 반환하면 거부한다."""
        from kpubdata.exceptions import CapabilityContractError
        from kpubdata.registry import ProviderRegistry

        bad_shape = FakeAdapter("bad_shape")
        bad_shape.list_datasets = lambda: "not a list"  # type: ignore[method-assign,return-value]

        reg = ProviderRegistry()
        with pytest.raises(CapabilityContractError, match="must return a list"):
            reg.register(bad_shape)

    def test_registration_rejects_non_dataset_ref_entries(self) -> None:
        """list_datasets에 DatasetRef가 아닌 엔트리가 섞이면 거부한다."""
        from kpubdata.exceptions import CapabilityContractError
        from kpubdata.registry import ProviderRegistry

        adapter = FakeAdapter("mixed")
        adapter.list_datasets = lambda: [self._ds("ok"), {"not": "a ref"}]  # type: ignore[method-assign]

        reg = ProviderRegistry()
        with pytest.raises(CapabilityContractError, match="non-DatasetRef entries"):
            reg.register(adapter)

    def test_validate_capabilities_can_be_disabled(self) -> None:
        """validate_capabilities=False면 capability 검증을 건너뛴다(deprecation 경로용)."""
        from kpubdata.registry import ProviderRegistry

        adapter = FakeAdapter("legacy")
        adapter.list_datasets = lambda: [self._ds("a", operations=())]  # type: ignore[method-assign]

        reg = ProviderRegistry()
        reg.register(adapter, validate_capabilities=False)  # 예외가 없어야 한다.
        assert "legacy" in reg

    def test_lazy_registration_also_validates_capabilities_on_materialization(self) -> None:
        """lazy 등록도 materialize 시점에 capability 검증을 거친다."""
        from kpubdata.exceptions import CapabilityContractError
        from kpubdata.registry import ProviderRegistry

        def factory() -> FakeAdapter:
            a = FakeAdapter("lazy_bad")
            a.list_datasets = lambda: [self._ds("a", operations=())]  # type: ignore[method-assign]
            return a

        reg = ProviderRegistry()
        reg.register_lazy("lazy_bad", factory)
        with pytest.raises(CapabilityContractError):
            reg.get("lazy_bad")

    def test_duplicate_name_short_circuits_before_capability_validation(self) -> None:
        """이미 등록된 이름이면 capability 검증(잠재적으로 비싼 catalogue 로드)을 건너뛴다."""
        from kpubdata.registry import ProviderRegistry

        reg = ProviderRegistry()
        reg.register(FakeAdapter("dup_provider"))

        call_count = {"n": 0}
        second = FakeAdapter("dup_provider")

        def expensive_list() -> list[object]:
            call_count["n"] += 1
            return []

        second.list_datasets = expensive_list  # type: ignore[method-assign]

        with pytest.raises(ValueError, match="already registered"):
            reg.register(second)
        # capability 검증이 이름 충돌 검사 뒤에 일어났다면 list_datasets는 호출되지 않아야 한다.
        assert call_count["n"] == 0
