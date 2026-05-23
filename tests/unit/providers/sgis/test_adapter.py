"""테스트 모듈.

이 파일은 ``tests/unit/providers/sgis/test_adapter.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

import json
from importlib import import_module
from pathlib import Path
from typing import Protocol, cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.exceptions import AuthError, DatasetNotFoundError, InvalidRequestError
from kpubdata.transport.http import HttpTransport


class _SgisAdapterFactory(Protocol):
    """
    _SgisAdapterFactory 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/providers/sgis/test_adapter.py`` 모듈 안에서 _SgisAdapterFactory의 상태와 동작을 함께 관리한다.
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
    return Path(__file__).resolve().parents[3] / "fixtures" / "sgis" / name


def _load_fixture(name: str) -> dict[str, object]:
    """
    내부 헬퍼로서 load fixture 처리를 담당한다.

    매개변수:
        name (str): 호출자가 제공하는 입력 값이다.

    반환값:
        dict[str, object]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    payload = cast(object, json.loads(_fixture_path(name).read_text(encoding="utf-8")))
    if isinstance(payload, dict):
        return cast(dict[str, object], payload)
    raise ValueError(f"Fixture must be object: {name}")


class _FakeResponse:
    """
    _FakeResponse 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/providers/sgis/test_adapter.py`` 모듈 안에서 _FakeResponse의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    def __init__(self, payload: dict[str, object]) -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        매개변수:
            payload (dict[str, object]): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self.headers: dict[str, str] = {"content-type": "application/json"}
        self.text: str = json.dumps(payload, ensure_ascii=False)
        self.content: bytes = self.text.encode("utf-8")


class _FakeTransport:
    """
    _FakeTransport 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/providers/sgis/test_adapter.py`` 모듈 안에서 _FakeTransport의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__, request.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    def __init__(self, responses: list[_FakeResponse]) -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        매개변수:
            responses (list[_FakeResponse]): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self._responses: list[_FakeResponse] = list(responses)
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


class _FakeAuthClient:
    """
    _FakeAuthClient 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/providers/sgis/test_adapter.py`` 모듈 안에서 _FakeAuthClient의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__, get_access_token, invalidate.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    def __init__(self, tokens: list[str]) -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        매개변수:
            tokens (list[str]): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self._tokens: list[str] = list(tokens)
        self.invalidate_count: int = 0
        self.force_refresh_count: int = 0

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
        if force_refresh:
            self.force_refresh_count += 1
        if not self._tokens:
            raise AssertionError("No tokens remaining")
        return self._tokens.pop(0)

    def invalidate(self) -> None:
        """
        invalidate 동작을 수행한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self.invalidate_count += 1


def _build_adapter(
    responses: list[_FakeResponse],
    *,
    auth_client: _FakeAuthClient,
) -> tuple[ProviderAdapter, _FakeTransport]:
    """
    내부 헬퍼로서 build adapter 처리를 담당한다.

    매개변수:
        responses (list[_FakeResponse]): 호출자가 제공하는 입력 값이다.
        auth_client (_FakeAuthClient): 호출자가 제공하는 입력 값이다.

    반환값:
        tuple[ProviderAdapter, _FakeTransport]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    transport = _FakeTransport(responses)
    adapter_module = import_module("kpubdata.providers.sgis.adapter")
    adapter_class_obj = cast(object, adapter_module.SgisAdapter)
    if not isinstance(adapter_class_obj, type):
        raise AssertionError("SgisAdapter is not a class")
    adapter_class = cast(_SgisAdapterFactory, adapter_class_obj)
    adapter = adapter_class(
        config=KPubDataConfig(provider_keys={"sgis": "consumer-key:consumer-secret"}),
        transport=cast(HttpTransport, cast(object, transport)),
        auth_client=auth_client,
    )
    return adapter, transport


# test query records sido parses features 테스트가 검증하는 시나리오를 설명한다.
def test_query_records_sido_parses_features() -> None:
    """
    test query records sido parses features 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    auth_client = _FakeAuthClient(["token-1"])
    adapter, transport = _build_adapter(
        [_FakeResponse(_load_fixture("sido_boundary.geojson"))],
        auth_client=auth_client,
    )
    dataset = adapter.get_dataset("boundary.sido")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert batch.total_count == 2
    assert batch.items[0]["adm_cd"] == "11"
    assert isinstance(batch.items[0]["geometry"], dict)
    request_params = cast(dict[str, str], transport.calls[0]["params"])
    assert request_params["year"] == "2023"
    assert request_params["low_search"] == "1"


# test query records sigungu applies filter overrides 테스트가 검증하는 시나리오를 설명한다.
def test_query_records_sigungu_applies_filter_overrides() -> None:
    """
    test query records sigungu applies filter overrides 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    auth_client = _FakeAuthClient(["token-1"])
    adapter, transport = _build_adapter(
        [_FakeResponse(_load_fixture("sigungu_boundary.geojson"))],
        auth_client=auth_client,
    )
    dataset = adapter.get_dataset("boundary.sigungu")

    batch = adapter.query_records(dataset, Query(filters={"year": "2021", "adm_cd": "11"}))

    assert len(batch.items) == 2
    request_params = cast(dict[str, str], transport.calls[0]["params"])
    assert request_params["year"] == "2021"
    assert request_params["adm_cd"] == "11"
    assert request_params["low_search"] == "2"


