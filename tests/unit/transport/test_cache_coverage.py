"""cache.py 미커버 라인을 보강하는 추가 테스트."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from kpubdata.transport.cache import (
    ResponseCache,
    _default_cache_dir,
    _is_expired,
    _load_payload,
    _normalize_mapping,
    make_cache_key,
)


# -- get(): 손상된 payload (body_b64 누락) --


def test_get_missing_body_b64_deletes_entry(tmp_path: Path) -> None:
    """body_b64 필드가 없는 payload를 읽으면 None을 반환하고 파일을 삭제한다."""
    cache = ResponseCache(base_dir=tmp_path)
    payload_path = tmp_path / "broken.json"
    payload_path.write_text(
        json.dumps({"created_at": 1.0, "ttl_seconds": 9999}),
        encoding="utf-8",
    )

    assert cache.get("broken") is None
    assert not payload_path.exists()


def test_get_invalid_json_returns_none(tmp_path: Path) -> None:
    """JSON 파싱 실패 시 None을 반환한다."""
    cache = ResponseCache(base_dir=tmp_path)
    payload_path = tmp_path / "bad.json"
    payload_path.write_text("NOT-JSON{{", encoding="utf-8")

    assert cache.get("bad") is None


def test_get_non_dict_json_returns_none(tmp_path: Path) -> None:
    """JSON이 dict가 아닌 경우(리스트 등) None을 반환하고 파일을 삭제한다."""
    cache = ResponseCache(base_dir=tmp_path)
    payload_path = tmp_path / "listjson.json"
    payload_path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

    assert cache.get("listjson") is None
    assert not payload_path.exists()


# -- clear() --


def test_clear_removes_all_entries(tmp_path: Path) -> None:
    """clear()가 저장된 모든 캐시 파일을 삭제한다."""
    cache = ResponseCache(base_dir=tmp_path)
    cache.set("a", b"data-a", ttl_seconds=60)
    cache.set("b", b"data-b", ttl_seconds=60)

    assert len(list(tmp_path.glob("*.json"))) == 2

    cache.clear()

    assert list(tmp_path.glob("*.json")) == []


# -- clear_expired() --


def test_clear_expired_removes_only_expired(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """만료된 엔트리만 삭제하고 유효한 엔트리는 보존한다."""
    cache = ResponseCache(base_dir=tmp_path)
    now = 1_000_000.0

    monkeypatch.setattr("kpubdata.transport.cache.time.time", lambda: now)
    cache.set("fresh", b"still-valid", ttl_seconds=300)
    cache.set("stale", b"expired", ttl_seconds=1)

    # 시간 경과 후 만료
    monkeypatch.setattr("kpubdata.transport.cache.time.time", lambda: now + 10)
    cache.clear_expired()

    assert cache.get("fresh") == b"still-valid"
    assert not (tmp_path / "stale.json").exists()


def test_clear_expired_handles_corrupt_entry(tmp_path: Path) -> None:
    """손상된 JSON 파일도 clear_expired()에서 정상적으로 정리된다."""
    cache = ResponseCache(base_dir=tmp_path)
    cache.set("good", b"ok", ttl_seconds=9999)

    corrupt_path = tmp_path / "corrupt.json"
    corrupt_path.write_text("NOT-JSON", encoding="utf-8")

    # 예외 없이 완료됨
    cache.clear_expired()

    # 정상 파일은 보존, 손상 파일은 삭제됨 (load 실패 → None → unlink)
    assert cache.get("good") == b"ok"


# -- _delete_entry() 예외 처리 --


def test_delete_entry_permission_error(tmp_path: Path) -> None:
    """_delete_entry에서 예외가 발생해도 조용히 처리된다."""
    cache = ResponseCache(base_dir=tmp_path)
    cache.set("perm", b"data", ttl_seconds=60)

    with patch.object(Path, "unlink", side_effect=PermissionError("권한 없음")):
        # 예외 없이 완료
        cache._delete_entry("perm")


# -- _default_cache_dir() --


def test_default_cache_dir_with_xdg(monkeypatch: pytest.MonkeyPatch) -> None:
    """XDG_CACHE_HOME이 설정되면 해당 경로를 기반으로 캐시 디렉터리를 구성한다."""
    monkeypatch.setenv("XDG_CACHE_HOME", "/custom/cache")
    result = _default_cache_dir()
    assert result == Path("/custom/cache/kpubdata/responses")


def test_default_cache_dir_without_xdg(monkeypatch: pytest.MonkeyPatch) -> None:
    """XDG_CACHE_HOME이 없으면 ~/.cache/kpubdata/responses를 사용한다."""
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    result = _default_cache_dir()
    assert result == Path.home() / ".cache" / "kpubdata" / "responses"


# -- _is_expired() --


def test_is_expired_negative_ttl() -> None:
    """음수 TTL은 만료로 판단한다."""
    payload = {"created_at": 1_000_000.0, "ttl_seconds": -1.0, "body_b64": ""}
    assert _is_expired(payload) is True


def test_is_expired_non_numeric_created_at() -> None:
    """created_at가 숫자가 아니면 만료로 판단한다."""
    payload = {"created_at": "not-a-number", "ttl_seconds": 60.0, "body_b64": ""}
    assert _is_expired(payload) is True


def test_is_expired_non_numeric_ttl() -> None:
    """ttl_seconds가 숫자가 아니면 만료로 판단한다."""
    payload = {"created_at": 1_000_000.0, "ttl_seconds": "sixty", "body_b64": ""}
    assert _is_expired(payload) is True


# -- _load_payload() --


def test_load_payload_non_dict_json(tmp_path: Path) -> None:
    """JSON이 dict가 아닌 경우 None을 반환한다."""
    p = tmp_path / "list.json"
    p.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    assert _load_payload(p) is None


def test_load_payload_missing_body_b64(tmp_path: Path) -> None:
    """body_b64가 없으면 None을 반환한다."""
    p = tmp_path / "no_body.json"
    p.write_text(json.dumps({"created_at": 1.0, "ttl_seconds": 60}), encoding="utf-8")
    assert _load_payload(p) is None


def test_load_payload_non_numeric_fields(tmp_path: Path) -> None:
    """created_at/ttl_seconds가 숫자가 아니면 None을 반환한다."""
    p = tmp_path / "bad_types.json"
    p.write_text(
        json.dumps({"created_at": "abc", "ttl_seconds": "def", "body_b64": "aGVsbG8="}),
        encoding="utf-8",
    )
    assert _load_payload(p) is None


# -- _normalize_mapping() --


def test_normalize_mapping_none() -> None:
    """None 입력 시 빈 리스트를 반환한다."""
    assert _normalize_mapping(None) == []
