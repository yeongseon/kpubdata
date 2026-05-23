"""테스트 모듈.

이 파일은 ``tests/unit/providers/datago/conftest.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef
from kpubdata.providers.datago.adapter import DataGoAdapter
from kpubdata.transport.http import HttpTransport


def fixture_path(name: str) -> Path:
    """
    fixture path 동작을 수행한다.

    매개변수:
        name (str): 호출자가 제공하는 입력 값이다.

    반환값:
        Path: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    return Path(__file__).resolve().parents[3] / "fixtures" / "datago" / name


def load_json_fixture(name: str) -> dict[str, object]:
    """
    load json fixture 동작을 수행한다.

    매개변수:
        name (str): 호출자가 제공하는 입력 값이다.

    반환값:
        dict[str, object]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    payload = cast(object, json.loads(fixture_path(name).read_text(encoding="utf-8")))
    if isinstance(payload, dict):
        return cast(dict[str, object], payload)
    raise ValueError(f"Fixture must contain a JSON object: {name}")


def load_fixture_bytes(name: str) -> bytes:
    """
    load fixture bytes 동작을 수행한다.

    매개변수:
        name (str): 호출자가 제공하는 입력 값이다.

    반환값:
        bytes: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    return fixture_path(name).read_bytes()


class FakeResponse:
    """
    FakeResponse 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/providers/datago/conftest.py`` 모듈 안에서 FakeResponse의 상태와 동작을 함께 관리한다.
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


class FixtureTransport:
    """
    FixtureTransport 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/providers/datago/conftest.py`` 모듈 안에서 FixtureTransport의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__, request.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    def __init__(self, fixture_names: list[str], content_type: str = "application/json") -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        매개변수:
            fixture_names (list[str]): 호출자가 제공하는 입력 값이다.
            content_type (str): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self._responses: list[FakeResponse] = [
            FakeResponse(load_fixture_bytes(name), content_type=content_type)
            for name in fixture_names
        ]
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> FakeResponse:
        """
        request 동작을 수행한다.

        매개변수:
            method (str): 호출자가 제공하는 입력 값이다.
            url (str): 호출자가 제공하는 입력 값이다.
            **kwargs (object): 호출자가 제공하는 입력 값이다.

        반환값:
            FakeResponse: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self.calls.append({"method": method, "url": url, **kwargs})
        if not self._responses:
            raise AssertionError("No fixture responses remaining")
        return self._responses.pop(0)


@pytest.fixture
def configured_adapter() -> Callable[
    [list[str], str], tuple[DataGoAdapter, DatasetRef, FixtureTransport]
]:
    """
    configured adapter 동작을 수행한다.

    반환값:
        Callable[[list[str], str], tuple[DataGoAdapter, DatasetRef, FixtureTransport]]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """

    def _build(
        fixture_names: list[str],
        content_type: str = "application/json",
    ) -> tuple[DataGoAdapter, DatasetRef, FixtureTransport]:
        """
        내부 헬퍼로서 build 처리를 담당한다.

        매개변수:
            fixture_names (list[str]): 호출자가 제공하는 입력 값이다.
            content_type (str): 호출자가 제공하는 입력 값이다.

        반환값:
            tuple[DataGoAdapter, DatasetRef, FixtureTransport]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        transport = FixtureTransport(fixture_names=fixture_names, content_type=content_type)
        config = KPubDataConfig(provider_keys={"datago": "test-key"})
        adapter = DataGoAdapter(
            config=config,
            transport=cast(HttpTransport, cast(object, transport)),
        )
        dataset = adapter.get_dataset("village_fcst")
        return adapter, dataset, transport

    return _build
