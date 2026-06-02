"""테스트 모듈.

이 파일은 ``tests/contract/test_datago.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.capability import Operation, PaginationMode
from kpubdata.core.models import DatasetRef, Query
from kpubdata.providers.datago.adapter import DataGoAdapter
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
    return Path(__file__).resolve().parents[1] / "fixtures" / "datago" / name


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

    이 클래스는 ``tests/contract/test_datago.py`` 모듈 안에서 _FakeResponse의 상태와 동작을 함께 관리한다.
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

    이 클래스는 ``tests/contract/test_datago.py`` 모듈 안에서 _FixtureTransport의 상태와 동작을 함께 관리한다.
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


def _build_adapter(fixture_names: list[str]) -> DataGoAdapter:
    """
    내부 헬퍼로서 build adapter 처리를 담당한다.

    매개변수:
        fixture_names (list[str]): 호출자가 제공하는 입력 값이다.

    반환값:
        DataGoAdapter: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    transport = _FixtureTransport(fixture_names)
    config = KPubDataConfig(provider_keys={"datago": "test-key"})
    return DataGoAdapter(
        config=config,
        transport=cast(HttpTransport, cast(object, transport)),
    )


class TestDataGoAdapterContract(ProviderAdapterContract):
    """
    TestDataGoAdapterContract 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/contract/test_datago.py`` 모듈 안에서 TestDataGoAdapterContract의 상태와 동작을 함께 관리한다.
    주요 메서드: adapter, valid_dataset_key, invalid_dataset_key, sample_dataset, sample_query.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    @pytest.fixture()
    def adapter(self) -> DataGoAdapter:
        """
        adapter 동작을 수행한다.

        반환값:
            DataGoAdapter: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

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
        return "village_fcst"

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
    def sample_dataset(self, adapter: DataGoAdapter) -> DatasetRef:
        """
        sample dataset 동작을 수행한다.

        매개변수:
            adapter (DataGoAdapter): 호출자가 제공하는 입력 값이다.

        반환값:
            DatasetRef: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return adapter.get_dataset("village_fcst")

    @pytest.fixture()
    def sample_query(self) -> Query:
        """
        sample query 동작을 수행한다.

        반환값:
            Query: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return Query()

    @pytest.fixture()
    def raw_operation(self) -> tuple[str, dict[str, object]]:
        """
        raw operation 동작을 수행한다.

        반환값:
            tuple[str, dict[str, object]]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return ("getVilageFcst", {})


# test dur usjnt taboo dataset contract metadata 테스트가 검증하는 시나리오를 설명한다.
def test_dur_usjnt_taboo_dataset_contract_metadata() -> None:
    """
    test dur usjnt taboo dataset contract metadata 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = _build_adapter(["success_dur_usjnt_taboo.json"])

    dataset = adapter.get_dataset("dur_usjnt_taboo")

    assert dataset.id == "datago.dur_usjnt_taboo"
    assert Operation.LIST in dataset.operations
    assert Operation.RAW in dataset.operations
    assert dataset.query_support is not None
    assert dataset.query_support.pagination is PaginationMode.OFFSET


# test dur usjnt taboo dataset contract query and raw 테스트가 검증하는 시나리오를 설명한다.
def test_dur_usjnt_taboo_dataset_contract_query_and_raw() -> None:
    """
    test dur usjnt taboo dataset contract query and raw 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = _build_adapter(["success_dur_usjnt_taboo.json", "success_dur_usjnt_taboo.json"])
    dataset = adapter.get_dataset("dur_usjnt_taboo")

    batch = adapter.query_records(dataset, Query(filters={"itemName": "샘플"}))
    raw = adapter.call_raw(dataset, "getUsjntTabooInfoList03", {"itemName": "샘플"})

    assert batch.dataset is dataset
    assert len(batch.items) == 2
    assert all(isinstance(item, dict) for item in batch.items)
    assert raw is not None


# test dur older adult caution dataset contract metadata 테스트가 검증하는 시나리오를 설명한다.
def test_dur_older_adult_caution_dataset_contract_metadata() -> None:
    """
    test dur older adult caution dataset contract metadata 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = _build_adapter(["success_dur_older_adult_caution.json"])

    dataset = adapter.get_dataset("dur_older_adult_caution")

    assert dataset.id == "datago.dur_older_adult_caution"
    assert Operation.LIST in dataset.operations
    assert Operation.RAW in dataset.operations
    assert dataset.query_support is not None
    assert dataset.query_support.pagination is PaginationMode.OFFSET


