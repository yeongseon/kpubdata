"""테스트 모듈.

이 파일은 ``tests/unit/providers/datago/test_fixtures.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

from typing import Protocol, cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.exceptions import (
    AuthError,
    InvalidRequestError,
    RateLimitError,
    ServiceUnavailableError,
)
from kpubdata.providers.datago.adapter import DataGoAdapter
from kpubdata.transport.http import HttpTransport

from .conftest import FixtureTransport, load_fixture_bytes, load_json_fixture


class AdapterFactory(Protocol):
    """
    AdapterFactory 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/providers/datago/test_fixtures.py`` 모듈 안에서 AdapterFactory의 상태와 동작을 함께 관리한다.
    주요 메서드: __call__.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    def __call__(
        self,
        fixture_names: list[str],
        content_type: str = "application/json",
    ) -> tuple[DataGoAdapter, DatasetRef, FixtureTransport]: ...


def _build_real_estate_adapter(
    fixture_name: str, dataset_key: str
) -> tuple[DataGoAdapter, DatasetRef]:
    """
    내부 헬퍼로서 build real estate adapter 처리를 담당한다.

    매개변수:
        fixture_name (str): 호출자가 제공하는 입력 값이다.
        dataset_key (str): 호출자가 제공하는 입력 값이다.

    반환값:
        tuple[DataGoAdapter, DatasetRef]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    data = load_fixture_bytes(fixture_name)

    class _FakeResponse:
        """
        _FakeResponse 관련 역할을 캡슐화하는 클래스.

        이 클래스는 ``tests/unit/providers/datago/test_fixtures.py`` 모듈 안에서 _FakeResponse의 상태와 동작을 함께 관리한다.
        주요 메서드: __init__.

        속성 설명:
            생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
        """

        def __init__(self) -> None:
            """
            인스턴스가 사용할 내부 상태를 초기화한다.

            반환값:
                None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

            예외:
                구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
            """
            self.headers: dict[str, str] = {"content-type": "application/json"}
            self.content: bytes = data
            self.text: str = data.decode("utf-8")

    class _FakeTransport:
        """
        _FakeTransport 관련 역할을 캡슐화하는 클래스.

        이 클래스는 ``tests/unit/providers/datago/test_fixtures.py`` 모듈 안에서 _FakeTransport의 상태와 동작을 함께 관리한다.
        주요 메서드: request.

        속성 설명:
            생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
        """

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
            return _FakeResponse()

    config = KPubDataConfig(provider_keys={"datago": "test-key"})
    adapter = DataGoAdapter(
        config=config,
        transport=cast(HttpTransport, cast(object, _FakeTransport())),
    )
    dataset = adapter.get_dataset(dataset_key)
    return adapter, dataset


# test fixture bus arrival v2 call raw returns full envelope 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_bus_arrival_v2_call_raw_returns_full_envelope() -> None:
    """
    test fixture bus arrival v2 call raw returns full envelope 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter("bus_arrival_v2.json", "bus_arrival")
    expected = load_json_fixture("bus_arrival_v2.json")

    payload = adapter.call_raw(dataset, "getBusArrivalListv2", {"stationId": "228000704"})

    assert payload == expected
    payload_dict = cast(dict[str, object], payload)
    response = payload_dict["response"]
    assert isinstance(response, dict)
    assert "msgHeader" in response
    assert "msgBody" in response


# test fixture bus arrival v2 list normalizes msg body list 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_bus_arrival_v2_list_normalizes_msg_body_list() -> None:
    """
    test fixture bus arrival v2 list normalizes msg body list 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter("bus_arrival_v2.json", "bus_arrival")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 1
    assert batch.items[0]["routeId"] == 200000333
    assert batch.items[0]["stationId"] == 228000704
    assert batch.total_count is None


# test fixture dur usjnt taboo parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_dur_usjnt_taboo_parses() -> None:
    """
    test fixture dur usjnt taboo parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter("success_dur_usjnt_taboo.json", "dur_usjnt_taboo")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert batch.items[0]["ITEM_NAME"] == "샘플정A"
    assert "MIXTURE_ITEM_NAME" in batch.items[0]
    assert "PROHBT_CONTENT" in batch.items[0]
    assert batch.total_count == 2


