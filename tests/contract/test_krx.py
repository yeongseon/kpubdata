"""테스트 모듈.

이 파일은 ``tests/contract/test_krx.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pytest

from kpubdata import Client
from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.providers.krx.adapter import KrxAdapter
from kpubdata.providers.manifest import BUILTIN_PROVIDERS
from tests.contract.provider_adapter import ProviderAdapterContract


def _index_frame() -> pd.DataFrame:
    """
    내부 헬퍼로서 index frame 처리를 담당한다.

    반환값:
        pd.DataFrame: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    return pd.DataFrame(
        {
            "시가": [2650.0],
            "고가": [2675.0],
            "저가": [2641.0],
            "종가": [2669.0],
            "거래량": [410000000],
            "거래대금": [8100000000000],
            "상장시가총액": [2100000000000],
        },
        index=pd.DatetimeIndex(["2024-01-02"], name="날짜"),
    )


def _build_adapter() -> KrxAdapter:
    """
    내부 헬퍼로서 build adapter 처리를 담당한다.

    반환값:
        KrxAdapter: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    adapter = KrxAdapter(config=KPubDataConfig())
    adapter._pykrx = SimpleNamespace(
        stock=SimpleNamespace(
            get_index_ohlcv=lambda *_args: _index_frame(),
            get_market_trading_value_by_date=lambda *_args, **_kwargs: pd.DataFrame(
                {
                    "개인": [100],
                    "기관합계": [50],
                    "외국인합계": [30],
                    "기타법인": [20],
                    "전체": [0],
                },
                index=pd.DatetimeIndex(["2024-01-02"], name="날짜"),
            ),
            get_market_fundamental=lambda *_args, **_kwargs: pd.DataFrame(
                {
                    "PER": [150.0],
                    "PBR": [1.5],
                    "DIV": [3.0],
                    "EPS": [1500.0],
                    "BPS": [6000.0],
                },
                index=pd.DatetimeIndex(["2024-01-02"], name="날짜"),
            ),
        )
    )
    return adapter


class TestKrxAdapterContract(ProviderAdapterContract):
    """
    TestKrxAdapterContract 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/contract/test_krx.py`` 모듈 안에서 TestKrxAdapterContract의 상태와 동작을 함께 관리한다.
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
        return _build_adapter()

    @pytest.fixture()
    def valid_dataset_key(self) -> str:
        """
        valid dataset key 동작을 수행한다.

        반환값:
            str: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return "kospi_index"

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
        return adapter.get_dataset("kospi_index")

    @pytest.fixture()
    def sample_query(self) -> Query:
        """
        sample query 동작을 수행한다.

        반환값:
            Query: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return Query(start_date="20240102", end_date="20240102")

    @pytest.fixture()
    def raw_operation(self) -> tuple[str, dict[str, object]]:
        """
        raw operation 동작을 수행한다.

        반환값:
            tuple[str, dict[str, object]]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return ("list", {"start_date": "20240102", "end_date": "20240102"})


# test krx provider is registered in builtin manifest 테스트가 검증하는 시나리오를 설명한다.
def test_krx_provider_is_registered_in_builtin_manifest() -> None:
    """
    test krx provider is registered in builtin manifest 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    assert ("krx", "kpubdata.providers.krx", "KrxAdapter") in BUILTIN_PROVIDERS


# test client from env lists three krx datasets 테스트가 검증하는 시나리오를 설명한다.
def test_client_from_env_lists_three_krx_datasets(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    test client from env lists three krx datasets 시나리오를 검증한다.

    매개변수:
        monkeypatch (pytest.MonkeyPatch): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    monkeypatch.delenv("KPUBDATA_KRX_API_KEY", raising=False)
    client = Client.from_env()

    datasets = client.datasets.list(provider="krx")

    assert [dataset.id for dataset in datasets] == [
        "krx.kospi_index",
        "krx.investor_flow",
        "krx.market_valuation",
    ]


# test client search finds krx datasets by description 테스트가 검증하는 시나리오를 설명한다.
def test_client_search_finds_krx_datasets_by_description() -> None:
    """
    test client search finds krx datasets by description 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    client = Client()

    matches = client.datasets.search("investor", provider="krx")

    assert any(dataset.id == "krx.investor_flow" for dataset in matches)


# test client can resolve krx schema 테스트가 검증하는 시나리오를 설명한다.
def test_client_can_resolve_krx_schema() -> None:
    """
    test client can resolve krx schema 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    client = Client()
    schema = client.dataset("krx.market_valuation").schema()

    assert schema is not None
    assert [field.name for field in schema.fields] == [
        "date",
        "market",
        "per",
        "pbr",
        "dividend_yield",
        "eps",
        "bps",
    ]


# test krx adapter declares authless provider 테스트가 검증하는 시나리오를 설명한다.
def test_krx_adapter_declares_authless_provider() -> None:
    """
    test krx adapter declares authless provider 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    assert KrxAdapter(config=KPubDataConfig()).requires_api_key is False


# test client iter authenticated providers excludes krx and includes bok 테스트가 검증하는 시나리오를 설명한다.
def test_client_iter_authenticated_providers_excludes_krx_and_includes_bok() -> None:
    """
    test client iter authenticated providers excludes krx and includes bok 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    client = Client()

    provider_names = {adapter.name for adapter in client.iter_authenticated_providers()}

    assert "krx" not in provider_names
    assert "bok" in provider_names
