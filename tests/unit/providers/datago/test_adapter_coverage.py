from __future__ import annotations

from types import MappingProxyType
from typing import cast

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.core.representation import Representation
from kpubdata.exceptions import ConfigError, ParseError, ProviderResponseError
from kpubdata.providers._common import build_dataset_ref, coerce_int, require_string_field
from kpubdata.providers.datago.adapter import DataGoAdapter
from kpubdata.transport.http import HttpTransport


class FakeResponse:
    def __init__(self, data: bytes, content_type: str = "application/json") -> None:
        self.headers: dict[str, str] = {"content-type": content_type}
        self.content: bytes = data
        self.text: str = data.decode("utf-8")


class FakeTransport:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        if not self._responses:
            raise AssertionError("No responses queued")
        return self._responses.pop(0)


def _dataset(raw_metadata: dict[str, object]) -> DatasetRef:
    return DatasetRef(
        id="datago.test",
        provider="datago",
        dataset_key="test",
        name="Test Dataset",
        representation=Representation.API_JSON,
        operations=frozenset(),
        raw_metadata=MappingProxyType(raw_metadata),
    )


def _adapter(
    transport: FakeTransport,
    dataset: DatasetRef,
) -> DataGoAdapter:
    return DataGoAdapter(
        config=KPubDataConfig(provider_keys={"datago": "test-key"}),
        transport=cast(HttpTransport, cast(object, transport)),
        catalogue=[dataset],
    )


def _ok_payload(*, items: object, total_count: object, num_of_rows: object) -> dict[str, object]:
    return {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
            "body": {
                "items": {"item": items},
                "totalCount": total_count,
                "numOfRows": num_of_rows,
                "pageNo": 1,
            },
        }
    }


def test_name_property_returns_datago() -> None:
    assert DataGoAdapter(catalogue=[]).name == "datago"


def test_get_record_raises_not_implemented() -> None:
    adapter = DataGoAdapter(catalogue=[])
    with pytest.raises(NotImplementedError):
        _ = adapter.get_record(_dataset({"base_url": "https://example.test"}), {})


def test_query_records_advances_page_for_full_page_with_remaining_total(monkeypatch) -> None:
    import kpubdata.providers.datago.adapter as adapter_module

    page1 = _ok_payload(items=[{"id": 1}, {"id": 2}], total_count=5, num_of_rows=2)
    page2 = _ok_payload(items=[{"id": 3}], total_count=5, num_of_rows=2)
    transport = FakeTransport([FakeResponse(b"{}"), FakeResponse(b"{}")])
    dataset = _dataset({"base_url": "https://example.test", "default_operation": "list"})
    adapter = _adapter(transport, dataset)

    decoded_pages = [page1, page2]
    monkeypatch.setattr(adapter_module, "detect_content_type", lambda _resp: "json")
    monkeypatch.setattr(adapter_module, "decode_json", lambda _content: decoded_pages.pop(0))

    _ = adapter.query_records(dataset, Query(page_size=2))

    assert len(transport.calls) == 2
    second_params = transport.calls[1]["params"]
    assert isinstance(second_params, dict)
    assert second_params["pageNo"] == "2"


def test_query_records_stops_when_page_size_times_page_reaches_total(monkeypatch) -> None:
    import kpubdata.providers.datago.adapter as adapter_module

    payload = _ok_payload(items=[{"id": 1}, {"id": 2}], total_count=2, num_of_rows=2)
    transport = FakeTransport([FakeResponse(b"{}")])
    dataset = _dataset({"base_url": "https://example.test", "default_operation": "list"})
    adapter = _adapter(transport, dataset)

    monkeypatch.setattr(adapter_module, "detect_content_type", lambda _resp: "json")
    monkeypatch.setattr(adapter_module, "decode_json", lambda _content: payload)

    _ = adapter.query_records(dataset, Query(page_size=2))

    assert len(transport.calls) == 1


