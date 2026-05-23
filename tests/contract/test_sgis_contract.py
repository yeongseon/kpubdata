"""테스트 모듈.

이 파일은 ``tests/contract/test_sgis_contract.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Protocol, cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.transport.http import HttpTransport
from tests.contract.provider_adapter import ProviderAdapterContract


def _fixture_path(name: str) -> Path:
    """
    내부 헬퍼로서 fixture path 처리를 담당한다.

    매개변수:
        name (str): 호출자가 제공하는 입력 값이다.

    반환값:
        Path: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    return Path(__file__).resolve().parents[1] / "fixtures" / "sgis" / name


class _FakeResponse:
    """
    _FakeResponse 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/contract/test_sgis_contract.py`` 모듈 안에서 _FakeResponse의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    def __init__(self, data: bytes, content_type: str = "application/json") -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        매개변수:
            data (bytes): 호출자가 제공하는 입력 값이다.
            content_type (str): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self.headers: dict[str, str] = {"content-type": content_type}
        self.content: bytes = data
        self.text: str = data.decode("utf-8")


class _FixtureTransport:
    """
    _FixtureTransport 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/contract/test_sgis_contract.py`` 모듈 안에서 _FixtureTransport의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__, request.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    def __init__(self, fixture_names: list[str]) -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        매개변수:
            fixture_names (list[str]): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self._responses: list[_FakeResponse] = [
            _FakeResponse(_fixture_path(name).read_bytes()) for name in fixture_names
        ]

    def request(self, _method: str, _url: str, **_kwargs: object) -> _FakeResponse:
        """
        request 동작을 수행한다.

        매개변수:
            _method (str): 호출자가 제공하는 입력 값이다.
            _url (str): 호출자가 제공하는 입력 값이다.
            **_kwargs (object): 호출자가 제공하는 입력 값이다.

        반환값:
            _FakeResponse: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        if not self._responses:
            raise AssertionError("No fixture responses remaining")
        return self._responses.pop(0)


class _FixtureAuthClient:
    """
    _FixtureAuthClient 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/contract/test_sgis_contract.py`` 모듈 안에서 _FixtureAuthClient의 상태와 동작을 함께 관리한다.
    주요 메서드: get_access_token, invalidate.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    def get_access_token(self, *, force_refresh: bool = False) -> str:
        """
        get access token 동작을 수행한다.

        매개변수:
            force_refresh (bool): 호출자가 제공하는 입력 값이다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        _ = force_refresh
        return "contract-token"

    def invalidate(self) -> None:
        """
        invalidate 동작을 수행한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return None


class _SgisAdapterFactory(Protocol):
    """
    _SgisAdapterFactory 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/contract/test_sgis_contract.py`` 모듈 안에서 _SgisAdapterFactory의 상태와 동작을 함께 관리한다.
    주요 메서드: __call__.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    def __call__(
        self,
        *,
        config: KPubDataConfig | None = None,
        transport: HttpTransport | None = None,
        auth_client: object = None,
    ) -> ProviderAdapter: ...


def _build_adapter(fixture_names: list[str]) -> ProviderAdapter:
    """
    내부 헬퍼로서 build adapter 처리를 담당한다.

    매개변수:
        fixture_names (list[str]): 호출자가 제공하는 입력 값이다.

    반환값:
        ProviderAdapter: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    transport = _FixtureTransport(fixture_names)
    config = KPubDataConfig(provider_keys={"sgis": "consumer-key:consumer-secret"})
    adapter_module = import_module("kpubdata.providers.sgis.adapter")
    adapter_class_obj = cast(object, adapter_module.SgisAdapter)
    if not isinstance(adapter_class_obj, type):
        raise AssertionError("SgisAdapter is not a class")
    adapter_class = cast(_SgisAdapterFactory, adapter_class_obj)
    return adapter_class(
        config=config,
        transport=cast(HttpTransport, cast(object, transport)),
        auth_client=_FixtureAuthClient(),
    )


class TestSgisAdapterContract(ProviderAdapterContract):
    """
    TestSgisAdapterContract 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/contract/test_sgis_contract.py`` 모듈 안에서 TestSgisAdapterContract의 상태와 동작을 함께 관리한다.
    주요 메서드: adapter, valid_dataset_key, invalid_dataset_key, sample_dataset, sample_query.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    @pytest.fixture()
    def adapter(self) -> ProviderAdapter:
        """
        adapter 동작을 수행한다.

        반환값:
            ProviderAdapter: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return _build_adapter(["sido_boundary.geojson"] * 5)

    @pytest.fixture()
    def valid_dataset_key(self) -> str:
        """
        valid dataset key 동작을 수행한다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return "boundary.sido"

    @pytest.fixture()
    def invalid_dataset_key(self) -> str:
        """
        invalid dataset key 동작을 수행한다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return "nonexistent_dataset_key_xyz"

    @pytest.fixture()
    def sample_dataset(self, adapter: ProviderAdapter) -> DatasetRef:
        """
        sample dataset 동작을 수행한다.

        매개변수:
            adapter (ProviderAdapter): 호출자가 제공하는 입력 값이다.

        반환값:
            DatasetRef: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return adapter.get_dataset("boundary.sido")

    @pytest.fixture()
    def sample_query(self) -> Query:
        """
        sample query 동작을 수행한다.

        반환값:
            Query: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return Query(filters={"year": "2023", "low_search": 1})

    @pytest.fixture()
    def raw_operation(self) -> tuple[str, dict[str, object]]:
        """
        raw operation 동작을 수행한다.

        반환값:
            tuple[str, dict[str, object]]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return ("list", {"year": "2023", "low_search": 1})
