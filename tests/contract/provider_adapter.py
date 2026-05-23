"""테스트 모듈.

이 파일은 ``tests/contract/provider_adapter.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

import pytest

from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.exceptions import DatasetNotFoundError


class ProviderAdapterContract:
    """
    ProviderAdapterContract 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/contract/provider_adapter.py`` 모듈 안에서 ProviderAdapterContract의 상태와 동작을 함께 관리한다.
    주요 메서드: test_isinstance_provider_adapter, test_name_is_nonempty_string, test_list_datasets_returns_list_of_dataset_ref, test_list_datasets_nonempty, test_search_datasets_returns_list_of_dataset_ref.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    # test isinstance provider adapter 테스트가 검증하는 시나리오를 설명한다.
    def test_isinstance_provider_adapter(self, adapter: ProviderAdapter) -> None:
        """
        test isinstance provider adapter 시나리오를 검증한다.

        매개변수:
            adapter (ProviderAdapter): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        assert isinstance(adapter, ProviderAdapter)

    # test name is nonempty string 테스트가 검증하는 시나리오를 설명한다.
    def test_name_is_nonempty_string(self, adapter: ProviderAdapter) -> None:
        """
        test name is nonempty string 시나리오를 검증한다.

        매개변수:
            adapter (ProviderAdapter): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        name = adapter.name
        assert isinstance(name, str)
        assert len(name) > 0

    # test list datasets returns list of dataset ref 테스트가 검증하는 시나리오를 설명한다.
    def test_list_datasets_returns_list_of_dataset_ref(self, adapter: ProviderAdapter) -> None:
        """
        test list datasets returns list of dataset ref 시나리오를 검증한다.

        매개변수:
            adapter (ProviderAdapter): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        datasets = adapter.list_datasets()
        assert isinstance(datasets, list)
        assert all(isinstance(ds, DatasetRef) for ds in datasets)

    # test list datasets nonempty 테스트가 검증하는 시나리오를 설명한다.
    def test_list_datasets_nonempty(self, adapter: ProviderAdapter) -> None:
        """
        test list datasets nonempty 시나리오를 검증한다.

        매개변수:
            adapter (ProviderAdapter): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        datasets = adapter.list_datasets()
        assert len(datasets) > 0

    # test search datasets returns list of dataset ref 테스트가 검증하는 시나리오를 설명한다.
    def test_search_datasets_returns_list_of_dataset_ref(self, adapter: ProviderAdapter) -> None:
        """
        test search datasets returns list of dataset ref 시나리오를 검증한다.

        매개변수:
            adapter (ProviderAdapter): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        result = adapter.search_datasets("test")
        assert isinstance(result, list)
        assert all(isinstance(ds, DatasetRef) for ds in result)

    # test get dataset valid key 테스트가 검증하는 시나리오를 설명한다.
    def test_get_dataset_valid_key(self, adapter: ProviderAdapter, valid_dataset_key: str) -> None:
        """
        test get dataset valid key 시나리오를 검증한다.

        매개변수:
            adapter (ProviderAdapter): 호출자가 제공하는 입력 값이다.
            valid_dataset_key (str): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        dataset = adapter.get_dataset(valid_dataset_key)
        assert isinstance(dataset, DatasetRef)
        assert dataset.dataset_key == valid_dataset_key

    # test get dataset invalid key raises 테스트가 검증하는 시나리오를 설명한다.
    def test_get_dataset_invalid_key_raises(
        self, adapter: ProviderAdapter, invalid_dataset_key: str
    ) -> None:
        """
        test get dataset invalid key raises 시나리오를 검증한다.

        매개변수:
            adapter (ProviderAdapter): 호출자가 제공하는 입력 값이다.
            invalid_dataset_key (str): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        with pytest.raises(DatasetNotFoundError):
            _ = adapter.get_dataset(invalid_dataset_key)

    # test query records returns record batch 테스트가 검증하는 시나리오를 설명한다.
    def test_query_records_returns_record_batch(
        self, adapter: ProviderAdapter, sample_dataset: DatasetRef, sample_query: Query
    ) -> None:
        """
        test query records returns record batch 시나리오를 검증한다.

        매개변수:
            adapter (ProviderAdapter): 호출자가 제공하는 입력 값이다.
            sample_dataset (DatasetRef): 호출자가 제공하는 입력 값이다.
            sample_query (Query): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        batch = adapter.query_records(sample_dataset, sample_query)
        assert isinstance(batch, RecordBatch)
        assert isinstance(batch.items, list)
        assert batch.dataset is sample_dataset

    # test query records items are dicts 테스트가 검증하는 시나리오를 설명한다.
    def test_query_records_items_are_dicts(
        self, adapter: ProviderAdapter, sample_dataset: DatasetRef, sample_query: Query
    ) -> None:
        """
        test query records items are dicts 시나리오를 검증한다.

        매개변수:
            adapter (ProviderAdapter): 호출자가 제공하는 입력 값이다.
            sample_dataset (DatasetRef): 호출자가 제공하는 입력 값이다.
            sample_query (Query): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        batch = adapter.query_records(sample_dataset, sample_query)
        for item in batch.items:
            assert isinstance(item, dict)

    # test get schema returns descriptor or none 테스트가 검증하는 시나리오를 설명한다.
    def test_get_schema_returns_descriptor_or_none(
        self, adapter: ProviderAdapter, sample_dataset: DatasetRef
    ) -> None:
        """
        test get schema returns descriptor or none 시나리오를 검증한다.

        매개변수:
            adapter (ProviderAdapter): 호출자가 제공하는 입력 값이다.
            sample_dataset (DatasetRef): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        schema = adapter.get_schema(sample_dataset)
        assert schema is None or isinstance(schema, SchemaDescriptor)

    # test call raw returns object 테스트가 검증하는 시나리오를 설명한다.
    def test_call_raw_returns_object(
        self,
        adapter: ProviderAdapter,
        sample_dataset: DatasetRef,
        raw_operation: tuple[str, dict[str, object]],
    ) -> None:
        """
        test call raw returns object 시나리오를 검증한다.

        매개변수:
            adapter (ProviderAdapter): 호출자가 제공하는 입력 값이다.
            sample_dataset (DatasetRef): 호출자가 제공하는 입력 값이다.
            raw_operation (tuple[str, dict[str, object]]): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        operation, params = raw_operation
        result = adapter.call_raw(sample_dataset, operation, params)
        assert result is not None

    # test all datasets have provider set 테스트가 검증하는 시나리오를 설명한다.
    def test_all_datasets_have_provider_set(self, adapter: ProviderAdapter) -> None:
        """
        test all datasets have provider set 시나리오를 검증한다.

        매개변수:
            adapter (ProviderAdapter): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        for dataset in adapter.list_datasets():
            assert dataset.provider == adapter.name

    # test all dataset ids prefixed with provider 테스트가 검증하는 시나리오를 설명한다.
    def test_all_dataset_ids_prefixed_with_provider(self, adapter: ProviderAdapter) -> None:
        """
        test all dataset ids prefixed with provider 시나리오를 검증한다.

        매개변수:
            adapter (ProviderAdapter): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        for dataset in adapter.list_datasets():
            assert dataset.id.startswith(f"{adapter.name}.")
