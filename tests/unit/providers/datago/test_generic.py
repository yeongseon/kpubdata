"""테스트 모듈.

이 파일은 ``tests/unit/providers/datago/test_generic.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

import json
import logging
from typing import cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.exceptions import ConfigError, InvalidRequestError
from kpubdata.providers.datago.adapter import DataGoAdapter
from kpubdata.transport.http import HttpTransport


class FakeResponse:
    """
    FakeResponse 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/providers/datago/test_generic.py`` 모듈 안에서 FakeResponse의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    def __init__(self, payload: object, content_type: str = "application/json") -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        매개변수:
            payload (object): 호출자가 제공하는 입력 값이다.
            content_type (str): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self.headers: dict[str, str] = {"content-type": content_type}
        self.text: str = json.dumps(payload)
        self.content: bytes = self.text.encode()


class FakeTransport:
    """
    FakeTransport 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/providers/datago/test_generic.py`` 모듈 안에서 FakeTransport의 상태와 동작을 함께 관리한다.
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
        return self._responses.pop(0)


def _success_envelope() -> dict[str, object]:
    """
    내부 헬퍼로서 success envelope 처리를 담당한다.

    반환값:
        dict[str, object]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    return {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "OK"},
            "body": {"items": {"item": [{"x": "1"}]}, "totalCount": 1},
        }
    }


def _build_adapter(responses: list[FakeResponse]) -> tuple[DataGoAdapter, FakeTransport]:
    """
    내부 헬퍼로서 build adapter 처리를 담당한다.

    매개변수:
        responses (list[FakeResponse]): 호출자가 제공하는 입력 값이다.

    반환값:
        tuple[DataGoAdapter, FakeTransport]: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
    """
    transport = FakeTransport(responses)
    config = KPubDataConfig(provider_keys={"datago": "test-key"})
    adapter = DataGoAdapter(
        config=config,
        transport=cast(HttpTransport, cast(object, transport)),
    )
    return adapter, transport


