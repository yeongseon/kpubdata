"""실행 경로와 verify 경로가 같은 구현을 써야 한다.

``SpecExecutor._check_error``/``_extract_items`` 가 모듈 함수
``check_payload_error``/``extract_items`` 와 **따로** 구현돼 있었다. 모듈 쪽은
``make verify`` 와 ``make record`` 가 쓰고, 메서드 쪽은 실제 질의가 쓴다. 두 벌이
갈라지면서 모듈 쪽에만 네 가지가 추가됐다 — ``err_field`` style, ``{operation}``
치환, KorService 류 최상단 ``resultCode`` 폴백, ``resultMsg``/``errMsg`` 폴백,
그리고 ``extract_items`` 쪽의 ``neis_double_list`` 와 ``$`` 루트.

그래서 "verify 통과" 가 실행 경로를 검증한다는 보장이 없었다. 지금 저장소에
실린 spec(datago·localdata 23개)은 그 기능을 쓰지 않으므로 당장 깨지는 것은
없지만, 그 기능을 쓰는 spec 이 들어오는 순간 verify 는 통과하고 실행은 실패한다.
"""

from __future__ import annotations

import dataclasses
import pathlib

import pytest

from kpubdata.core.executor import SpecExecutor, check_payload_error, extract_items
from kpubdata.core.spec import SpecDefinition, load_spec_file
from kpubdata.exceptions import ProviderResponseError, RateLimitError

_SPEC_DIR = pathlib.Path(__file__).resolve().parents[3] / "src" / "kpubdata" / "specs" / "datago"


@pytest.fixture()
def spec() -> SpecDefinition:
    return load_spec_file(sorted(_SPEC_DIR.glob("*.yaml"))[0])


@pytest.fixture()
def executor() -> SpecExecutor:
    return SpecExecutor.__new__(SpecExecutor)


def _with_error_style(spec: SpecDefinition, style: str) -> SpecDefinition:
    error = dataclasses.replace(spec.response.error, style=style)
    return dataclasses.replace(spec, response=dataclasses.replace(spec.response, error=error))


class TestTheRuntimePathHasTheSameCapabilities:
    def test_root_items_path(self, spec: SpecDefinition, executor: SpecExecutor) -> None:
        """``$`` 는 루트를 가리킨다 (kosis 최상위 배열). 예전에는 빈 목록이었다."""
        rooted = dataclasses.replace(
            spec, response=dataclasses.replace(spec.response, items_path="$")
        )

        assert executor._extract_items(rooted, {"x": 1}) == [{"x": 1}]

    def test_err_field_style_accepts_a_success(
        self, spec: SpecDefinition, executor: SpecExecutor
    ) -> None:
        """kosis 류는 코드 체계가 없다 — 예전에는 성공 응답이 오히려 실패했다."""
        executor._check_error(_with_error_style(spec, "err_field"), {"result": [{"a": 1}]})

    def test_err_field_style_rejects_a_failure(
        self, spec: SpecDefinition, executor: SpecExecutor
    ) -> None:
        with pytest.raises(ProviderResponseError, match="quota exceeded"):
            executor._check_error(_with_error_style(spec, "err_field"), {"err": "quota exceeded"})

    def test_the_top_level_result_code_fallback(
        self, spec: SpecDefinition, executor: SpecExecutor
    ) -> None:
        """KorService 류는 에러를 envelope 밖 최상단으로 평면 반환한다."""
        with pytest.raises(RateLimitError):
            executor._check_error(spec, {"resultCode": "22", "resultMsg": "LIMITED"})


class TestBothPathsAgree:
    """두 경로가 같은 입력에 같은 답을 내는지 — 갈라짐을 막는 고정핀."""

    @pytest.mark.parametrize(
        "payload",
        [
            {"response": {"header": {"resultCode": "00"}, "body": {"items": {"item": []}}}},
            {"resultCode": "22", "resultMsg": "LIMITED"},
            {"err": "boom"},
            {"unexpected": True},
        ],
    )
    def test_check_error_agrees(
        self, spec: SpecDefinition, executor: SpecExecutor, payload: dict[str, object]
    ) -> None:
        def _outcome(call: object) -> str:
            try:
                call()  # type: ignore[operator]
            except Exception as exc:
                return type(exc).__name__
            return "ok"

        assert _outcome(lambda: executor._check_error(spec, payload)) == _outcome(
            lambda: check_payload_error(spec, payload)
        )

    @pytest.mark.parametrize(
        "payload",
        [
            {"response": {"body": {"items": {"item": [{"a": 1}]}}}},
            {"response": {"body": {"items": {}}}},
            {},
        ],
    )
    def test_extract_items_agrees(
        self, spec: SpecDefinition, executor: SpecExecutor, payload: dict[str, object]
    ) -> None:
        assert executor._extract_items(spec, payload) == extract_items(spec, payload)
