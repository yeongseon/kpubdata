"""테스트 모듈.

이 파일은 ``tests/contract/test_kosis.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from typing import cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.exceptions import AuthError
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
    return Path(__file__).resolve().parents[1] / "fixtures" / "kosis" / name


def _load_fixture_bytes(name: str) -> bytes:
    """
    내부 헬퍼로서 load fixture bytes 처리를 담당한다.

    매개변수:
        name (str): 호출자가 제공하는 입력 값이다.

    반환값:
        bytes: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    return _fixture_path(name).read_bytes()


class _FakeResponse:
    """
    _FakeResponse 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/contract/test_kosis.py`` 모듈 안에서 _FakeResponse의 상태와 동작을 함께 관리한다.
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

    이 클래스는 ``tests/contract/test_kosis.py`` 모듈 안에서 _FixtureTransport의 상태와 동작을 함께 관리한다.
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
            _FakeResponse(_load_fixture_bytes(name)) for name in fixture_names
        ]
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> _FakeResponse:
        """
        request 동작을 수행한다.

        매개변수:
            method (str): 호출자가 제공하는 입력 값이다.
            url (str): 호출자가 제공하는 입력 값이다.
            **kwargs (object): 호출자가 제공하는 입력 값이다.

        반환값:
            _FakeResponse: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self.calls.append({"method": method, "url": url, **kwargs})
        if not self._responses:
            raise AssertionError("No fixture responses remaining")
        return self._responses.pop(0)


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
    config = KPubDataConfig(provider_keys={"kosis": "test-key"})
    module = import_module("kpubdata.providers.kosis.adapter")
    adapter_class = cast(Callable[..., ProviderAdapter], module.KosisAdapter)
    return adapter_class(
        config=config,
        transport=cast(HttpTransport, cast(object, transport)),
    )


def _build_adapter_with_transport(
    fixture_names: list[str],
) -> tuple[ProviderAdapter, _FixtureTransport]:
    """
    내부 헬퍼로서 build adapter with transport 처리를 담당한다.

    매개변수:
        fixture_names (list[str]): 호출자가 제공하는 입력 값이다.

    반환값:
        tuple[ProviderAdapter, _FixtureTransport]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    transport = _FixtureTransport(fixture_names)
    config = KPubDataConfig(provider_keys={"kosis": "test-key"})
    module = import_module("kpubdata.providers.kosis.adapter")
    adapter_class = cast(Callable[..., ProviderAdapter], module.KosisAdapter)
    adapter = adapter_class(
        config=config,
        transport=cast(HttpTransport, cast(object, transport)),
    )
    return adapter, transport


class TestKosisAdapterContract(ProviderAdapterContract):
    """
    TestKosisAdapterContract 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/contract/test_kosis.py`` 모듈 안에서 TestKosisAdapterContract의 상태와 동작을 함께 관리한다.
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
        return _build_adapter(["success_single_page.json"] * 5)

    @pytest.fixture()
    def valid_dataset_key(self) -> str:
        """
        valid dataset key 동작을 수행한다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return "population_migration"

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
        return adapter.get_dataset("population_migration")

    @pytest.fixture()
    def sample_query(self) -> Query:
        """
        sample query 동작을 수행한다.

        반환값:
            Query: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return Query(start_date="202401", end_date="202401")

    @pytest.fixture()
    def raw_operation(self) -> tuple[str, dict[str, object]]:
        """
        raw operation 동작을 수행한다.

        반환값:
            tuple[str, dict[str, object]]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return ("statisticsParameterData", {})

    # test query records empty array returns empty batch 테스트가 검증하는 시나리오를 설명한다.
    def test_query_records_empty_array_returns_empty_batch(self) -> None:
        """
        test query records empty array returns empty batch 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = _build_adapter(["success_empty.json"])
        dataset = adapter.get_dataset("population_migration")

        batch = adapter.query_records(dataset, Query(start_date="202401", end_date="202401"))

        assert batch.items == []
        assert batch.total_count == 0

    # test query records auth error maps to auth error 테스트가 검증하는 시나리오를 설명한다.
    def test_query_records_auth_error_maps_to_auth_error(self) -> None:
        """
        test query records auth error maps to auth error 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = _build_adapter(["error_auth.json"])
        dataset = adapter.get_dataset("population_migration")

        with pytest.raises(AuthError):
            _ = adapter.query_records(dataset, Query(start_date="202401", end_date="202401"))


# test industrial production query records builds default param url and parses fixture 테스트가 검증하는 시나리오를 설명한다.
def test_industrial_production_query_records_builds_default_param_url_and_parses_fixture() -> None:
    """
    test industrial production query records builds default param url and parses fixture 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, transport = _build_adapter_with_transport(["industrial_production_success.json"])
    dataset = adapter.get_dataset("industrial_production")

    batch = adapter.query_records(dataset, Query(start_date="202401", end_date="202401"))

    request_url = cast(str, transport.calls[0]["url"])
    assert "tblId=DT_1J22003" in request_url
    assert "objL1=T10" in request_url
    assert "itmId=T" in request_url
    assert "prdSe=M" in request_url
    assert "objL2=ALL" not in request_url
    assert len(batch.items) == 1
    assert batch.items[0]["TBL_ID"] == "DT_1J22003"
    assert batch.items[0]["C1"] == "T10"