# test fixture dur usjnt taboo call raw returns full envelope 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_dur_usjnt_taboo_call_raw_returns_full_envelope() -> None:
    """
    test fixture dur usjnt taboo call raw returns full envelope 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter("success_dur_usjnt_taboo.json", "dur_usjnt_taboo")
    expected = load_json_fixture("success_dur_usjnt_taboo.json")

    payload = adapter.call_raw(dataset, "getUsjntTabooInfoList03", {"itemName": "샘플"})

    assert payload == expected
    payload_dict = cast(dict[str, object], payload)
    response = payload_dict["response"]
    assert isinstance(response, dict)
    assert "header" in response
    assert "body" in response


# test fixture dur older adult caution parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_dur_older_adult_caution_parses() -> None:
    """
    test fixture dur older adult caution parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter(
        "success_dur_older_adult_caution.json", "dur_older_adult_caution"
    )

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert batch.items[0]["ITEM_NAME"] == "샘플정E"
    assert "CLASS_NAME" in batch.items[0]
    assert "ODSN_ATENT_CN" in batch.items[0]
    assert batch.total_count == 2


# test fixture dur older adult caution call raw returns full envelope 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_dur_older_adult_caution_call_raw_returns_full_envelope() -> None:
    """
    test fixture dur older adult caution call raw returns full envelope 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter(
        "success_dur_older_adult_caution.json", "dur_older_adult_caution"
    )
    expected = load_json_fixture("success_dur_older_adult_caution.json")

    payload = adapter.call_raw(dataset, "getOdsnAtentInfoList03", {"itemName": "샘플"})

    assert payload == expected
    payload_dict = cast(dict[str, object], payload)
    response = payload_dict["response"]
    assert isinstance(response, dict)
    assert "header" in response
    assert "body" in response


# test fixture dur product info parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_dur_product_info_parses() -> None:
    """
    test fixture dur product info parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter(
        "success_dur_product_info.json", "dur_product_info"
    )

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert batch.items[0]["ITEM_NAME"] == "샘플정G"
    assert "ETC_OTC_CODE" in batch.items[0]
    assert "CHART" in batch.items[0]
    assert batch.total_count == 2


# test fixture dur product info call raw returns full envelope 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_dur_product_info_call_raw_returns_full_envelope() -> None:
    """
    test fixture dur product info call raw returns full envelope 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter(
        "success_dur_product_info.json", "dur_product_info"
    )
    expected = load_json_fixture("success_dur_product_info.json")

    payload = adapter.call_raw(dataset, "getDurPrdlstInfoList03", {"itemName": "샘플"})

    assert payload == expected
    payload_dict = cast(dict[str, object], payload)
    response = payload_dict["response"]
    assert isinstance(response, dict)
    assert "header" in response
    assert "body" in response


# test fixture single page 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_single_page(configured_adapter: AdapterFactory) -> None:
    """
    test fixture single page 시나리오를 검증한다.

    매개변수:
        configured_adapter (AdapterFactory): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset, _ = configured_adapter(["success_single_page.json"])

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 3
    assert batch.total_count == 3
    assert batch.next_page is None
    assert isinstance(batch.raw, dict)


# test fixture multi page pagination 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_multi_page_pagination(configured_adapter: AdapterFactory) -> None:
    """
    test fixture multi page pagination 시나리오를 검증한다.

    매개변수:
        configured_adapter (AdapterFactory): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset, _ = configured_adapter(
        ["success_multi_page_1.json", "success_multi_page_2.json"]
    )

    batch = adapter.query_records(dataset, Query(page_size=2))

    assert len(batch.items) == 2
    assert [item["stationName"] for item in batch.items] == ["종로구", "강남구"]
    assert batch.next_page == 2


# test fixture single item normalization 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_single_item_normalization(configured_adapter: AdapterFactory) -> None:
    """
    test fixture single item normalization 시나리오를 검증한다.

    매개변수:
        configured_adapter (AdapterFactory): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset, _ = configured_adapter(["success_single_item.json"])

    batch = adapter.query_records(dataset, Query())

    assert batch.items == [{"stationName": "종로구", "pm10Value": "45"}]
    assert batch.total_count == 1


# test fixture empty response 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_empty_response(configured_adapter: AdapterFactory) -> None:
    """
    test fixture empty response 시나리오를 검증한다.

    매개변수:
        configured_adapter (AdapterFactory): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset, _ = configured_adapter(["success_empty.json"])

    batch = adapter.query_records(dataset, Query())

    assert batch.items == []
    assert batch.total_count is None


# test fixture string numerics 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_string_numerics(configured_adapter: AdapterFactory) -> None:
    """
    test fixture string numerics 시나리오를 검증한다.

    매개변수:
        configured_adapter (AdapterFactory): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset, _ = configured_adapter(["success_string_numerics.json"])

    batch = adapter.query_records(dataset, Query(page=1, page_size=100))

    assert isinstance(batch.total_count, int)
    assert batch.total_count == 1