def test_get_schema_returns_none_when_all_fields_are_filtered_out() -> None:
    dataset = _dataset(
        {
            "base_url": "https://example.test",
            "fields": [{"title": "no-name"}, {"name": ""}, {"name": None}],
        }
    )
    adapter = DataGoAdapter(catalogue=[dataset])

    assert adapter.get_schema(dataset) is None


def test_build_request_url_raises_when_base_url_missing() -> None:
    adapter = DataGoAdapter(catalogue=[])
    with pytest.raises(ProviderResponseError, match="missing base_url"):
        _ = adapter._build_request_url(_dataset({}))


def test_build_request_url_returns_base_url_when_operation_missing() -> None:
    adapter = DataGoAdapter(catalogue=[])
    dataset = _dataset({"base_url": "https://example.test/api"})

    assert adapter._build_request_url(dataset) == "https://example.test/api"


def test_request_and_decode_falls_back_to_json_for_unknown_content_type(monkeypatch) -> None:
    import kpubdata.providers.datago.adapter as adapter_module

    transport = FakeTransport([FakeResponse(b"ignored")])
    adapter = DataGoAdapter(
        config=KPubDataConfig(provider_keys={"datago": "test-key"}),
        transport=cast(HttpTransport, cast(object, transport)),
        catalogue=[],
    )

    called = {"decode_json": False}

    monkeypatch.setattr(adapter_module, "detect_content_type", lambda _resp: "unknown")

    def _decode_json(_content: bytes) -> dict[str, object]:
        called["decode_json"] = True
        return {"response": {}}

    monkeypatch.setattr(adapter_module, "decode_json", _decode_json)

    decoded = adapter._request_and_decode("https://example.test", {"a": "1"})
    assert called["decode_json"] is True
    assert decoded == {"response": {}}


def test_request_and_decode_raises_parse_error_when_decoded_payload_not_object(monkeypatch) -> None:
    import kpubdata.providers.datago.adapter as adapter_module

    transport = FakeTransport([FakeResponse(b"[]")])
    adapter = DataGoAdapter(
        config=KPubDataConfig(provider_keys={"datago": "test-key"}),
        transport=cast(HttpTransport, cast(object, transport)),
        catalogue=[],
    )

    monkeypatch.setattr(adapter_module, "detect_content_type", lambda _resp: "json")
    monkeypatch.setattr(adapter_module, "decode_json", lambda _content: [{"x": 1}])

    with pytest.raises(ParseError, match="not an object"):
        _ = adapter._request_and_decode("https://example.test", {})


def test_request_and_decode_raises_parse_error_when_decode_fails(monkeypatch) -> None:
    import kpubdata.providers.datago.adapter as adapter_module

    transport = FakeTransport([FakeResponse(b"invalid")])
    adapter = DataGoAdapter(
        config=KPubDataConfig(provider_keys={"datago": "test-key"}),
        transport=cast(HttpTransport, cast(object, transport)),
        catalogue=[],
    )

    monkeypatch.setattr(adapter_module, "detect_content_type", lambda _resp: "unknown")

    def _raises_parse_error(_content: bytes) -> dict[str, object]:
        raise ParseError("bad payload")

    monkeypatch.setattr(adapter_module, "decode_json", _raises_parse_error)

    with pytest.raises(ParseError, match="bad payload"):
        _ = adapter._request_and_decode("https://example.test", {})


def test_validate_envelope_raises_when_response_missing() -> None:
    adapter = DataGoAdapter(catalogue=[])

    with pytest.raises(ProviderResponseError, match="missing response"):
        _ = adapter._validate_envelope({})


def test_validate_envelope_raises_when_header_missing() -> None:
    adapter = DataGoAdapter(catalogue=[])

    with pytest.raises(ProviderResponseError, match="missing header"):
        _ = adapter._validate_envelope({"response": {"body": {}}})