# test dur older adult caution dataset contract query and raw 테스트가 검증하는 시나리오를 설명한다.
def test_dur_older_adult_caution_dataset_contract_query_and_raw() -> None:
    """
    test dur older adult caution dataset contract query and raw 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = _build_adapter(
        [
            "success_dur_older_adult_caution.json",
            "success_dur_older_adult_caution.json",
        ]
    )
    dataset = adapter.get_dataset("dur_older_adult_caution")

    batch = adapter.query_records(dataset, Query(filters={"itemName": "샘플"}))
    raw = adapter.call_raw(dataset, "getOdsnAtentInfoList03", {"itemName": "샘플"})

    assert batch.dataset is dataset
    assert len(batch.items) == 2
    assert all(isinstance(item, dict) for item in batch.items)
    assert raw is not None


# test dur product info dataset contract metadata 테스트가 검증하는 시나리오를 설명한다.
def test_dur_product_info_dataset_contract_metadata() -> None:
    """
    test dur product info dataset contract metadata 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = _build_adapter(["success_dur_product_info.json"])

    dataset = adapter.get_dataset("dur_product_info")

    assert dataset.id == "datago.dur_product_info"
    assert Operation.LIST in dataset.operations
    assert Operation.RAW in dataset.operations
    assert dataset.query_support is not None
    assert dataset.query_support.pagination is PaginationMode.OFFSET


# test dur product info dataset contract query and raw 테스트가 검증하는 시나리오를 설명한다.
def test_dur_product_info_dataset_contract_query_and_raw() -> None:
    """
    test dur product info dataset contract query and raw 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = _build_adapter(
        [
            "success_dur_product_info.json",
            "success_dur_product_info.json",
        ]
    )
    dataset = adapter.get_dataset("dur_product_info")

    batch = adapter.query_records(dataset, Query(filters={"itemName": "샘플"}))
    raw = adapter.call_raw(dataset, "getDurPrdlstInfoList03", {"itemName": "샘플"})

    assert batch.dataset is dataset
    assert len(batch.items) == 2
    assert all(isinstance(item, dict) for item in batch.items)
    assert raw is not None


# test dur age taboo dataset contract metadata 테스트가 검증하는 시나리오를 설명한다.
def test_dur_age_taboo_dataset_contract_metadata() -> None:
    """
    test dur age taboo dataset contract metadata 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = _build_adapter(["success_dur_age_taboo.json"])

    dataset = adapter.get_dataset("dur_age_taboo")

    assert dataset.id == "datago.dur_age_taboo"
    assert Operation.LIST in dataset.operations
    assert Operation.RAW in dataset.operations
    assert dataset.query_support is not None
    assert dataset.query_support.pagination is PaginationMode.OFFSET


# test dur age taboo dataset contract query and raw 테스트가 검증하는 시나리오를 설명한다.
def test_dur_age_taboo_dataset_contract_query_and_raw() -> None:
    """
    test dur age taboo dataset contract query and raw 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = _build_adapter(["success_dur_age_taboo.json", "success_dur_age_taboo.json"])
    dataset = adapter.get_dataset("dur_age_taboo")

    batch = adapter.query_records(dataset, Query(filters={"itemName": "샘플"}))
    raw = adapter.call_raw(dataset, "getSpcifyAgrdeTabooInfoList03", {"itemName": "샘플"})

    assert batch.dataset is dataset
    assert len(batch.items) == 2
    assert all(isinstance(item, dict) for item in batch.items)
    assert raw is not None


# test dur dosage caution dataset contract metadata 테스트가 검증하는 시나리오를 설명한다.
def test_dur_dosage_caution_dataset_contract_metadata() -> None:
    """
    test dur dosage caution dataset contract metadata 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = _build_adapter(["success_dur_dosage_caution.json"])

    dataset = adapter.get_dataset("dur_dosage_caution")

    assert dataset.id == "datago.dur_dosage_caution"
    assert Operation.LIST in dataset.operations
    assert Operation.RAW in dataset.operations
    assert dataset.query_support is not None
    assert dataset.query_support.pagination is PaginationMode.OFFSET


