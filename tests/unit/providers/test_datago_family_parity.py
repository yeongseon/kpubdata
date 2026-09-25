"""localdata 와 semas 가 같은 규약을 실제로 공유하는지 (#470 회귀 방지).

두 어댑터는 375줄짜리 사본 두 벌이었다. 이름 문자열을 맞춰 비교하면 코드 차이가
0줄이었는데, 그 상태가 바로 #470 을 만들었다 — data.go.kr 의 ``"03"``(NODATA)을
정상으로 다루는 분기가 semas 에만 있어서, 결과가 없는 흔한 조회가 localdata
에서만 예외로 올라왔다. 한쪽을 고치면 다른 쪽도 고쳐야 한다는 사실이 코드
어디에도 없었다.

이제 공용 base 하나를 상속한다. 이 테스트는 그 사실을 계약으로 고정한다.
"""

from __future__ import annotations

from typing import Any

import pytest

from kpubdata.providers._datago_family import DataGoFamilyAdapter
from kpubdata.providers.localdata.adapter import LocaldataAdapter
from kpubdata.providers.semas.adapter import SemasAdapter

_ADAPTERS = (LocaldataAdapter, SemasAdapter)


def _envelope(result_code: str, items: object = None) -> dict[str, object]:
    body: dict[str, object] = {} if items is None else {"items": items}
    return {"response": {"header": {"resultCode": result_code, "resultMsg": "m"}, "body": body}}


class TestBothShareTheImplementation:
    @pytest.mark.parametrize("adapter_cls", _ADAPTERS)
    def test_it_is_the_shared_base(self, adapter_cls: type[Any]) -> None:
        assert issubclass(adapter_cls, DataGoFamilyAdapter)

    @pytest.mark.parametrize("adapter_cls", _ADAPTERS)
    def test_it_declares_its_own_identity(self, adapter_cls: type[Any]) -> None:
        adapter = adapter_cls()

        assert adapter.name == adapter_cls.provider_name
        assert adapter.list_datasets(), "카탈로그가 비면 안 된다"
        assert all(d.id.startswith(f"{adapter.name}.") for d in adapter.list_datasets())


class TestTheEnvelopeRulesMatch:
    """#470 의 핵심 — 두 provider 가 같은 resultCode 에 같은 반응을 해야 한다."""

    @pytest.mark.parametrize("adapter_cls", _ADAPTERS)
    def test_nodata_is_a_success(self, adapter_cls: type[Any]) -> None:
        """``03`` 은 "조건에 맞는 데이터가 없다" 이지 호출 실패가 아니다."""
        _body, items = adapter_cls()._validate_envelope(_envelope("03", [{"x": 1}]), "x")

        assert items == []

    @pytest.mark.parametrize("adapter_cls", _ADAPTERS)
    def test_success_returns_items(self, adapter_cls: type[Any]) -> None:
        _body, items = adapter_cls()._validate_envelope(_envelope("00", [{"x": 1}]), "x")

        assert items == [{"x": 1}]

    @pytest.mark.parametrize("adapter_cls", _ADAPTERS)
    @pytest.mark.parametrize(
        ("code", "exception_name"),
        [("30", "AuthError"), ("22", "RateLimitError")],
    )
    def test_real_errors_still_raise(
        self, adapter_cls: type[Any], code: str, exception_name: str
    ) -> None:
        with pytest.raises(Exception) as excinfo:  # noqa: B017 - 타입 이름만 비교한다
            _ = adapter_cls()._validate_envelope(_envelope(code), "x")

        assert type(excinfo.value).__name__ == exception_name


class TestItemNormalisationMatches:
    """#482 에서 한쪽만 고쳐 유령 행이 생겼던 지점 (#483 에서 되돌림)."""

    @pytest.mark.parametrize("adapter_cls", _ADAPTERS)
    @pytest.mark.parametrize(
        ("wrapper", "expected"),
        [
            ({"item": [{"a": 1}, {"a": 2}]}, [{"a": 1}, {"a": 2}]),
            ({"item": {"a": 1}}, [{"a": 1}]),
            ({"item": None}, []),
            ({}, []),
            ({"a": 1}, [{"a": 1}]),
        ],
    )
    def test_shapes_normalise_identically(
        self, adapter_cls: type[Any], wrapper: object, expected: list[dict[str, object]]
    ) -> None:
        assert adapter_cls()._normalize_items(wrapper) == expected
