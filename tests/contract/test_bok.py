"""테스트 모듈.

이 파일은 ``tests/contract/test_bok.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
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
    return Path(__file__).resolve().parents[1] / "fixtures" / "bok" / name


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

    이 클래스는 ``tests/contract/test_bok.py`` 모듈 안에서 _FakeResponse의 상태와 동작을 함께 관리한다.
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

    이 클래스는 ``tests/contract/test_bok.py`` 모듈 안에서 _FixtureTransport의 상태와 동작을 함께 관리한다.
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


class _AdapterFactory(Protocol):
    """
    _AdapterFactory 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/contract/test_bok.py`` 모듈 안에서 _AdapterFactory의 상태와 동작을 함께 관리한다.
    주요 메서드: __call__.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    def __call__(
        self,
        *,
        config: KPubDataConfig | None = None,
        transport: HttpTransport | None = None,
    ) -> ProviderAdapter: ...


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
    config = KPubDataConfig(provider_keys={"bok": "test-key"})
    adapter_module = import_module("kpubdata.providers.bok.adapter")
    adapter_class_obj = cast(object, adapter_module.BokAdapter)
    if not isinstance(adapter_class_obj, type):
        raise AssertionError("BokAdapter is not a class")
    adapter_class = cast(_AdapterFactory, adapter_class_obj)
    adapter_obj = adapter_class(
        config=config,
        transport=cast(HttpTransport, cast(object, transport)),
    )
    return adapter_obj, transport


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
    adapter, _ = _build_adapter_with_transport(fixture_names)
    return adapter


class TestBokAdapterContract(ProviderAdapterContract):
    """
    TestBokAdapterContract 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/contract/test_bok.py`` 모듈 안에서 TestBokAdapterContract의 상태와 동작을 함께 관리한다.
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
        return "base_rate"

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
        return adapter.get_dataset("base_rate")

    @pytest.fixture()
    def sample_query(self) -> Query:
        """
        sample query 동작을 수행한다.

        반환값:
            Query: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return Query(start_date="202401", end_date="202403")

    @pytest.fixture()
    def raw_operation(self) -> tuple[str, dict[str, object]]:
        """
        raw operation 동작을 수행한다.

        반환값:
            tuple[str, dict[str, object]]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return (
            "StatisticSearch",
            {"start_date": "202401", "end_date": "202403", "frequency": "M"},
        )


# test usd krw query records builds daily ecos url and parses fixture 테스트가 검증하는 시나리오를 설명한다.
def test_usd_krw_query_records_builds_daily_ecos_url_and_parses_fixture() -> None:
    """
    test usd krw query records builds daily ecos url and parses fixture 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, transport = _build_adapter_with_transport(["usd_krw_success.json"])
    dataset = adapter.get_dataset("usd_krw")

    batch = adapter.query_records(
        dataset,
        Query(
            start_date="20240101",
            end_date="20240105",
            extra={"frequency": "D"},
        ),
    )

    request_url = cast(str, transport.calls[0]["url"])
    assert "/StatisticSearch/" in request_url
    assert "731Y003/D/20240101/20240105/0000003" in request_url
    assert len(batch.items) == 4
    assert [item["TIME"] for item in batch.items] == [
        "20240102",
        "20240103",
        "20240104",
        "20240105",
    ]


# test bond yield 3y query records builds daily ecos url and parses fixture 테스트가 검증하는 시나리오를 설명한다.
def test_bond_yield_3y_query_records_builds_daily_ecos_url_and_parses_fixture() -> None:
    """
    test bond yield 3y query records builds daily ecos url and parses fixture 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, transport = _build_adapter_with_transport(["bond_yield_3y_success.json"])
    dataset = adapter.get_dataset("bond_yield_3y")

    batch = adapter.query_records(
        dataset,
        Query(
            start_date="20240102",
            end_date="20240108",
            extra={"frequency": "D"},
        ),
    )

    request_url = cast(str, transport.calls[0]["url"])
    assert "/StatisticSearch/" in request_url
    assert "817Y002/D/20240102/20240108/010200000" in request_url
    assert len(batch.items) == 5
    assert [item["TIME"] for item in batch.items] == [
        "20240102",
        "20240103",
        "20240104",
        "20240105",
        "20240108",
    ]


# test money supply query records builds monthly ecos url and parses fixture 테스트가 검증하는 시나리오를 설명한다.
def test_money_supply_query_records_builds_monthly_ecos_url_and_parses_fixture() -> None:
    """
    test money supply query records builds monthly ecos url and parses fixture 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, transport = _build_adapter_with_transport(["money_supply_success.json"])
    dataset = adapter.get_dataset("money_supply")

    batch = adapter.query_records(
        dataset,
        Query(
            start_date="200301",
            end_date="200303",
            extra={"frequency": "M"},
        ),
    )

    request_url = cast(str, transport.calls[0]["url"])
    assert "/StatisticSearch/" in request_url
    assert "101Y003/M/200301/200303/BBHS00" in request_url
    assert len(batch.items) == 3
    assert [item["TIME"] for item in batch.items] == ["200301", "200302", "200303"]
    assert {item["STAT_CODE"] for item in batch.items} == {"101Y003"}
    assert {item["ITEM_CODE1"] for item in batch.items} == {"BBHS00"}
