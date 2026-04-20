from __future__ import annotations

import json
from typing import cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.exceptions import ConfigError, InvalidRequestError
from kpubdata.providers.datago.adapter import DataGoAdapter
from kpubdata.transport.http import HttpTransport


class FakeResponse:
    def __init__(self, payload: dict[str, object], content_type: str = "application/json") -> None:
        self.headers: dict[str, str] = {"content-type": content_type}
        self.text: str = json.dumps(payload)
        self.content: bytes = self.text.encode()


class FakeTransport:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self._responses: list[FakeResponse] = list(responses)
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        return self._responses.pop(0)


def _success_envelope() -> dict[str, object]:
    return {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "OK"},
            "body": {"items": {"item": [{"x": "1"}]}, "totalCount": 1},
        }
    }


def _build_adapter(responses: list[FakeResponse]) -> tuple[DataGoAdapter, FakeTransport]:
    transport = FakeTransport(responses)
    config = KPubDataConfig(provider_keys={"datago": "test-key"})
    adapter = DataGoAdapter(
        config=config,
        transport=cast(HttpTransport, cast(object, transport)),
    )
    return adapter, transport


class TestDataGoGenericDataset:
    def test_generic_dataset_in_catalogue(self) -> None:
        adapter = DataGoAdapter()

        dataset = adapter.get_dataset("generic")

        assert dataset.id == "datago.generic"
        assert dataset.dataset_key == "generic"
        assert dataset.raw_metadata.get("generic") is True

    def test_call_raw_with_base_url_builds_url(self) -> None:
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

    def test_call_raw_strips_trailing_slash_from_base_url(self) -> None:
        adapter, transport = _build_adapter([FakeResponse(_success_envelope())])
        dataset = adapter.get_dataset("generic")

        adapter.call_raw(
            dataset,
            "getX",
            {"_base_url": "http://apis.data.go.kr/foo/bar/"},
        )

        assert transport.calls[0]["url"] == "http://apis.data.go.kr/foo/bar/getX"

    def test_call_raw_missing_base_url_raises(self) -> None:
        adapter, _ = _build_adapter([])
        dataset = adapter.get_dataset("generic")

        with pytest.raises(InvalidRequestError, match="_base_url"):
            adapter.call_raw(dataset, "getX", {})

    def test_call_raw_envelope_skip_allows_non_standard_payload(self) -> None:
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

    def test_call_raw_with_service_key_param_override(self) -> None:
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

    def test_call_raw_requires_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
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

    def test_list_on_generic_raises(self) -> None:
        from kpubdata.core.models import Query

        adapter, _ = _build_adapter([])
        dataset = adapter.get_dataset("generic")

        with pytest.raises(InvalidRequestError, match="generic"):
            adapter.query_records(dataset, Query())

    def test_envelope_must_be_bool(self) -> None:
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

    def test_envelope_rejects_int(self) -> None:
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

    def test_non_data_go_kr_host_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
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

    def test_data_go_kr_host_no_warning(self, caplog: pytest.LogCaptureFixture) -> None:
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
