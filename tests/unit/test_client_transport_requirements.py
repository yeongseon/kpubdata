"""테스트 모듈.

이 파일은 ``tests/unit/test_client_transport_requirements.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from kpubdata.client import Client
from kpubdata.core.models import DatasetRef, Query, RecordBatch, SchemaDescriptor
from kpubdata.transport.cache import ResponseCache
from kpubdata.transport.http import HttpTransport, TransportRequirements


class _AdapterWithoutRequirements:
    """
    _AdapterWithoutRequirements 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/test_client_transport_requirements.py`` 모듈 안에서 _AdapterWithoutRequirements의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__, name, list_datasets, search_datasets, get_dataset.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    instances: list[object] = []

    def __init__(self, *, config: object, transport: HttpTransport) -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        매개변수:
            config (object): 호출자가 제공하는 입력 값이다.
            transport (HttpTransport): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self.config: object = config
        self.transport: HttpTransport = transport
        type(self).instances.append(self)

    @property
    def name(self) -> str:
        """
        name 동작을 수행한다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return "dummy"

    def list_datasets(self) -> list[DatasetRef]:
        """
        list datasets 동작을 수행한다.

        반환값:
            list[DatasetRef]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return []

    def search_datasets(self, _text: str) -> list[DatasetRef]:
        """
        search datasets 동작을 수행한다.

        매개변수:
            _text (str): 호출자가 제공하는 입력 값이다.

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

    def query_records(self, dataset: DatasetRef, _query: Query) -> RecordBatch:
        """
        query records 동작을 수행한다.

        매개변수:
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.
            _query (Query): 호출자가 제공하는 입력 값이다.

        반환값:
            RecordBatch: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return RecordBatch(items=[], dataset=dataset)

    def get_schema(self, _dataset: DatasetRef) -> SchemaDescriptor | None:
        """
        get schema 동작을 수행한다.

        매개변수:
            _dataset (DatasetRef): 호출자가 제공하는 입력 값이다.

        반환값:
            SchemaDescriptor | None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return None

    def call_raw(self, _dataset: DatasetRef, _operation: str, _params: dict[str, object]) -> object:
        """
        call raw 동작을 수행한다.

        매개변수:
            _dataset (DatasetRef): 호출자가 제공하는 입력 값이다.
            _operation (str): 호출자가 제공하는 입력 값이다.
            _params (dict[str, object]): 호출자가 제공하는 입력 값이다.

        반환값:
            object: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return None


class _AdapterWithRequirements:
    """
    _AdapterWithRequirements 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/test_client_transport_requirements.py`` 모듈 안에서 _AdapterWithRequirements의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__, name, transport_requirements, list_datasets, search_datasets.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    instances: list[object] = []

    def __init__(self, *, config: object, transport: HttpTransport) -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        매개변수:
            config (object): 호출자가 제공하는 입력 값이다.
            transport (HttpTransport): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self.config: object = config
        self.transport: HttpTransport = transport
        type(self).instances.append(self)

    @property
    def name(self) -> str:
        """
        name 동작을 수행한다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return "dummy"

    @property
    def transport_requirements(self) -> TransportRequirements | None:
        """
        transport requirements 동작을 수행한다.

        반환값:
            TransportRequirements | None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return TransportRequirements(headers={"X-Provider": "dummy"}, verify_ssl=False)

    def list_datasets(self) -> list[DatasetRef]:
        """
        list datasets 동작을 수행한다.

        반환값:
            list[DatasetRef]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return []

    def search_datasets(self, _text: str) -> list[DatasetRef]:
        """
        search datasets 동작을 수행한다.

        매개변수:
            _text (str): 호출자가 제공하는 입력 값이다.

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

    def query_records(self, dataset: DatasetRef, _query: Query) -> RecordBatch:
        """
        query records 동작을 수행한다.

        매개변수:
            dataset (DatasetRef): 호출자가 제공하는 입력 값이다.
            _query (Query): 호출자가 제공하는 입력 값이다.

        반환값:
            RecordBatch: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return RecordBatch(items=[], dataset=dataset)

    def get_schema(self, _dataset: DatasetRef) -> SchemaDescriptor | None:
        """
        get schema 동작을 수행한다.

        매개변수:
            _dataset (DatasetRef): 호출자가 제공하는 입력 값이다.

        반환값:
            SchemaDescriptor | None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return None

    def call_raw(self, _dataset: DatasetRef, _operation: str, _params: dict[str, object]) -> object:
        """
        call raw 동작을 수행한다.

        매개변수:
            _dataset (DatasetRef): 호출자가 제공하는 입력 값이다.
            _operation (str): 호출자가 제공하는 입력 값이다.
            _params (dict[str, object]): 호출자가 제공하는 입력 값이다.

        반환값:
            object: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return None


