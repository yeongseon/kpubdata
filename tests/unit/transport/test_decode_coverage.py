"""테스트 모듈.

이 파일은 ``tests/unit/transport/test_decode_coverage.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from kpubdata.exceptions import ParseError
from kpubdata.transport.decode import decode_json, decode_xml


# test decode json raises for non utf8 bytes 테스트가 검증하는 시나리오를 설명한다.
def test_decode_json_raises_for_non_utf8_bytes() -> None:
    """
    test decode json raises for non utf8 bytes 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    with pytest.raises(ParseError, match="UTF-8"):
        decode_json(b"\xff\xfe")


# test decode xml raises when parser returns non dict 테스트가 검증하는 시나리오를 설명한다.
def test_decode_xml_raises_when_parser_returns_non_dict(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    test decode xml raises when parser returns non dict 시나리오를 검증한다.

    매개변수:
        monkeypatch (pytest.MonkeyPatch): 호출자가 제공하는 입력 값이다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    fake_module = MagicMock()
    fake_module.parse.return_value = ["not", "a", "dict"]
    monkeypatch.setattr("kpubdata.transport.decode.import_module", lambda _name: fake_module)

    with pytest.raises(ParseError, match="did not decode into a dictionary"):
        _ = decode_xml("<root />")
