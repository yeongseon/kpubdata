"""테스트 모듈.

이 파일은 ``tests/unit/providers/seoul/test_adapter.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import Query
from kpubdata.exceptions import AuthError, InvalidRequestError, ProviderResponseError
from kpubdata.providers.seoul.adapter import SeoulAdapter
from kpubdata.transport.http import HttpTransport


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
    return Path(__file__).resolve().parents[3] / "fixtures" / "seoul" / name


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
    return cast(dict[str, object], json.loads(_fixture_path(name).read_text(encoding="utf-8")))


class FakeResponse:
    """
    FakeResponse 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/providers/seoul/test_adapter.py`` 모듈 안에서 FakeResponse의 상태와 동작을 함께 관리한다.
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


class FakeTransport:
    """
    FakeTransport 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/providers/seoul/test_adapter.py`` 모듈 안에서 FakeTransport의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__, request.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    def __init__(self, responses: list[FakeResponse]) -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        매개변수:
            responses (list[FakeResponse]): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self._responses: list[FakeResponse] = list(responses)
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


def _build_adapter(
    responses: list[FakeResponse],
    *,
    config: KPubDataConfig | None = None,
) -> tuple[SeoulAdapter, FakeTransport]:
    """
    내부 헬퍼로서 build adapter 처리를 담당한다.

    매개변수:
        responses (list[FakeResponse]): 호출자가 제공하는 입력 값이다.
        config (KPubDataConfig | None): 호출자가 제공하는 입력 값이다.

    반환값:
        tuple[SeoulAdapter, FakeTransport]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    transport = FakeTransport(responses)
    adapter = SeoulAdapter(
        config=config or KPubDataConfig(provider_keys={"seoul": "test-seoul-key"}),
        transport=cast(HttpTransport, cast(object, transport)),
    )
    return adapter, transport


# test query records builds subway url with path key 테스트가 검증하는 시나리오를 설명한다.
def test_query_records_builds_subway_url_with_path_key() -> None:
    """
    test query records builds subway url with path key 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, transport = _build_adapter(
        [FakeResponse(_load_fixture("subway_realtime_arrival_success.json"))]
    )
    dataset = adapter.get_dataset("subway_realtime_arrival")

    _ = adapter.query_records(dataset, Query(filters={"stationName": "강남"}))

    assert transport.calls[0]["url"] == (
        "http://swopenAPI.seoul.go.kr/api/subway/test-seoul-key/json/"
        "realtimeStationArrival/1/100/%EA%B0%95%EB%82%A8"
    )


# test query records builds bike url with path key 테스트가 검증하는 시나리오를 설명한다.
def test_query_records_builds_bike_url_with_path_key() -> None:
    """
    test query records builds bike url with path key 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, transport = _build_adapter(
        [FakeResponse(_load_fixture("bike_rent_month_success.json"))]
    )
    dataset = adapter.get_dataset("bike_rent_month")

    _ = adapter.query_records(dataset, Query(filters={"RENT_NM": "202401"}, page_size=10))

    assert transport.calls[0]["url"] == (
        "http://openapi.seoul.go.kr:8088/test-seoul-key/json/tbCycleRentUseMonthInfo/1/10/202401"
    )


# test query records parses successful envelope 테스트가 검증하는 시나리오를 설명한다.
def test_query_records_parses_successful_envelope() -> None:
    """
    test query records parses successful envelope 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, _ = _build_adapter(
        [FakeResponse(_load_fixture("subway_realtime_arrival_success.json"))]
    )
    dataset = adapter.get_dataset("subway_realtime_arrival")

    batch = adapter.query_records(
        dataset, Query(filters={"stationName": "강남"}, page=1, page_size=2)
    )

    assert len(batch.items) == 2
    assert batch.items[0]["statnNm"] == "강남"
    assert batch.total_count == 2
    assert batch.next_page is None


# test info 100 raises auth error 테스트가 검증하는 시나리오를 설명한다.
def test_info_100_raises_auth_error() -> None:
    """
    test info 100 raises auth error 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, _ = _build_adapter([FakeResponse(_load_fixture("error_auth.json"))])
    dataset = adapter.get_dataset("subway_realtime_arrival")

    with pytest.raises(AuthError) as exc_info:
        _ = adapter.query_records(dataset, Query(filters={"stationName": "강남"}))

    assert exc_info.value.provider_code == "INFO-100"