# test builtin provider without transport requirements uses shared transport 테스트가 검증하는 시나리오를 설명한다.
def test_builtin_provider_without_transport_requirements_uses_shared_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    test builtin provider without transport requirements uses shared transport 시나리오를 검증한다.

    매개변수:
        monkeypatch (pytest.MonkeyPatch): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    _AdapterWithoutRequirements.instances.clear()
    monkeypatch.setattr(
        "kpubdata.client._BUILTIN_PROVIDERS", (("dummy", "dummy.module", "DummyAdapter"),)
    )

    with (
        patch(
            "importlib.import_module",
            return_value=SimpleNamespace(DummyAdapter=_AdapterWithoutRequirements),
        ),
        patch.object(HttpTransport, "with_requirements") as with_requirements,
    ):
        client = Client()
        _ = client.datasets.list()

    with_requirements.assert_not_called()
    assert len(_AdapterWithoutRequirements.instances) == 1


# test builtin provider with transport requirements builds custom transport 테스트가 검증하는 시나리오를 설명한다.
def test_builtin_provider_with_transport_requirements_builds_custom_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    test builtin provider with transport requirements builds custom transport 시나리오를 검증한다.

    매개변수:
        monkeypatch (pytest.MonkeyPatch): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    _AdapterWithRequirements.instances.clear()
    monkeypatch.setattr(
        "kpubdata.client._BUILTIN_PROVIDERS", (("dummy", "dummy.module", "DummyAdapter"),)
    )

    with patch(
        "importlib.import_module",
        return_value=SimpleNamespace(DummyAdapter=_AdapterWithRequirements),
    ):
        client = Client(timeout=12.0, max_retries=7)
        _ = client.datasets.list()

    adapter = _AdapterWithRequirements.instances[-1]
    assert isinstance(adapter, _AdapterWithRequirements)
    assert len(_AdapterWithRequirements.instances) == 2

    with patch("kpubdata.transport.http.httpx.Client") as client_cls:
        _ = adapter.transport.client

    client_cls.assert_called_once_with(
        timeout=12.0,
        headers={"X-Provider": "dummy"},
        follow_redirects=True,
        verify=False,
    )


# test custom transport inherits cache settings 테스트가 검증하는 시나리오를 설명한다.
def test_custom_transport_inherits_cache_settings(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """
    test custom transport inherits cache settings 시나리오를 검증한다.

    매개변수:
        monkeypatch (pytest.MonkeyPatch): 호출자가 제공하는 입력 값이다.
        tmp_path (Path): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    _AdapterWithRequirements.instances.clear()
    monkeypatch.setattr(
        "kpubdata.client._BUILTIN_PROVIDERS", (("dummy", "dummy.module", "DummyAdapter"),)
    )
    cache = ResponseCache(base_dir=tmp_path)

    with patch(
        "importlib.import_module",
        return_value=SimpleNamespace(DummyAdapter=_AdapterWithRequirements),
    ):
        client = Client(cache=cache, cache_ttl_seconds=123)
        _ = client.datasets.list()

    adapter = _AdapterWithRequirements.instances[-1]
    assert isinstance(adapter, _AdapterWithRequirements)
    assert adapter.transport.cache is cache
    assert adapter.transport.cache_ttl_seconds == 123