# test fixture auth error 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_auth_error(configured_adapter: AdapterFactory) -> None:
    """
    test fixture auth error 시나리오를 검증한다.

    매개변수:
        configured_adapter (AdapterFactory): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset, _ = configured_adapter(["error_auth_30.json"])

    with pytest.raises(AuthError) as excinfo:
        _ = adapter.query_records(dataset, Query())

    assert excinfo.value.provider_code == "30"


# test fixture rate limit 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_rate_limit(configured_adapter: AdapterFactory) -> None:
    """
    test fixture rate limit 시나리오를 검증한다.

    매개변수:
        configured_adapter (AdapterFactory): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset, _ = configured_adapter(["error_rate_limit_22.json"])

    with pytest.raises(RateLimitError) as excinfo:
        _ = adapter.query_records(dataset, Query())

    assert excinfo.value.provider_code == "22"
    assert excinfo.value.retryable is False


# test fixture invalid request 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_invalid_request(configured_adapter: AdapterFactory) -> None:
    """
    test fixture invalid request 시나리오를 검증한다.

    매개변수:
        configured_adapter (AdapterFactory): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset, _ = configured_adapter(["error_invalid_request_10.json"])

    with pytest.raises(InvalidRequestError):
        _ = adapter.query_records(dataset, Query())


# test fixture service unavailable 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_service_unavailable(configured_adapter: AdapterFactory) -> None:
    """
    test fixture service unavailable 시나리오를 검증한다.

    매개변수:
        configured_adapter (AdapterFactory): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset, _ = configured_adapter(["error_service_unavailable_01.json"])

    with pytest.raises(ServiceUnavailableError):
        _ = adapter.query_records(dataset, Query())


# test fixture xml response 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_xml_response(configured_adapter: AdapterFactory) -> None:
    """
    test fixture xml response 시나리오를 검증한다.

    매개변수:
        configured_adapter (AdapterFactory): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    pytest.importorskip("xmltodict")
    adapter, dataset, _ = configured_adapter(["success_xml.xml"], "application/xml")

    batch = adapter.query_records(dataset, Query())

    assert [item["stationName"] for item in batch.items] == ["종로구", "강남구"]
    assert batch.total_count == 2


# test fixture records have korean text 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_records_have_korean_text(configured_adapter: AdapterFactory) -> None:
    """
    test fixture records have korean text 시나리오를 검증한다.

    매개변수:
        configured_adapter (AdapterFactory): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset, _ = configured_adapter(["success_single_page.json"])

    batch = adapter.query_records(dataset, Query())

    assert batch.items[0]["stationName"] == "종로구"
    assert batch.items[1]["stationName"] == "강남구"


# test fixture call raw returns full envelope 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_call_raw_returns_full_envelope(configured_adapter: AdapterFactory) -> None:
    """
    test fixture call raw returns full envelope 시나리오를 검증한다.

    매개변수:
        configured_adapter (AdapterFactory): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset, _ = configured_adapter(["success_single_page.json"])
    expected = load_json_fixture("success_single_page.json")

    payload = adapter.call_raw(dataset, "getVilageFcst", {})

    assert payload == expected
    payload_dict = cast(dict[str, object], payload)
    response = payload_dict["response"]
    assert isinstance(response, dict)
    assert "header" in response
    assert "body" in response


# test fixture apt rent parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_apt_rent_parses() -> None:
    """
    test fixture apt rent parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter("success_apt_rent.json", "apt_rent")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "deposit" in batch.items[0]
    assert "monthlyRent" in batch.items[0]
    assert batch.total_count == 2


# test fixture offi trade parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_offi_trade_parses() -> None:
    """
    test fixture offi trade parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter("success_offi_trade.json", "offi_trade")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "dealAmount" in batch.items[0]
    assert batch.total_count == 2


# test fixture offi rent parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_offi_rent_parses() -> None:
    """
    test fixture offi rent parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter("success_offi_rent.json", "offi_rent")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "deposit" in batch.items[0]
    assert "monthlyRent" in batch.items[0]
    assert batch.total_count == 2


