"""Tests for transport decode utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from kpubdata.exceptions import ParseError
from kpubdata.transport.decode import decode_json, decode_xml, detect_content_type


class FakeResponse:
    """
    FakeResponse 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/transport/test_decode.py`` 모듈 안에서 FakeResponse의 상태와 동작을 함께 관리한다.
    주요 메서드: __init__.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    def __init__(self, content_type: str) -> None:
        """
        인스턴스가 사용할 내부 상태를 초기화한다.

        매개변수:
            content_type (str): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
        """
        self.headers = {"content-type": content_type}


class TestDetectContentType:
    """
    TestDetectContentType 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/transport/test_decode.py`` 모듈 안에서 TestDetectContentType의 상태와 동작을 함께 관리한다.
    주요 메서드: test_json, test_xml, test_other.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    # test json 테스트가 검증하는 시나리오를 설명한다.
    def test_json(self) -> None:
        """
        test json 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        assert detect_content_type(FakeResponse("application/json; charset=utf-8")) == "json"

    # test xml 테스트가 검증하는 시나리오를 설명한다.
    def test_xml(self) -> None:
        """
        test xml 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        assert detect_content_type(FakeResponse("text/xml")) == "xml"

    # test other 테스트가 검증하는 시나리오를 설명한다.
    def test_other(self) -> None:
        """
        test other 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        assert detect_content_type(FakeResponse("text/plain")) == "other"


class TestDecodeJson:
    """
    TestDecodeJson 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/transport/test_decode.py`` 모듈 안에서 TestDecodeJson의 상태와 동작을 함께 관리한다.
    주요 메서드: test_string, test_bytes, test_invalid.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    # test string 테스트가 검증하는 시나리오를 설명한다.
    def test_string(self) -> None:
        """
        test string 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        assert decode_json('{"a": 1}') == {"a": 1}

    # test bytes 테스트가 검증하는 시나리오를 설명한다.
    def test_bytes(self) -> None:
        """
        test bytes 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        assert decode_json(b'{"a": 1}') == {"a": 1}

    # test invalid 테스트가 검증하는 시나리오를 설명한다.
    def test_invalid(self) -> None:
        """
        test invalid 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        with pytest.raises(ParseError, match="decode JSON"):
            decode_json("not json")


class TestDecodeXml:
    """
    TestDecodeXml 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/transport/test_decode.py`` 모듈 안에서 TestDecodeXml의 상태와 동작을 함께 관리한다.
    주요 메서드: test_real_fixture_string, test_real_fixture_bytes, test_single_item_returns_dict_not_list, test_invalid_xml_raises_parse_error, test_missing_xmltodict_raises_import_error.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    # test real fixture string 테스트가 검증하는 시나리오를 설명한다.
    def test_real_fixture_string(self) -> None:
        """
        test real fixture string 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        xml_path = Path(__file__).resolve().parents[2] / "fixtures" / "datago" / "success_xml.xml"
        xml_text = xml_path.read_text(encoding="utf-8")
        result = decode_xml(xml_text)
        assert isinstance(result, dict)

        body = result["response"]["body"]
        items = body["items"]["item"]
        assert isinstance(items, list)
        assert items[0]["stationName"] == "종로구"
        assert items[1]["stationName"] == "강남구"

    # test real fixture bytes 테스트가 검증하는 시나리오를 설명한다.
    def test_real_fixture_bytes(self) -> None:
        """
        test real fixture bytes 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        xml_path = Path(__file__).resolve().parents[2] / "fixtures" / "datago" / "success_xml.xml"
        xml_bytes = xml_path.read_bytes()
        result = decode_xml(xml_bytes)
        assert isinstance(result, dict)
        assert result["response"]["header"]["resultCode"] == "00"

    # test single item returns dict not list 테스트가 검증하는 시나리오를 설명한다.
    def test_single_item_returns_dict_not_list(self) -> None:
        """
        test single item returns dict not list 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        xml_path = (
            Path(__file__).resolve().parents[2]
            / "fixtures"
            / "datago"
            / "success_xml_single_item.xml"
        )
        xml_text = xml_path.read_text(encoding="utf-8")
        result = decode_xml(xml_text)
        item = result["response"]["body"]["items"]["item"]

        assert isinstance(item, dict)
        assert item["stationName"] == "종로구"

    # test invalid xml raises parse error 테스트가 검증하는 시나리오를 설명한다.
    def test_invalid_xml_raises_parse_error(self) -> None:
        """
        test invalid xml raises parse error 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        with pytest.raises(ParseError, match="Failed to decode XML"):
            decode_xml("<<<not xml>>>")

    # test missing xmltodict raises import error 테스트가 검증하는 시나리오를 설명한다.
    def test_missing_xmltodict_raises_import_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        test missing xmltodict raises import error 시나리오를 검증한다.

        매개변수:
            monkeypatch (pytest.MonkeyPatch): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        def _mock_import(name: str) -> None:
            """
            내부 헬퍼로서 mock import 처리를 담당한다.

            매개변수:
                name (str): 호출자가 제공하는 입력 값이다.

            반환값:
                None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

            예외:
                구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.
            """
            raise ImportError("No module named 'xmltodict'")

        monkeypatch.setattr("kpubdata.transport.decode.import_module", _mock_import)
        with pytest.raises(ImportError, match="kpubdata\\[xml\\]"):
            decode_xml("<root/>")

    # test bytes utf8 decode error 테스트가 검증하는 시나리오를 설명한다.
    def test_bytes_utf8_decode_error(self) -> None:
        """
        test bytes utf8 decode error 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        bad_bytes = b"\xff\xfe<root/>"
        with pytest.raises(ParseError, match="UTF-8"):
            decode_xml(bad_bytes)