# test dur dosage caution dataset contract query and raw 테스트가 검증하는 시나리오를 설명한다.
def test_dur_dosage_caution_dataset_contract_query_and_raw() -> None:
    """
    test dur dosage caution dataset contract query and raw 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = _build_adapter(
        [
            "success_dur_dosage_caution.json",
            "success_dur_dosage_caution.json",
        ]
    )
    dataset = adapter.get_dataset("dur_dosage_caution")

    batch = adapter.query_records(dataset, Query(filters={"itemName": "샘플"}))
    raw = adapter.call_raw(dataset, "getCpctyAtentInfoList03", {"itemName": "샘플"})

    assert batch.dataset is dataset
    assert len(batch.items) == 2
    assert all(isinstance(item, dict) for item in batch.items)
    assert raw is not None


# test dur medication period caution dataset contract metadata 테스트가 검증하는 시나리오를 설명한다.
def test_dur_medication_period_caution_dataset_contract_metadata() -> None:
    """
    test dur medication period caution dataset contract metadata 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = _build_adapter(["success_dur_medication_period_caution.json"])

    dataset = adapter.get_dataset("dur_medication_period_caution")

    assert dataset.id == "datago.dur_medication_period_caution"
    assert Operation.LIST in dataset.operations
    assert Operation.RAW in dataset.operations
    assert dataset.query_support is not None
    assert dataset.query_support.pagination is PaginationMode.OFFSET


# test dur medication period caution dataset contract query and raw 테스트가 검증하는 시나리오를 설명한다.
def test_dur_medication_period_caution_dataset_contract_query_and_raw() -> None:
    """
    test dur medication period caution dataset contract query and raw 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = _build_adapter(
        [
            "success_dur_medication_period_caution.json",
            "success_dur_medication_period_caution.json",
        ]
    )
    dataset = adapter.get_dataset("dur_medication_period_caution")

    batch = adapter.query_records(dataset, Query(filters={"itemName": "샘플"}))
    raw = adapter.call_raw(dataset, "getMdctnPdAtentInfoList03", {"itemName": "샘플"})

    assert batch.dataset is dataset
    assert len(batch.items) == 2
    assert all(isinstance(item, dict) for item in batch.items)
    assert raw is not None


# test dur efficacy duplication dataset contract metadata 테스트가 검증하는 시나리오를 설명한다.
def test_dur_efficacy_duplication_dataset_contract_metadata() -> None:
    """
    test dur efficacy duplication dataset contract metadata 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = _build_adapter(["success_dur_efficacy_duplication.json"])

    dataset = adapter.get_dataset("dur_efficacy_duplication")

    assert dataset.id == "datago.dur_efficacy_duplication"
    assert Operation.LIST in dataset.operations
    assert Operation.RAW in dataset.operations
    assert dataset.query_support is not None
    assert dataset.query_support.pagination is PaginationMode.OFFSET


# test dur efficacy duplication dataset contract query and raw 테스트가 검증하는 시나리오를 설명한다.
def test_dur_efficacy_duplication_dataset_contract_query_and_raw() -> None:
    """
    test dur efficacy duplication dataset contract query and raw 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = _build_adapter(
        [
            "success_dur_efficacy_duplication.json",
            "success_dur_efficacy_duplication.json",
        ]
    )
    dataset = adapter.get_dataset("dur_efficacy_duplication")

    batch = adapter.query_records(dataset, Query(filters={"itemName": "샘플"}))
    raw = adapter.call_raw(dataset, "getEfcyDplctInfoList03", {"itemName": "샘플"})

    assert batch.dataset is dataset
    assert len(batch.items) == 2
    assert all(isinstance(item, dict) for item in batch.items)
    assert raw is not None


# test dur er tablet split caution dataset contract metadata 테스트가 검증하는 시나리오를 설명한다.
def test_dur_er_tablet_split_caution_dataset_contract_metadata() -> None:
    """
    test dur er tablet split caution dataset contract metadata 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = _build_adapter(["success_dur_er_tablet_split_caution.json"])

    dataset = adapter.get_dataset("dur_er_tablet_split_caution")

    assert dataset.id == "datago.dur_er_tablet_split_caution"
    assert Operation.LIST in dataset.operations
    assert Operation.RAW in dataset.operations
    assert dataset.query_support is not None
    assert dataset.query_support.pagination is PaginationMode.OFFSET