# test fixture rh trade parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_rh_trade_parses() -> None:
    """
    test fixture rh trade parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter("success_rh_trade.json", "rh_trade")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "dealAmount" in batch.items[0]
    assert batch.total_count == 2


# test fixture rh rent parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_rh_rent_parses() -> None:
    """
    test fixture rh rent parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter("success_rh_rent.json", "rh_rent")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "deposit" in batch.items[0]
    assert "monthlyRent" in batch.items[0]
    assert batch.total_count == 2


# test fixture sh trade parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_sh_trade_parses() -> None:
    """
    test fixture sh trade parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter("success_sh_trade.json", "sh_trade")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "dealAmount" in batch.items[0]
    assert batch.total_count == 2


# test fixture sh rent parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_sh_rent_parses() -> None:
    """
    test fixture sh rent parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter("success_sh_rent.json", "sh_rent")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "deposit" in batch.items[0]
    assert "monthlyRent" in batch.items[0]
    assert batch.total_count == 2


# test fixture tour kor area parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_tour_kor_area_parses() -> None:
    """
    test fixture tour kor area parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter("success_tour_kor_area.json", "tour_kor_area")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert batch.items[0]["title"] == "경복궁"
    assert "contentid" in batch.items[0]
    assert batch.total_count == 2


# test fixture tour kor location parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_tour_kor_location_parses() -> None:
    """
    test fixture tour kor location parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter(
        "success_tour_kor_location.json", "tour_kor_location"
    )

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "dist" in batch.items[0]
    assert batch.total_count == 2


# test fixture tour kor keyword parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_tour_kor_keyword_parses() -> None:
    """
    test fixture tour kor keyword parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter(
        "success_tour_kor_keyword.json", "tour_kor_keyword"
    )

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "title" in batch.items[0]
    assert batch.total_count == 2


# test fixture tour kor festival parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_tour_kor_festival_parses() -> None:
    """
    test fixture tour kor festival parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter(
        "success_tour_kor_festival.json", "tour_kor_festival"
    )

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "eventstartdate" in batch.items[0]
    assert "eventenddate" in batch.items[0]
    assert batch.total_count == 2


# test fixture metro fare parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_metro_fare_parses() -> None:
    """
    test fixture metro fare parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter("success_metro_fare.json", "metro_fare")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "startStation" in batch.items[0]
    assert "endStation" in batch.items[0]
    assert "fareCard" in batch.items[0]
    assert batch.total_count == 2


# test fixture metro path parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_metro_path_parses() -> None:
    """
    test fixture metro path parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter("success_metro_path.json", "metro_path")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 3
    assert batch.items[0]["stationName"] == "서울역"
    assert "lineNum" in batch.items[0]
    assert batch.total_count == 3


# test fixture building title parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_building_title_parses() -> None:
    """
    test fixture building title parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter("success_building_title.json", "building_title")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "bldNm" in batch.items[0]
    assert batch.total_count == 2


# test fixture building recap title parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_building_recap_title_parses() -> None:
    """
    test fixture building recap title parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter(
        "success_building_recap_title.json", "building_recap_title"
    )

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "vlRat" in batch.items[0]
    assert "bcRat" in batch.items[0]
    assert batch.total_count == 2


# test fixture building floor parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_building_floor_parses() -> None:
    """
    test fixture building floor parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter("success_building_floor.json", "building_floor")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "flrNo" in batch.items[0]
    assert "area" in batch.items[0]
    assert batch.total_count == 2


# test fixture building area parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_building_area_parses() -> None:
    """
    test fixture building area parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter("success_building_area.json", "building_area")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "hoNm" in batch.items[0]
    assert "exposPubuseGbCdNm" in batch.items[0]
    assert batch.total_count == 2


# test fixture g2b contract parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_g2b_contract_parses() -> None:
    """
    test fixture g2b contract parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter("success_g2b_contract.json", "g2b_contract")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "cntrctSn" in batch.items[0]
    assert "prdctNm" in batch.items[0]
    assert "cntrctAmt" in batch.items[0]
    assert batch.total_count == 2


# test fixture social enterprise parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_social_enterprise_parses() -> None:
    """
    test fixture social enterprise parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter(
        "success_social_enterprise.json", "social_enterprise"
    )

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "entNmV" in batch.items[0]
    assert "certiNumV" in batch.items[0]
    assert batch.total_count == 4783


