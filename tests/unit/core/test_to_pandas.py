"""Tests for RecordBatch.to_pandas() optional pandas integration."""

from __future__ import annotations

from types import ModuleType
from unittest.mock import patch

import pytest

from kpubdata.core.models import DatasetRef, RecordBatch
from kpubdata.core.representation import Representation


def _dataset_ref() -> DatasetRef:
    """
    내부 헬퍼로서 dataset ref 처리를 담당한다.

    반환값:
        DatasetRef: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    return DatasetRef(
        id="mock.test",
        provider="mock",
        dataset_key="test",
        name="Test",
        representation=Representation.API_JSON,
    )


class _FakeDataFrame:
    """
    _FakeDataFrame 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/core/test_to_pandas.py`` 모듈 안에서 _FakeDataFrame의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__, __len__.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    _data: list[dict[str, object]]
    columns: list[str]

    def __init__(self, data: list[dict[str, object]]) -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        매개변수:
            data (list[dict[str, object]]): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self._data = list(data)
        self.columns = list(self._data[0].keys()) if self._data else []

    def __len__(self) -> int:
        """
        내부 헬퍼로서 len 처리를 담당한다.

        반환값:
            int: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        return len(self._data)


class _FakePandasModule(ModuleType):
    """
    _FakePandasModule 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/core/test_to_pandas.py`` 모듈 안에서 _FakePandasModule의 상태와 동작을 함께 관리한다.
    주요 메서드: 없음.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    DataFrame: type[_FakeDataFrame] = _FakeDataFrame


def _fake_pandas_module() -> _FakePandasModule:
    """
    내부 헬퍼로서 fake pandas module 처리를 담당한다.

    반환값:
        _FakePandasModule: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    module = _FakePandasModule("pandas")
    module.DataFrame = _FakeDataFrame
    return module


# test to pandas returns dataframe 테스트가 검증하는 시나리오를 설명한다.
def test_to_pandas_returns_dataframe() -> None:
    """
    test to pandas returns dataframe 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    batch = RecordBatch(
        items=[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 31}],
        dataset=_dataset_ref(),
    )

    fake_pandas = _fake_pandas_module()

    with patch.dict("sys.modules", {"pandas": fake_pandas}):
        df = batch.to_pandas()

    assert isinstance(df, fake_pandas.DataFrame)
    assert list(df.columns) == ["name", "age"]
    assert len(df) == 2


# test to pandas empty items 테스트가 검증하는 시나리오를 설명한다.
def test_to_pandas_empty_items() -> None:
    """
    test to pandas empty items 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    batch = RecordBatch(items=[], dataset=_dataset_ref())

    fake_pandas = _fake_pandas_module()

    with patch.dict("sys.modules", {"pandas": fake_pandas}):
        df = batch.to_pandas()

    assert isinstance(df, fake_pandas.DataFrame)
    assert list(df.columns) == []
    assert len(df) == 0


# test to pandas import error 테스트가 검증하는 시나리오를 설명한다.
def test_to_pandas_import_error() -> None:
    """
    test to pandas import error 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    batch = RecordBatch(items=[{"name": "Alice"}], dataset=_dataset_ref())

    with (
        patch.dict("sys.modules", {"pandas": None}),
        pytest.raises(ImportError, match=r"pandas is required for to_pandas\(\)"),
    ):
        _ = batch.to_pandas()


# test to pandas real pandas if available 테스트가 검증하는 시나리오를 설명한다.
def test_to_pandas_real_pandas_if_available() -> None:
    """
    test to pandas real pandas if available 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    from typing import Protocol, cast

    class _DataFrameLike(Protocol):
        """
        _DataFrameLike 관련 역할을 캡슐화하는 클래스.

        이 클래스는 ``tests/unit/core/test_to_pandas.py`` 모듈 안에서 _DataFrameLike의 상태와 동작을 함께 관리한다.
        주요 메서드: 없음.

        속성 설명:
            생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
        """
        shape: tuple[int, int]
        columns: list[str]

    class _PandasModule(Protocol):
        """
        _PandasModule 관련 역할을 캡슐화하는 클래스.

        이 클래스는 ``tests/unit/core/test_to_pandas.py`` 모듈 안에서 _PandasModule의 상태와 동작을 함께 관리한다.
        주요 메서드: 없음.

        속성 설명:
            생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
        """
        DataFrame: type[_DataFrameLike]

    pd = cast(_PandasModule, pytest.importorskip("pandas"))

    batch = RecordBatch(
        items=[
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 31},
            {"name": "Carol", "age": 32},
        ],
        dataset=_dataset_ref(),
    )

    df = batch.to_pandas()

    assert isinstance(df, pd.DataFrame)
    assert df.shape == (3, 2)
    assert list(df.columns) == ["name", "age"]
