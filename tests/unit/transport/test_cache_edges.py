"""``ResponseCache`` 의 가장자리 동작 회귀 테스트 (#454).

캐시는 버그가 조용히 나는 계층이다 — 잘못된 키나 TTL 로 오래된/남의 응답을 돌려줘도
호출부는 정상처럼 보인다. 여기서는 정상 왕복이 아니라 **캐시가 무엇을 돌려주지 않아야
하는가**(만료·손상·형식 불일치)와 **키가 무엇을 구분해야 하는가**를 고정한다.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest

from kpubdata.transport.cache import ResponseCache, make_cache_key


def _write_raw(cache: ResponseCache, key: str, payload: object) -> Path:
    """검증을 우회해 캐시 파일을 직접 쓴다(손상된 엔트리 재현용)."""
    path = cache.base_dir / f"{key}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _entry(
    *, body: bytes = b"cached", created_at: float = 1_000.0, ttl: float = 60.0
) -> dict[str, object]:
    return {
        "created_at": created_at,
        "ttl_seconds": ttl,
        "body_b64": base64.b64encode(body).decode("ascii"),
    }


# --- TTL 경계 --------------------------------------------------------------


def test_entry_is_served_before_its_ttl(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = ResponseCache(base_dir=tmp_path)
    _ = _write_raw(cache, "k", _entry(created_at=1_000.0, ttl=60.0))

    monkeypatch.setattr("kpubdata.transport.cache.time.time", lambda: 1_059.0)
    assert cache.get("k") == b"cached"


def test_entry_expires_exactly_at_its_ttl(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """경계는 닫혀 있다 — created_at + ttl 에 도달하면 이미 만료다."""
    cache = ResponseCache(base_dir=tmp_path)
    path = _write_raw(cache, "k", _entry(created_at=1_000.0, ttl=60.0))

    monkeypatch.setattr("kpubdata.transport.cache.time.time", lambda: 1_060.0)
    assert cache.get("k") is None
    # 만료 엔트리는 읽을 때 지운다 — 디스크에 남겨 두지 않는다.
    assert not path.exists()


def test_zero_ttl_entry_is_never_served(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = ResponseCache(base_dir=tmp_path)
    cache.set("k", b"cached", ttl_seconds=0)
    assert cache.get("k") is None


def test_negative_ttl_entry_is_never_served(tmp_path: Path) -> None:
    """음수 TTL 은 '무한 유효' 가 아니라 즉시 만료다."""
    cache = ResponseCache(base_dir=tmp_path)
    _ = _write_raw(cache, "k", _entry(ttl=-1.0))
    assert cache.get("k") is None


# --- 손상된 엔트리 ---------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "payload"),
    [
        ("not-a-mapping", ["created_at", 1.0]),
        ("missing-body", {"created_at": 1.0, "ttl_seconds": 60.0}),
        ("body-not-a-string", {"created_at": 1.0, "ttl_seconds": 60.0, "body_b64": 12}),
        ("created-at-not-a-number", {"created_at": "now", "ttl_seconds": 60.0, "body_b64": "eA=="}),
        ("ttl-not-a-number", {"created_at": 1.0, "ttl_seconds": "forever", "body_b64": "eA=="}),
    ],
)
def test_malformed_entry_is_dropped_not_served(tmp_path: Path, name: str, payload: object) -> None:
    """형식이 어긋난 엔트리는 예외 없이 미스로 취급하고 파일도 지운다."""
    cache = ResponseCache(base_dir=tmp_path)
    path = _write_raw(cache, name, payload)

    assert cache.get(name) is None
    assert not path.exists()


def test_unparsable_json_entry_is_a_miss(tmp_path: Path) -> None:
    cache = ResponseCache(base_dir=tmp_path)
    path = tmp_path / "broken.json"
    path.write_text("{not json", encoding="utf-8")

    assert cache.get("broken") is None


def test_non_base64_body_is_a_miss(tmp_path: Path) -> None:
    """body_b64 가 base64 가 아니면 디코딩 예외를 삼키고 미스를 반환한다."""
    cache = ResponseCache(base_dir=tmp_path)
    _ = _write_raw(
        cache, "k", {"created_at": 1.0, "ttl_seconds": 10**9, "body_b64": "!!!not-base64!!!"}
    )
    assert cache.get("k") is None


# --- clear / clear_expired -------------------------------------------------


def test_clear_removes_every_entry(tmp_path: Path) -> None:
    cache = ResponseCache(base_dir=tmp_path)
    cache.set("a", b"1", ttl_seconds=600)
    cache.set("b", b"2", ttl_seconds=600)

    cache.clear()

    assert cache.get("a") is None
    assert cache.get("b") is None
    assert list(tmp_path.glob("*.json")) == []


def test_clear_on_a_missing_directory_is_a_noop(tmp_path: Path) -> None:
    cache = ResponseCache(base_dir=tmp_path / "never-created")
    cache.clear()
    cache.clear_expired()


def test_clear_expired_keeps_live_entries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """만료된 것만 지운다 — 유효한 엔트리를 같이 날리면 캐시가 무용지물이 된다."""
    cache = ResponseCache(base_dir=tmp_path)
    _ = _write_raw(cache, "stale", _entry(body=b"old", created_at=0.0, ttl=1.0))
    _ = _write_raw(cache, "fresh", _entry(body=b"new", created_at=0.0, ttl=10**9))

    monkeypatch.setattr("kpubdata.transport.cache.time.time", lambda: 1_000.0)
    cache.clear_expired()

    assert cache.get("stale") is None
    assert cache.get("fresh") == b"new"


def test_clear_expired_drops_malformed_entries(tmp_path: Path) -> None:
    """판정할 수 없는 엔트리도 정리 대상이다 — 영원히 남아 디스크를 먹지 않게."""
    cache = ResponseCache(base_dir=tmp_path)
    path = _write_raw(cache, "junk", {"nothing": "useful"})

    cache.clear_expired()

    assert not path.exists()


def test_clear_expired_ignores_unrelated_files(tmp_path: Path) -> None:
    cache = ResponseCache(base_dir=tmp_path)
    stray = tmp_path / "README.txt"
    stray.write_text("not a cache entry", encoding="utf-8")

    cache.clear()
    cache.clear_expired()

    assert stray.exists()


# --- 캐시 키 ---------------------------------------------------------------


def test_key_is_stable_across_parameter_order() -> None:
    """dict 순서는 키에 영향을 주면 안 된다 — 같은 요청은 같은 엔트리여야 한다."""
    first = make_cache_key("GET", "https://x.test/r", {"a": "1", "b": "2"}, None)
    second = make_cache_key("GET", "https://x.test/r", {"b": "2", "a": "1"}, None)
    assert first == second


def test_key_ignores_method_and_parameter_name_casing() -> None:
    assert make_cache_key("get", "https://x.test/r", {"Page": "1"}, None) == make_cache_key(
        "GET", "https://x.test/r", {"page": "1"}, None
    )


def test_key_separates_different_urls_methods_and_values() -> None:
    base = make_cache_key("GET", "https://x.test/r", {"page": "1"}, None)
    assert base != make_cache_key("GET", "https://x.test/other", {"page": "1"}, None)
    assert base != make_cache_key("POST", "https://x.test/r", {"page": "1"}, None)
    assert base != make_cache_key("GET", "https://x.test/r", {"page": "2"}, None)


def test_key_treats_absent_and_empty_parameters_as_one_request() -> None:
    """None 과 {} 는 같은 요청이다 — 둘을 다른 엔트리로 쪼개 캐시를 반으로 나누지 않는다."""
    assert make_cache_key("GET", "https://x.test/r", None, None) == make_cache_key(
        "GET", "https://x.test/r", {}, None
    )


def test_key_never_contains_the_credential(tmp_path: Path) -> None:
    """키는 파일명이 된다 — 원문 credential 이 디스크 경로에 남으면 안 된다 (#263)."""
    secret = "super-secret-service-key"
    key = make_cache_key("GET", "https://x.test/r", {"serviceKey": secret}, None)
    assert secret not in key
    assert len(key) == 32


def test_key_isolates_header_credentials() -> None:
    """Authorization 헤더가 다르면 같은 URL 이라도 다른 엔트리다."""
    first = make_cache_key("GET", "https://x.test/r", None, {"Authorization": "Bearer a"})
    second = make_cache_key("GET", "https://x.test/r", None, {"Authorization": "Bearer b"})
    assert first != second


def test_key_handles_non_string_parameter_values() -> None:
    """숫자/불리언 파라미터도 문자열로 정규화돼 예외 없이 키가 나온다."""
    key = make_cache_key("GET", "https://x.test/r", {"page": 1, "all": True}, None)
    assert len(key) == 32
    assert key == make_cache_key("GET", "https://x.test/r", {"page": "1", "all": "True"}, None)


# --- 실패를 삼키는 경로 ----------------------------------------------------
#
# 캐시는 보조 계층이다 — 디스크가 말을 듣지 않아도 호출부가 죽으면 안 된다.
# 아래 테스트는 "예외를 밖으로 내보내지 않는다"를 고정한다.


def test_set_failure_does_not_raise(tmp_path: Path) -> None:
    """base_dir 이 파일이면 mkdir 이 실패한다 — 조용히 포기해야 한다."""
    blocked = tmp_path / "blocked"
    blocked.write_text("not a directory", encoding="utf-8")
    cache = ResponseCache(base_dir=blocked)

    cache.set("k", b"payload", ttl_seconds=60)

    assert cache.get("k") is None


def test_clear_failure_does_not_raise(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = ResponseCache(base_dir=tmp_path)
    cache.set("k", b"payload", ttl_seconds=60)

    def exploding_glob(self: Path, pattern: str) -> object:
        raise OSError("glob failed")

    monkeypatch.setattr(Path, "glob", exploding_glob)

    cache.clear()
    cache.clear_expired()


def test_clear_expired_survives_one_unreadable_entry(tmp_path: Path) -> None:
    """엔트리 하나가 읽히지 않아도 나머지 정리는 계속돼야 한다."""
    cache = ResponseCache(base_dir=tmp_path)
    # 디렉터리를 .json 이름으로 두면 read_text 가 IsADirectoryError 를 던진다.
    (tmp_path / "unreadable.json").mkdir()
    stale = _write_raw(cache, "stale", _entry(created_at=0.0, ttl=1.0))

    cache.clear_expired()

    assert (tmp_path / "unreadable.json").exists()
    # 만료 엔트리가 디스크에서 사라졌는지를 본다. ``cache.get`` 은 정리가 중간에
    # 멈췄더라도 실제 시계 기준으로 이미 만료라 None 을 주므로 아무것도 증명하지 못한다.
    assert not stale.exists()


def test_delete_failure_still_reports_a_miss(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """만료 엔트리를 지우지 못해도 값을 돌려주지는 않는다."""
    cache = ResponseCache(base_dir=tmp_path)
    _ = _write_raw(cache, "k", _entry(created_at=0.0, ttl=1.0))

    def exploding_unlink(self: Path, missing_ok: bool = False) -> None:
        raise OSError("unlink failed")

    monkeypatch.setattr(Path, "unlink", exploding_unlink)

    assert cache.get("k") is None


# --- 기본 캐시 디렉터리 ----------------------------------------------------


def test_default_dir_follows_xdg_cache_home(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CACHE_HOME", "/tmp/xdg-probe")
    assert ResponseCache().base_dir == Path("/tmp/xdg-probe/kpubdata/responses")


def test_default_dir_falls_back_to_home(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: Path("/home/probe")))
    assert ResponseCache().base_dir == Path("/home/probe/.cache/kpubdata/responses")


def test_empty_xdg_cache_home_falls_back_to_home(monkeypatch: pytest.MonkeyPatch) -> None:
    """빈 문자열은 '설정 안 함'과 같게 다뤄야 한다 — 루트에 캐시를 만들지 않는다."""
    monkeypatch.setenv("XDG_CACHE_HOME", "")
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: Path("/home/probe")))
    assert ResponseCache().base_dir == Path("/home/probe/.cache/kpubdata/responses")