# test fixture road traffic call raw returns full envelope 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_road_traffic_call_raw_returns_full_envelope() -> None:
    """
    test fixture road traffic call raw returns full envelope 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter("success_road_traffic.json", "road_traffic")
    expected = load_json_fixture("success_road_traffic.json")

    payload = adapter.call_raw(dataset, "trafficInfo", {"type": "all", "drcType": "all"})

    assert payload == expected
    payload_dict = cast(dict[str, object], payload)
    assert payload_dict["resultCode"] == "00"
    items = cast(list[dict[str, object]], payload_dict["items"])
    assert len(items) == 3
    first = items[0]
    assert first["roadName"] == "경부고속도로"
    assert first["linkId"] == "1610038501"


# test fixture road traffic list parses flat envelope 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_road_traffic_list_parses_flat_envelope() -> None:
    """
    test fixture road traffic list parses flat envelope 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter("success_road_traffic.json", "road_traffic")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 3
    assert batch.items[0]["roadName"] == "경부고속도로"
    assert "speed" in batch.items[0]
    assert "travelTime" in batch.items[0]
    assert batch.total_count == 3


# test fixture g2b catalog parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_g2b_catalog_parses() -> None:
    """
    test fixture g2b catalog parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter("success_g2b_catalog.json", "g2b_catalog")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert "prdctIdntNo" in batch.items[0]
    assert "prdctNm" in batch.items[0]
    assert "crtfcTyNm" in batch.items[0]
    assert batch.total_count == 2


# test fixture dur age taboo parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_dur_age_taboo_parses() -> None:
    """
    test fixture dur age taboo parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter("success_dur_age_taboo.json", "dur_age_taboo")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert batch.items[0]["ITEM_NAME"] == "샘플정G"
    assert "CLASS_NAME" in batch.items[0]
    assert "SPCIFY_AGRDE_TABOO_CN" in batch.items[0]
    assert batch.total_count == 2


# test fixture dur age taboo call raw returns full envelope 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_dur_age_taboo_call_raw_returns_full_envelope() -> None:
    """
    test fixture dur age taboo call raw returns full envelope 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter("success_dur_age_taboo.json", "dur_age_taboo")
    expected = load_json_fixture("success_dur_age_taboo.json")

    payload = adapter.call_raw(dataset, "getSpcifyAgrdeTabooInfoList03", {"itemName": "샘플"})

    assert payload == expected
    payload_dict = cast(dict[str, object], payload)
    response = payload_dict["response"]
    assert isinstance(response, dict)
    assert "header" in response
    assert "body" in response


# test fixture dur dosage caution parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_dur_dosage_caution_parses() -> None:
    """
    test fixture dur dosage caution parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter(
        "success_dur_dosage_caution.json", "dur_dosage_caution"
    )

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert batch.items[0]["ITEM_NAME"] == "샘플정G"
    assert "CLASS_NAME" in batch.items[0]
    assert "CPCTY_ATENT_CN" in batch.items[0]
    assert batch.total_count == 2


# test fixture dur dosage caution call raw returns full envelope 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_dur_dosage_caution_call_raw_returns_full_envelope() -> None:
    """
    test fixture dur dosage caution call raw returns full envelope 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter(
        "success_dur_dosage_caution.json", "dur_dosage_caution"
    )
    expected = load_json_fixture("success_dur_dosage_caution.json")

    payload = adapter.call_raw(dataset, "getCpctyAtentInfoList03", {"itemName": "샘플"})

    assert payload == expected
    payload_dict = cast(dict[str, object], payload)
    response = payload_dict["response"]
    assert isinstance(response, dict)
    assert "header" in response
    assert "body" in response


# test fixture dur medication period caution parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_dur_medication_period_caution_parses() -> None:
    """
    test fixture dur medication period caution parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter(
        "success_dur_medication_period_caution.json",
        "dur_medication_period_caution",
    )

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert batch.items[0]["ITEM_NAME"] == "샘플정I"
    assert "CLASS_NAME" in batch.items[0]
    assert "MDCTN_PD_ATENT_CN" in batch.items[0]
    assert batch.total_count == 2


