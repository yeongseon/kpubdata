from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from kpubdata.exceptions import ParseError
from kpubdata.transport.decode import decode_json, decode_xml


def test_decode_json_raises_for_non_utf8_bytes() -> None:
    with pytest.raises(ParseError, match="UTF-8"):
        decode_json(b"\xff\xfe")


def test_decode_xml_raises_when_parser_returns_non_dict(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_module = MagicMock()
    fake_module.parse.return_value = ["not", "a", "dict"]
    monkeypatch.setattr("kpubdata.transport.decode.import_module", lambda _name: fake_module)

    with pytest.raises(ParseError, match="did not decode into a dictionary"):
        _ = decode_xml("<root />")
