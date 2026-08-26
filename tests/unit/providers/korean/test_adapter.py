"""국립국어원 어댑터 단위 테스트 (#222)."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import Query
from kpubdata.exceptions import AuthError, InvalidRequestError
from kpubdata.providers.korean.adapter import KoreanAdapter
from kpubdata.transport.http import HttpTransport
from tests.unit.providers.datago.conftest import FakeResponse

_FIXTURE_DIR = Path(__file__).parents[3] / "fixtures" / "korean"


def _load(name: str) -> bytes:
    return (_FIXTURE_DIR / name).read_bytes()


def _build_adapter(fixture_names: list[str]) -> tuple[KoreanAdapter, object]:
    class _Transport:
        def __init__(self, names: list[str]) -> None:
            self._responses = [FakeResponse(_load(n)) for n in names]
            self.calls: list[dict[str, object]] = []

        def request(self, method: str, url: str, **kwargs: object) -> FakeResponse:
            self.calls.append({"method": method, "url": url, **kwargs})
            return self._responses.pop(0)

    transport = _Transport(fixture_names)
    adapter = KoreanAdapter(
        config=KPubDataConfig(provider_keys={"korean": "STDICT-KEY-1"}),
        transport=cast(HttpTransport, cast(object, transport)),
    )
    return adapter, transport


def test_query_records_builds_stdict_url() -> None:
    """stdict search.do URL 형상(key/type_search/req_type/start/num/q)을 검증한다."""
    adapter, transport = _build_adapter(["dict_search.json"])
    dataset = adapter.get_dataset("dict_search")

    batch = adapter.query_records(dataset, Query(filters={"q": "나무"}, page_size=10))

    call = transport.calls[0]
    url = str(call["url"])
    assert url.startswith("https://stdict.korean.go.kr/api/search.do?")
    assert "key=STDICT-KEY-1" in url
    assert "type_search=search" in url
    assert "req_type=json" in url
    assert "start=1" in url
    assert "num=10" in url
    assert "q=" in url

    # 다의어가 sense 단위로 펼쳐진다(나무 2 sense + 나무꾼 1 sense = 3 records)
    assert len(batch.items) == 3
    assert batch.items[0]["word"] == "나무"
    assert "줄기와 가지" in str(batch.items[0]["sense"]["definition"])
    assert batch.total_count == 2
    assert batch.next_page is None


def test_query_records_missing_q_raises() -> None:
    """필수 filter q 누락 시 InvalidRequestError."""
    adapter, _ = _build_adapter(["dict_search.json"])
    dataset = adapter.get_dataset("dict_search")

    try:
        adapter.query_records(dataset, Query())
    except InvalidRequestError as exc:
        assert "q" in str(exc)
    else:
        raise AssertionError("q 누락이 예외로 나야 한다")


def test_auth_error_maps_to_auth_error() -> None:
    """statusCode 019(인증 오류)는 AuthError로 매핑된다."""
    adapter, _ = _build_adapter(["auth_error.json"])
    dataset = adapter.get_dataset("dict_search")

    try:
        adapter.query_records(dataset, Query(filters={"q": "나무"}))
    except AuthError:
        pass
    else:
        raise AssertionError("019는 AuthError로 매핑되어야 한다")


def test_pagination_next_page_from_total() -> None:
    """total이 페이지 범위를 넘으면 next_page가 계산된다."""
    adapter, _ = _build_adapter(["dict_search.json"])
    dataset = adapter.get_dataset("dict_search")

    batch = adapter.query_records(dataset, Query(filters={"q": "나무"}, page=1, page_size=1))

    assert batch.total_count == 2
    assert batch.next_page == 2


def test_call_raw_returns_full_envelope() -> None:
    """call_raw가 channel 엔벨로프 전체를 반환한다."""
    adapter, _ = _build_adapter(["dict_search.json"])
    dataset = adapter.get_dataset("dict_search")

    payload = adapter.call_raw(dataset, "search.do", {"q": "나무"})

    assert "channel" in cast(dict, payload)