# test fixture dur medication period caution call raw returns full envelope 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_dur_medication_period_caution_call_raw_returns_full_envelope() -> None:
    """
    test fixture dur medication period caution call raw returns full envelope 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter(
        "success_dur_medication_period_caution.json",
        "dur_medication_period_caution",
    )
    expected = load_json_fixture("success_dur_medication_period_caution.json")

    payload = adapter.call_raw(dataset, "getMdctnPdAtentInfoList03", {"itemName": "샘플"})

    assert payload == expected
    payload_dict = cast(dict[str, object], payload)
    response = payload_dict["response"]
    assert isinstance(response, dict)
    assert "header" in response
    assert "body" in response


# test fixture dur efficacy duplication parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_dur_efficacy_duplication_parses() -> None:
    """
    test fixture dur efficacy duplication parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter(
        "success_dur_efficacy_duplication.json", "dur_efficacy_duplication"
    )

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert batch.items[0]["ITEM_NAME"] == "샘플정G"
    assert "SERS_NAME" in batch.items[0]
    assert "PROHBT_CONTENT" in batch.items[0]
    assert batch.total_count == 2


# test fixture dur efficacy duplication call raw returns full envelope 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_dur_efficacy_duplication_call_raw_returns_full_envelope() -> None:
    """
    test fixture dur efficacy duplication call raw returns full envelope 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter(
        "success_dur_efficacy_duplication.json", "dur_efficacy_duplication"
    )
    expected = load_json_fixture("success_dur_efficacy_duplication.json")

    payload = adapter.call_raw(dataset, "getEfcyDplctInfoList03", {"itemName": "샘플"})

    assert payload == expected
    payload_dict = cast(dict[str, object], payload)
    response = payload_dict["response"]
    assert isinstance(response, dict)
    assert "header" in response
    assert "body" in response


# test fixture dur er tablet split caution parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_dur_er_tablet_split_caution_parses() -> None:
    """
    test fixture dur er tablet split caution parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter(
        "success_dur_er_tablet_split_caution.json", "dur_er_tablet_split_caution"
    )

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert batch.items[0]["ITEM_NAME"] == "샘플서방정A"
    assert "CLASS_NAME" in batch.items[0]
    assert "SEOBANGJEONG_PARTITN_ATENT_CN" in batch.items[0]
    assert batch.total_count == 2


# test fixture dur er tablet split caution call raw returns full envelope 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_dur_er_tablet_split_caution_call_raw_returns_full_envelope() -> None:
    """
    test fixture dur er tablet split caution call raw returns full envelope 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter(
        "success_dur_er_tablet_split_caution.json", "dur_er_tablet_split_caution"
    )
    expected = load_json_fixture("success_dur_er_tablet_split_caution.json")

    payload = adapter.call_raw(
        dataset,
        "getSeobangjeongPartitnAtentInfoList03",
        {"itemName": "샘플"},
    )

    assert payload == expected
    payload_dict = cast(dict[str, object], payload)
    response = payload_dict["response"]
    assert isinstance(response, dict)
    assert "header" in response
    assert "body" in response


# test fixture dur pregnancy taboo parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_dur_pregnancy_taboo_parses() -> None:
    """
    test fixture dur pregnancy taboo parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter(
        "success_dur_pregnancy_taboo.json", "dur_pregnancy_taboo"
    )

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 2
    assert batch.items[0]["ITEM_NAME"] == "샘플정I"
    assert "PREGNANT_GRADE" in batch.items[0]
    assert "PREGNANT_PROHBT_CN" in batch.items[0]
    assert batch.total_count == 2


# test fixture dur pregnancy taboo call raw returns full envelope 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_dur_pregnancy_taboo_call_raw_returns_full_envelope() -> None:
    """
    test fixture dur pregnancy taboo call raw returns full envelope 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter(
        "success_dur_pregnancy_taboo.json", "dur_pregnancy_taboo"
    )
    expected = load_json_fixture("success_dur_pregnancy_taboo.json")

    payload = adapter.call_raw(dataset, "getPwnmTabooInfoList03", {"itemName": "샘플"})

    assert payload == expected
    payload_dict = cast(dict[str, object], payload)
    response = payload_dict["response"]
    assert isinstance(response, dict)
    assert "header" in response
    assert "body" in response


# test fixture agri price parses 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_agri_price_parses() -> None:
    """
    test fixture agri price parses 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter("success_agri_price.json", "agri_price")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 3
    assert batch.items[0]["item_nm"] == "쌀"
    assert "exmn_dd_prc" in batch.items[0]
    assert "sgg_nm" in batch.items[0]
    assert "grd_nm" in batch.items[0]
    assert batch.total_count == 3