def test_validate_envelope_raises_when_result_code_not_string() -> None:
    adapter = DataGoAdapter(catalogue=[])

    with pytest.raises(ProviderResponseError, match="missing resultCode"):
        _ = adapter._validate_envelope({"response": {"header": {"resultCode": 0}, "body": {}}})


def test_raise_for_result_code_unknown_code_raises_provider_response_error() -> None:
    adapter = DataGoAdapter(catalogue=[])

    with pytest.raises(ProviderResponseError):
        adapter._raise_for_result_code("99", "unknown code", "datago.test")


def test_normalize_items_accepts_direct_list_wrapper() -> None:
    adapter = DataGoAdapter(catalogue=[])

    normalized = adapter._normalize_items([{"id": 1}, "x", {"id": 2}])

    assert normalized == [{"id": 1}, {"id": 2}]


def test_normalize_items_returns_empty_for_unsupported_wrapper() -> None:
    adapter = DataGoAdapter(catalogue=[])
    assert adapter._normalize_items("not-a-list-or-dict") == []


def test_coerce_int_returns_default_for_non_numeric_string() -> None:
    assert coerce_int("not-a-number", 7) == 7


def test_coerce_int_returns_default_for_non_string_non_int() -> None:
    assert coerce_int(3.14, 11) == 11


class _FakeCatalogueFile:
    def __init__(self, text: str) -> None:
        self._text = text

    def read_text(self, encoding: str = "utf-8") -> str:
        del encoding
        return self._text


class _FakePackageFiles:
    def __init__(self, text: str) -> None:
        self._text = text

    def joinpath(self, _name: str) -> _FakeCatalogueFile:
        return _FakeCatalogueFile(self._text)


def test_load_default_catalogue_raises_when_top_level_json_not_list(monkeypatch) -> None:
    import kpubdata.providers._common as common_module

    monkeypatch.setattr(common_module, "files", lambda _pkg: _FakePackageFiles("{}"))

    with pytest.raises(ConfigError, match="top-level JSON array"):
        _ = DataGoAdapter._load_default_catalogue()


def test_load_default_catalogue_raises_when_entry_not_dict(monkeypatch) -> None:
    import kpubdata.providers._common as common_module

    monkeypatch.setattr(common_module, "files", lambda _pkg: _FakePackageFiles("[1]"))

    with pytest.raises(ConfigError, match="entries must be JSON objects"):
        _ = DataGoAdapter._load_default_catalogue()


def test_load_default_catalogue_raises_when_entry_key_not_string(monkeypatch) -> None:
    import kpubdata.providers._common as common_module

    monkeypatch.setattr(common_module, "files", lambda _pkg: _FakePackageFiles("[]"))
    monkeypatch.setattr(common_module.json, "loads", lambda _text: [{1: "bad-key"}])

    with pytest.raises(ConfigError, match="entry keys must be strings"):
        _ = DataGoAdapter._load_default_catalogue()


def test_build_dataset_ref_parses_string_max_page_size() -> None:
    dataset = build_dataset_ref(
        "datago",
        {
            "dataset_key": "test",
            "name": "Test",
            "representation": "api_json",
            "query_support": {"pagination": "offset", "max_page_size": "250"},
            "base_url": "https://example.test",
        },
    )

    assert dataset.query_support is not None
    assert dataset.query_support.max_page_size == 250


def test_build_dataset_ref_raises_for_invalid_max_page_size_type() -> None:
    with pytest.raises(ConfigError, match="max_page_size must be int-like"):
        _ = build_dataset_ref(
            "datago",
            {
                "dataset_key": "test",
                "name": "Test",
                "representation": "api_json",
                "query_support": {"pagination": "offset", "max_page_size": {}},
            },
        )


def test_require_string_field_raises_when_field_missing() -> None:
    with pytest.raises(ConfigError, match="missing non-empty string field"):
        _ = require_string_field({}, "dataset_key", "datago")