# test dur er tablet split caution dataset contract query and raw 테스트가 검증하는 시나리오를 설명한다.
def test_dur_er_tablet_split_caution_dataset_contract_query_and_raw() -> None:
    """
    test dur er tablet split caution dataset contract query and raw 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = _build_adapter(
        [
            "success_dur_er_tablet_split_caution.json",
            "success_dur_er_tablet_split_caution.json",
        ]
    )
    dataset = adapter.get_dataset("dur_er_tablet_split_caution")

    batch = adapter.query_records(dataset, Query(filters={"itemName": "샘플"}))
    raw = adapter.call_raw(
        dataset,
        "getSeobangjeongPartitnAtentInfoList03",
        {"itemName": "샘플"},
    )

    assert batch.dataset is dataset
    assert len(batch.items) == 2
    assert all(isinstance(item, dict) for item in batch.items)
    assert raw is not None


# test dur pregnancy taboo dataset contract metadata 테스트가 검증하는 시나리오를 설명한다.
def test_dur_pregnancy_taboo_dataset_contract_metadata() -> None:
    """
    test dur pregnancy taboo dataset contract metadata 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = _build_adapter(["success_dur_pregnancy_taboo.json"])

    dataset = adapter.get_dataset("dur_pregnancy_taboo")

    assert dataset.id == "datago.dur_pregnancy_taboo"
    assert Operation.LIST in dataset.operations
    assert Operation.RAW in dataset.operations
    assert dataset.query_support is not None
    assert dataset.query_support.pagination is PaginationMode.OFFSET


# test dur pregnancy taboo dataset contract query and raw 테스트가 검증하는 시나리오를 설명한다.
def test_dur_pregnancy_taboo_dataset_contract_query_and_raw() -> None:
    """
    test dur pregnancy taboo dataset contract query and raw 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = _build_adapter(
        [
            "success_dur_pregnancy_taboo.json",
            "success_dur_pregnancy_taboo.json",
        ]
    )
    dataset = adapter.get_dataset("dur_pregnancy_taboo")

    batch = adapter.query_records(dataset, Query(filters={"itemName": "샘플"}))
    raw = adapter.call_raw(dataset, "getPwnmTabooInfoList03", {"itemName": "샘플"})

    assert batch.dataset is dataset
    assert len(batch.items) == 2
    assert all(isinstance(item, dict) for item in batch.items)
    assert raw is not None


# test agri price dataset contract metadata 테스트가 검증하는 시나리오를 설명한다.
def test_agri_price_dataset_contract_metadata() -> None:
    """
    test agri price dataset contract metadata 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = _build_adapter(["success_agri_price.json"])

    dataset = adapter.get_dataset("agri_price")

    assert dataset.id == "datago.agri_price"
    assert Operation.LIST in dataset.operations
    assert Operation.RAW in dataset.operations
    assert dataset.query_support is not None
    assert dataset.query_support.pagination is PaginationMode.OFFSET