# test query records refreshes token on auth error 테스트가 검증하는 시나리오를 설명한다.
def test_query_records_refreshes_token_on_auth_error() -> None:
    """
    test query records refreshes token on auth error 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    auth_client = _FakeAuthClient(["expired-token", "fresh-token"])
    adapter, transport = _build_adapter(
        [
            _FakeResponse(_load_fixture("error_invalid_token.json")),
            _FakeResponse(_load_fixture("sido_boundary.geojson")),
        ],
        auth_client=auth_client,
    )
    dataset = adapter.get_dataset("boundary.sido")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert auth_client.invalidate_count == 1
    assert auth_client.force_refresh_count == 1
    first_params = cast(dict[str, str], transport.calls[0]["params"])
    second_params = cast(dict[str, str], transport.calls[1]["params"])
    assert first_params["accessToken"] == "expired-token"
    assert second_params["accessToken"] == "fresh-token"


# test query records raises auth error when refresh also fails 테스트가 검증하는 시나리오를 설명한다.
def test_query_records_raises_auth_error_when_refresh_also_fails() -> None:
    """
    test query records raises auth error when refresh also fails 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    auth_client = _FakeAuthClient(["expired-token", "fresh-token"])
    adapter, _ = _build_adapter(
        [
            _FakeResponse(_load_fixture("error_invalid_token.json")),
            _FakeResponse(_load_fixture("error_invalid_token.json")),
        ],
        auth_client=auth_client,
    )
    dataset = adapter.get_dataset("boundary.sido")

    with pytest.raises(AuthError):
        _ = adapter.query_records(dataset, Query())


# test call raw list uses dataset endpoint 테스트가 검증하는 시나리오를 설명한다.
def test_call_raw_list_uses_dataset_endpoint() -> None:
    """
    test call raw list uses dataset endpoint 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    auth_client = _FakeAuthClient(["token-1"])
    payload = _load_fixture("sido_boundary.geojson")
    adapter, _ = _build_adapter([_FakeResponse(payload)], auth_client=auth_client)
    dataset = adapter.get_dataset("boundary.sido")

    raw = adapter.call_raw(dataset, "list", {"year": "2022"})

    assert raw == payload


# test call raw rejects full url operation 테스트가 검증하는 시나리오를 설명한다.
def test_call_raw_rejects_full_url_operation() -> None:
    """
    test call raw rejects full url operation 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    auth_client = _FakeAuthClient(["token-1"])
    adapter, _ = _build_adapter(
        [_FakeResponse(_load_fixture("sido_boundary.geojson"))], auth_client=auth_client
    )
    dataset = adapter.get_dataset("boundary.sido")

    with pytest.raises(InvalidRequestError):
        _ = adapter.call_raw(
            dataset, "https://sgisapi.kostat.go.kr/OpenAPI3/boundary/hadmarea.geojson", {}
        )


# test get dataset invalid key raises 테스트가 검증하는 시나리오를 설명한다.
def test_get_dataset_invalid_key_raises() -> None:
    """
    test get dataset invalid key raises 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    auth_client = _FakeAuthClient(["token-1"])
    adapter, _ = _build_adapter(
        [_FakeResponse(_load_fixture("sido_boundary.geojson"))], auth_client=auth_client
    )

    with pytest.raises(DatasetNotFoundError):
        _ = adapter.get_dataset("missing.dataset")


# test dataset ref ids include required catalogue entries 테스트가 검증하는 시나리오를 설명한다.
def test_dataset_ref_ids_include_required_catalogue_entries() -> None:
    """
    test dataset ref ids include required catalogue entries 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    auth_client = _FakeAuthClient(["token-1"])
    adapter, _ = _build_adapter(
        [_FakeResponse(_load_fixture("sido_boundary.geojson"))], auth_client=auth_client
    )

    dataset_ids = {dataset.id for dataset in adapter.list_datasets()}
    assert "sgis.boundary.sido" in dataset_ids
    assert "sgis.boundary.sigungu" in dataset_ids
    assert "sgis.boundary.emd" in dataset_ids


# test schema returns descriptor for boundary dataset 테스트가 검증하는 시나리오를 설명한다.
def test_schema_returns_descriptor_for_boundary_dataset() -> None:
    """
    test schema returns descriptor for boundary dataset 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    auth_client = _FakeAuthClient(["token-1"])
    adapter, _ = _build_adapter(
        [_FakeResponse(_load_fixture("sido_boundary.geojson"))], auth_client=auth_client
    )
    dataset: DatasetRef = adapter.get_dataset("boundary.sido")

    schema = adapter.get_schema(dataset)

    assert schema is not None
    assert len(schema.fields) >= 5