class TestDataGoGenericDataset:
    """
    TestDataGoGenericDataset 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/providers/datago/test_generic.py`` 모듈 안에서 TestDataGoGenericDataset의 상태와 동작을 함께 관리한다.
    주요 메서드: test_generic_dataset_in_catalogue, test_call_raw_with_base_url_builds_url, test_call_raw_strips_trailing_slash_from_base_url, test_call_raw_missing_base_url_raises, test_call_raw_missing_base_url_logs_debug.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """

    # test generic dataset in catalogue 테스트가 검증하는 시나리오를 설명한다.
    def test_generic_dataset_in_catalogue(self) -> None:
        """
        test generic dataset in catalogue 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter = DataGoAdapter()

        dataset = adapter.get_dataset("generic")

        assert dataset.id == "datago.generic"
        assert dataset.dataset_key == "generic"
        assert dataset.raw_metadata.get("generic") is True

    # test call raw with base url builds url 테스트가 검증하는 시나리오를 설명한다.
    def test_call_raw_with_base_url_builds_url(self) -> None:
        """
        test call raw with base url builds url 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter, transport = _build_adapter([FakeResponse(_success_envelope())])
        dataset = adapter.get_dataset("generic")

        adapter.call_raw(
            dataset,
            "getVilageFcst",
            {
                "_base_url": "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0",
                "base_date": "20250401",
                "nx": "55",
            },
        )

        call = transport.calls[0]
        assert (
            call["url"] == "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
        )
        params = cast(dict[str, str], call["params"])
        assert params["serviceKey"] == "test-key"
        assert params["base_date"] == "20250401"
        assert params["nx"] == "55"
        assert "_base_url" not in params

    # test call raw strips trailing slash from base url 테스트가 검증하는 시나리오를 설명한다.
    def test_call_raw_strips_trailing_slash_from_base_url(self) -> None:
        """
        test call raw strips trailing slash from base url 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter, transport = _build_adapter([FakeResponse(_success_envelope())])
        dataset = adapter.get_dataset("generic")

        adapter.call_raw(
            dataset,
            "getX",
            {"_base_url": "http://apis.data.go.kr/foo/bar/"},
        )

        assert transport.calls[0]["url"] == "http://apis.data.go.kr/foo/bar/getX"

    # test call raw missing base url raises 테스트가 검증하는 시나리오를 설명한다.
    def test_call_raw_missing_base_url_raises(self) -> None:
        """
        test call raw missing base url raises 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter, _ = _build_adapter([])
        dataset = adapter.get_dataset("generic")

        with pytest.raises(InvalidRequestError, match="_base_url"):
            adapter.call_raw(dataset, "getX", {})

    # test call raw missing base url logs debug 테스트가 검증하는 시나리오를 설명한다.
    def test_call_raw_missing_base_url_logs_debug(self, caplog: pytest.LogCaptureFixture) -> None:
        """
        test call raw missing base url logs debug 시나리오를 검증한다.

        매개변수:
            caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter, _ = _build_adapter([])
        dataset = adapter.get_dataset("generic")

        caplog.set_level(logging.DEBUG, logger="kpubdata.provider.datago")
        with pytest.raises(InvalidRequestError, match="_base_url"):
            adapter.call_raw(dataset, "getX", {})

        record = next(
            record
            for record in caplog.records
            if record.getMessage() == "Datago.generic missing _base_url in call_raw params"
        )
        assert record.__dict__["dataset_id"] == dataset.id

    # test call raw envelope skip allows non standard payload 테스트가 검증하는 시나리오를 설명한다.
    def test_call_raw_envelope_skip_allows_non_standard_payload(self) -> None:
        """
        test call raw envelope skip allows non standard payload 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        non_standard = {"items": [{"a": 1}]}
        adapter, _ = _build_adapter([FakeResponse(non_standard)])
        dataset = adapter.get_dataset("generic")

        result = adapter.call_raw(
            dataset,
            "getX",
            {
                "_base_url": "http://apis.data.go.kr/foo/bar",
                "_envelope": False,
            },
        )

        assert result == non_standard

    # test call raw with service key param override 테스트가 검증하는 시나리오를 설명한다.
    def test_call_raw_with_service_key_param_override(self) -> None:
        """
        test call raw with service key param override 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter, transport = _build_adapter([FakeResponse(_success_envelope())])
        dataset = adapter.get_dataset("generic")

        adapter.call_raw(
            dataset,
            "getX",
            {
                "_base_url": "http://apis.data.go.kr/foo/bar",
                "_service_key_param": "ServiceKey",
            },
        )

        params = cast(dict[str, str], transport.calls[0]["params"])
        assert params["ServiceKey"] == "test-key"
        assert "serviceKey" not in params

    # test call raw requires api key 테스트가 검증하는 시나리오를 설명한다.
    def test_call_raw_requires_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        test call raw requires api key 시나리오를 검증한다.

        매개변수:
            monkeypatch (pytest.MonkeyPatch): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        monkeypatch.delenv("KPUBDATA_DATAGO_API_KEY", raising=False)
        transport = FakeTransport([])
        adapter = DataGoAdapter(
            config=KPubDataConfig(),
            transport=cast(HttpTransport, cast(object, transport)),
        )
        dataset = adapter.get_dataset("generic")

        with pytest.raises(ConfigError):
            adapter.call_raw(
                dataset,
                "getX",
                {"_base_url": "http://apis.data.go.kr/foo/bar"},
            )

    # test list on generic raises 테스트가 검증하는 시나리오를 설명한다.
    def test_list_on_generic_raises(self) -> None:
        """
        test list on generic raises 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        from kpubdata.core.models import Query

        adapter, _ = _build_adapter([])
        dataset = adapter.get_dataset("generic")

        with pytest.raises(InvalidRequestError, match="generic"):
            adapter.query_records(dataset, Query())

    # test envelope must be bool 테스트가 검증하는 시나리오를 설명한다.
    def test_envelope_must_be_bool(self) -> None:
        """
        test envelope must be bool 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter, _ = _build_adapter([FakeResponse(_success_envelope())])
        dataset = adapter.get_dataset("generic")

        with pytest.raises(InvalidRequestError, match="_envelope"):
            adapter.call_raw(
                dataset,
                "getX",
                {
                    "_base_url": "http://apis.data.go.kr/foo/bar",
                    "_envelope": "false",
                },
            )

    # test envelope rejects int 테스트가 검증하는 시나리오를 설명한다.
    def test_envelope_rejects_int(self) -> None:
        """
        test envelope rejects int 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        adapter, _ = _build_adapter([FakeResponse(_success_envelope())])
        dataset = adapter.get_dataset("generic")

        with pytest.raises(InvalidRequestError, match="_envelope"):
            adapter.call_raw(
                dataset,
                "getX",
                {
                    "_base_url": "http://apis.data.go.kr/foo/bar",
                    "_envelope": 0,
                },
            )

    # test non data go kr host logs warning 테스트가 검증하는 시나리오를 설명한다.
    def test_non_data_go_kr_host_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """
        test non data go kr host logs warning 시나리오를 검증한다.

        매개변수:
            caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        import logging

        adapter, _ = _build_adapter([FakeResponse(_success_envelope())])
        dataset = adapter.get_dataset("generic")

        with caplog.at_level(logging.WARNING, logger="kpubdata.provider.datago"):
            adapter.call_raw(
                dataset,
                "getX",
                {"_base_url": "http://example.com/foo"},
            )

        assert any("non-data.go.kr host" in record.message for record in caplog.records)

    # test data go kr host no warning 테스트가 검증하는 시나리오를 설명한다.
    def test_data_go_kr_host_no_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """
        test data go kr host no warning 시나리오를 검증한다.

        매개변수:
            caplog (pytest.LogCaptureFixture): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        import logging

        adapter, _ = _build_adapter([FakeResponse(_success_envelope())])
        dataset = adapter.get_dataset("generic")

        with caplog.at_level(logging.WARNING, logger="kpubdata.provider.datago"):
            adapter.call_raw(
                dataset,
                "getX",
                {"_base_url": "http://apis.data.go.kr/foo/bar"},
            )

        assert not any("non-data.go.kr" in record.message for record in caplog.records)