# test info 200 returns empty record batch 테스트가 검증하는 시나리오를 설명한다.
def test_info_200_returns_empty_record_batch() -> None:
    """
    test info 200 returns empty record batch 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, _ = _build_adapter([FakeResponse(_load_fixture("empty_response.json"))])
    dataset = adapter.get_dataset("subway_realtime_arrival")

    batch = adapter.query_records(dataset, Query(filters={"stationName": "강남"}))

    assert batch.items == []
    assert batch.total_count is None
    assert batch.next_page is None


# test call raw returns raw payload 테스트가 검증하는 시나리오를 설명한다.
def test_call_raw_returns_raw_payload() -> None:
    """
    test call raw returns raw payload 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    payload = _load_fixture("bike_rent_month_success.json")
    adapter, _ = _build_adapter([FakeResponse(payload)])
    dataset = adapter.get_dataset("bike_rent_month")

    raw = adapter.call_raw(
        dataset,
        "tbCycleRentUseMonthInfo",
        {"RENT_NM": "202401", "page_no": 1, "page_size": 5},
    )

    assert raw == payload


# test pagination uses index window in url 테스트가 검증하는 시나리오를 설명한다.
def test_pagination_uses_index_window_in_url() -> None:
    """
    test pagination uses index window in url 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, transport = _build_adapter(
        [FakeResponse(_load_fixture("bike_rent_month_success.json"))]
    )
    dataset = adapter.get_dataset("bike_rent_month")

    _ = adapter.query_records(dataset, Query(filters={"RENT_NM": "202401"}, page=2, page_size=10))

    assert "/11/20/202401" in cast(str, transport.calls[0]["url"])


# test error code mapping table 테스트가 검증하는 시나리오를 설명한다.
@pytest.mark.parametrize(
    ("code", "expected_exception"),
    [
        ("INFO-300", AuthError),
        ("INFO-400", InvalidRequestError),
        ("INFO-500", ProviderResponseError),
        ("ERROR-300", InvalidRequestError),
        ("ERROR-336", InvalidRequestError),
        ("ERROR-600", ProviderResponseError),
        ("UNKNOWN-999", ProviderResponseError),
    ],
)
def test_error_code_mapping_table(code: str, expected_exception: type[Exception]) -> None:
    """
    test error code mapping table 시나리오를 검증한다.

    매개변수:
        code (str): 호출자가 제공하는 입력 값이다.
        expected_exception (type[Exception]): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    payload: dict[str, object] = {
        "realtimeStationArrival": {
            "list_total_count": 0,
            "RESULT": {"CODE": code, "MESSAGE": f"error: {code}"},
            "row": [],
        }
    }
    adapter, _ = _build_adapter([FakeResponse(payload)])
    dataset = adapter.get_dataset("subway_realtime_arrival")

    with pytest.raises(expected_exception) as exc_info:
        _ = adapter.query_records(dataset, Query(filters={"stationName": "강남"}))

    provider_error = exc_info.value
    assert getattr(provider_error, "provider_code", None) == code


# test config from env injects seoul api key 테스트가 검증하는 시나리오를 설명한다.
def test_config_from_env_injects_seoul_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    test config from env injects seoul api key 시나리오를 검증한다.

    매개변수:
        monkeypatch (pytest.MonkeyPatch): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    monkeypatch.setenv("KPUBDATA_SEOUL_API_KEY", "env-seoul-key")
    adapter, transport = _build_adapter(
        [FakeResponse(_load_fixture("subway_realtime_arrival_success.json"))],
        config=KPubDataConfig.from_env(),
    )
    dataset = adapter.get_dataset("subway_realtime_arrival")

    _ = adapter.query_records(dataset, Query(filters={"stationName": "강남"}))

    assert "/env-seoul-key/json/" in cast(str, transport.calls[0]["url"])


# test page size over 1000 raises invalid request 테스트가 검증하는 시나리오를 설명한다.
def test_page_size_over_1000_raises_invalid_request() -> None:
    """
    test page size over 1000 raises invalid request 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, _ = _build_adapter([])
    dataset = adapter.get_dataset("bike_rent_month")

    with pytest.raises(InvalidRequestError, match="page_size must be <= 1000"):
        _ = adapter.query_records(dataset, Query(filters={"RENT_NM": "202401"}, page_size=1001))


# test query records builds park info url 테스트가 검증하는 시나리오를 설명한다.
def test_query_records_builds_park_info_url() -> None:
    """
    test query records builds park info url 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, transport = _build_adapter([FakeResponse(_load_fixture("park_info.json"))])
    dataset = adapter.get_dataset("park_info")

    _ = adapter.query_records(dataset, Query(page_size=10))

    assert transport.calls[0]["url"] == (
        "http://openapi.seoul.go.kr:8088/test-seoul-key/json/GetParkInfo/1/10"
    )


# test query records parses park info response 테스트가 검증하는 시나리오를 설명한다.
def test_query_records_parses_park_info_response() -> None:
    """
    test query records parses park info response 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, _ = _build_adapter([FakeResponse(_load_fixture("park_info.json"))])
    dataset = adapter.get_dataset("park_info")

    batch = adapter.query_records(dataset, Query(page=1, page_size=10))

    assert len(batch.items) == 1
    assert batch.items[0]["PARKING_NAME"] == "샘플 공영주차장"
    assert batch.total_count == 1
