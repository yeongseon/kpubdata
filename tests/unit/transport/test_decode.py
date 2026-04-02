"""Tests for transport decode utilities."""

from __future__ import annotations

import pytest

from kpubdata.transport.decode import decode_json, decode_xml, detect_content_type


class FakeResponse:
    def __init__(self, content_type: str) -> None:
        self.headers = {"content-type": content_type}


class TestDetectContentType:
    def test_json(self) -> None:
        assert detect_content_type(FakeResponse("application/json; charset=utf-8")) == "json"

    def test_xml(self) -> None:
        assert detect_content_type(FakeResponse("text/xml")) == "xml"

    def test_other(self) -> None:
        assert detect_content_type(FakeResponse("text/plain")) == "other"


class TestDecodeJson:
    def test_string(self) -> None:
        assert decode_json('{"a": 1}') == {"a": 1}

    def test_bytes(self) -> None:
        assert decode_json(b'{"a": 1}') == {"a": 1}

    def test_invalid(self) -> None:
        with pytest.raises(ValueError, match="decode JSON"):
            decode_json("not json")


class TestDecodeXml:
    def test_missing_xmltodict(self) -> None:
        # This test passes if xmltodict is not installed
        # If xmltodict IS installed, we test actual decoding
        try:
            import xmltodict  # noqa: F401

            result = decode_xml("<root><item>1</item></root>")
            assert isinstance(result, dict)
        except ImportError:
            with pytest.raises(ImportError, match="xmltodict"):
                decode_xml("<root/>")