# test fixture agri price call raw returns full envelope 테스트가 검증하는 시나리오를 설명한다.
def test_fixture_agri_price_call_raw_returns_full_envelope() -> None:
    """
    test fixture agri price call raw returns full envelope 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    adapter, dataset = _build_real_estate_adapter("success_agri_price.json", "agri_price")
    expected = load_json_fixture("success_agri_price.json")

    payload = adapter.call_raw(dataset, "price", {"cond[exmn_ymd::GTE]": "20240101"})

    assert payload == expected
    payload_dict = cast(dict[str, object], payload)
    response = payload_dict["response"]
    assert isinstance(response, dict)
    assert "header" in response
    assert "body" in response


def test_fixture_mid_fcst_parses() -> None:
    adapter, dataset = _build_real_estate_adapter("success_mid_fcst.json", "mid_fcst")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 1
    assert "wfSv" in batch.items[0]
    assert batch.total_count == 1


def test_fixture_mid_fcst_call_raw_returns_full_envelope() -> None:
    adapter, dataset = _build_real_estate_adapter("success_mid_fcst.json", "mid_fcst")
    expected = load_json_fixture("success_mid_fcst.json")

    payload = adapter.call_raw(dataset, "getMidFcst", {"stnId": "108", "tmFc": "2026052206"})

    assert payload == expected
    payload_dict = cast(dict[str, object], payload)
    response = payload_dict["response"]
    assert isinstance(response, dict)
    assert "header" in response
    assert "body" in response


def test_fixture_mid_land_fcst_parses() -> None:
    adapter, dataset = _build_real_estate_adapter("success_mid_land_fcst.json", "mid_land_fcst")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 1
    assert batch.items[0]["regId"] == "11B00000"
    assert "rnSt4Am" in batch.items[0]
    assert "wf4Am" in batch.items[0]
    assert batch.total_count == 1


def test_fixture_mid_land_fcst_call_raw_returns_full_envelope() -> None:
    adapter, dataset = _build_real_estate_adapter("success_mid_land_fcst.json", "mid_land_fcst")
    expected = load_json_fixture("success_mid_land_fcst.json")

    payload = adapter.call_raw(
        dataset, "getMidLandFcst", {"regId": "11B00000", "tmFc": "2026052206"}
    )

    assert payload == expected
    payload_dict = cast(dict[str, object], payload)
    response = payload_dict["response"]
    assert isinstance(response, dict)
    assert "header" in response
    assert "body" in response


def test_fixture_mid_ta_parses() -> None:
    adapter, dataset = _build_real_estate_adapter("success_mid_ta.json", "mid_ta")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 1
    assert batch.items[0]["regId"] == "11D20501"
    assert "taMin4" in batch.items[0]
    assert "taMax4" in batch.items[0]
    assert batch.total_count == 1


def test_fixture_mid_ta_call_raw_returns_full_envelope() -> None:
    adapter, dataset = _build_real_estate_adapter("success_mid_ta.json", "mid_ta")
    expected = load_json_fixture("success_mid_ta.json")

    payload = adapter.call_raw(dataset, "getMidTa", {"regId": "11D20501", "tmFc": "2026052206"})

    assert payload == expected
    payload_dict = cast(dict[str, object], payload)
    response = payload_dict["response"]
    assert isinstance(response, dict)
    assert "header" in response
    assert "body" in response


def test_fixture_mid_sea_fcst_parses() -> None:
    adapter, dataset = _build_real_estate_adapter("success_mid_sea_fcst.json", "mid_sea_fcst")

    batch = adapter.query_records(dataset, Query())

    assert len(batch.items) == 1
    assert batch.items[0]["regId"] == "12A20000"
    assert "wf4Am" in batch.items[0]
    assert "wh4AAm" in batch.items[0]
    assert batch.total_count == 1


def test_fixture_mid_sea_fcst_call_raw_returns_full_envelope() -> None:
    adapter, dataset = _build_real_estate_adapter("success_mid_sea_fcst.json", "mid_sea_fcst")
    expected = load_json_fixture("success_mid_sea_fcst.json")

    payload = adapter.call_raw(
        dataset, "getMidSeaFcst", {"regId": "12A20000", "tmFc": "2026052206"}
    )

    assert payload == expected
    payload_dict = cast(dict[str, object], payload)
    response = payload_dict["response"]
    assert isinstance(response, dict)
    assert "header" in response
    assert "body" in response