# test agri price dataset contract query and raw 테스트가 검증하는 시나리오를 설명한다.
def test_agri_price_dataset_contract_query_and_raw() -> None:
    """
    test agri price dataset contract query and raw 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter = _build_adapter(
        [
            "success_agri_price.json",
            "success_agri_price.json",
        ]
    )
    dataset = adapter.get_dataset("agri_price")

    batch = adapter.query_records(dataset, Query(filters={"cond[exmn_ymd::GTE]": "20240101"}))
    raw = adapter.call_raw(dataset, "price", {"cond[exmn_ymd::GTE]": "20240101"})

    assert batch.dataset is dataset
    assert len(batch.items) == 3
    assert all(isinstance(item, dict) for item in batch.items)
    assert raw is not None


def test_subway_passengers_dataset_contract_metadata() -> None:
    adapter = _build_adapter(["success_subway_passengers.json"])

    dataset = adapter.get_dataset("subway_passengers")

    assert dataset.id == "datago.subway_passengers"
    assert Operation.LIST in dataset.operations
    assert Operation.RAW in dataset.operations
    assert dataset.query_support is not None
    assert dataset.query_support.pagination is PaginationMode.OFFSET


def test_subway_passengers_dataset_contract_query_and_raw() -> None:
    adapter = _build_adapter(["success_subway_passengers.json", "success_subway_passengers.json"])
    dataset = adapter.get_dataset("subway_passengers")

    batch = adapter.query_records(dataset, Query(filters={"pasngYmd": "20260521"}))
    raw = adapter.call_raw(dataset, "getStnPsgr", {"pasngYmd": "20260521"})

    assert batch.dataset is dataset
    assert len(batch.items) == 2
    assert all(isinstance(item, dict) for item in batch.items)
    assert raw is not None


def test_mid_fcst_dataset_contract_metadata() -> None:
    adapter = _build_adapter(["success_mid_fcst.json"])

    dataset = adapter.get_dataset("mid_fcst")

    assert dataset.id == "datago.mid_fcst"
    assert Operation.LIST in dataset.operations
    assert Operation.RAW in dataset.operations
    assert dataset.query_support is not None
    assert dataset.query_support.pagination is PaginationMode.OFFSET


def test_mid_fcst_dataset_contract_query_and_raw() -> None:
    adapter = _build_adapter(["success_mid_fcst.json", "success_mid_fcst.json"])
    dataset = adapter.get_dataset("mid_fcst")

    batch = adapter.query_records(dataset, Query(filters={"stnId": "108", "tmFc": "2026052206"}))
    raw = adapter.call_raw(dataset, "getMidFcst", {"stnId": "108", "tmFc": "2026052206"})

    assert batch.dataset is dataset
    assert len(batch.items) == 1
    assert all(isinstance(item, dict) for item in batch.items)
    assert raw is not None


def test_mid_land_fcst_dataset_contract_metadata() -> None:
    adapter = _build_adapter(["success_mid_land_fcst.json"])

    dataset = adapter.get_dataset("mid_land_fcst")

    assert dataset.id == "datago.mid_land_fcst"
    assert Operation.LIST in dataset.operations
    assert Operation.RAW in dataset.operations
    assert dataset.query_support is not None
    assert dataset.query_support.pagination is PaginationMode.OFFSET


def test_mid_land_fcst_dataset_contract_query_and_raw() -> None:
    adapter = _build_adapter(["success_mid_land_fcst.json", "success_mid_land_fcst.json"])
    dataset = adapter.get_dataset("mid_land_fcst")

    batch = adapter.query_records(
        dataset, Query(filters={"regId": "11B00000", "tmFc": "2026052206"})
    )
    raw = adapter.call_raw(dataset, "getMidLandFcst", {"regId": "11B00000", "tmFc": "2026052206"})

    assert batch.dataset is dataset
    assert len(batch.items) == 1
    assert all(isinstance(item, dict) for item in batch.items)
    assert raw is not None


def test_mid_ta_dataset_contract_metadata() -> None:
    adapter = _build_adapter(["success_mid_ta.json"])

    dataset = adapter.get_dataset("mid_ta")

    assert dataset.id == "datago.mid_ta"
    assert Operation.LIST in dataset.operations
    assert Operation.RAW in dataset.operations
    assert dataset.query_support is not None
    assert dataset.query_support.pagination is PaginationMode.OFFSET


def test_mid_ta_dataset_contract_query_and_raw() -> None:
    adapter = _build_adapter(["success_mid_ta.json", "success_mid_ta.json"])
    dataset = adapter.get_dataset("mid_ta")

    batch = adapter.query_records(
        dataset, Query(filters={"regId": "11D20501", "tmFc": "2026052206"})
    )
    raw = adapter.call_raw(dataset, "getMidTa", {"regId": "11D20501", "tmFc": "2026052206"})

    assert batch.dataset is dataset
    assert len(batch.items) == 1
    assert all(isinstance(item, dict) for item in batch.items)
    assert raw is not None


def test_mid_sea_fcst_dataset_contract_metadata() -> None:
    adapter = _build_adapter(["success_mid_sea_fcst.json"])

    dataset = adapter.get_dataset("mid_sea_fcst")

    assert dataset.id == "datago.mid_sea_fcst"
    assert Operation.LIST in dataset.operations
    assert Operation.RAW in dataset.operations
    assert dataset.query_support is not None
    assert dataset.query_support.pagination is PaginationMode.OFFSET


def test_mid_sea_fcst_dataset_contract_query_and_raw() -> None:
    adapter = _build_adapter(["success_mid_sea_fcst.json", "success_mid_sea_fcst.json"])
    dataset = adapter.get_dataset("mid_sea_fcst")

    batch = adapter.query_records(
        dataset, Query(filters={"regId": "12A20000", "tmFc": "2026052206"})
    )
    raw = adapter.call_raw(dataset, "getMidSeaFcst", {"regId": "12A20000", "tmFc": "2026052206"})

    assert batch.dataset is dataset
    assert len(batch.items) == 1
    assert all(isinstance(item, dict) for item in batch.items)
    assert raw is not None
