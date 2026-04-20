from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import time
from collections.abc import Mapping
from pathlib import Path
from typing import TypedDict, cast

logger = logging.getLogger("kpubdata.transport")


class _CachePayload(TypedDict, total=False):
    created_at: float
    ttl_seconds: float
    body_b64: str


_REDACTED_VALUE = "[REDACTED]"
_SENSITIVE_CACHE_KEY_NAMES = {
    "servicekey",
    "service_key",
    "api_key",
    "apikey",
    "token",
    "authorization",
    "secret",
    "password",
    "key",
}


class ResponseCache:
    def __init__(self, base_dir: str | Path | None = None) -> None:
        self._base_dir: Path = Path(base_dir) if base_dir is not None else _default_cache_dir()

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    def get(self, key: str) -> bytes | None:
        payload_path = self._payload_path(key)
        try:
            if not payload_path.exists():
                return None
            payload = _load_payload(payload_path)
            if payload is None:
                self._delete_entry(key)
                return None
            if _is_expired(payload):
                self._delete_entry(key)
                return None
            body_b64 = payload.get("body_b64")
            if body_b64 is None:
                self._delete_entry(key)
                return None
            return base64.b64decode(body_b64.encode("ascii"))
        except Exception as exc:
            logger.debug(
                "transport cache read failed",
                extra={
                    "cache_key": key,
                    "path": str(payload_path),
                    "exception_type": type(exc).__name__,
                },
            )
            return None

    def set(self, key: str, value: bytes, ttl_seconds: int) -> None:
        payload_path = self._payload_path(key)
        try:
            payload_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "created_at": time.time(),
                "ttl_seconds": ttl_seconds,
                "body_b64": base64.b64encode(value).decode("ascii"),
            }
            _ = payload_path.write_text(
                json.dumps(payload, separators=(",", ":")),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.debug(
                "transport cache write failed",
                extra={
                    "cache_key": key,
                    "path": str(payload_path),
                    "exception_type": type(exc).__name__,
                },
            )

    def clear(self) -> None:
        try:
            if not self._base_dir.exists():
                return
            for payload_path in self._base_dir.glob("*.json"):
                payload_path.unlink(missing_ok=True)
        except Exception as exc:
            logger.debug(
                "transport cache clear failed",
                extra={"path": str(self._base_dir), "exception_type": type(exc).__name__},
            )

    def clear_expired(self) -> None:
        try:
            if not self._base_dir.exists():
                return
            for payload_path in self._base_dir.glob("*.json"):
                try:
                    payload = _load_payload(payload_path)
                    if payload is None or _is_expired(payload):
                        payload_path.unlink(missing_ok=True)
                except Exception as exc:
                    logger.debug(
                        "transport cache cleanup entry failed",
                        extra={
                            "path": str(payload_path),
                            "exception_type": type(exc).__name__,
                        },
                    )
        except Exception as exc:
            logger.debug(
                "transport cache cleanup failed",
                extra={"path": str(self._base_dir), "exception_type": type(exc).__name__},
            )

    def _payload_path(self, key: str) -> Path:
        return self._base_dir / f"{key}.json"

    def _delete_entry(self, key: str) -> None:
        try:
            self._payload_path(key).unlink(missing_ok=True)
        except Exception as exc:
            logger.debug(
                "transport cache delete failed",
                extra={
                    "cache_key": key,
                    "path": str(self._payload_path(key)),
                    "exception_type": type(exc).__name__,
                },
            )


def make_cache_key(
    method: str,
    url: str,
    params: Mapping[str, object] | None,
    headers_subset: Mapping[str, object] | None,
) -> str:
    normalized_payload = {
        "method": method.upper(),
        "url": url,
        "params": _normalize_mapping(params),
        "headers": _normalize_mapping(headers_subset),
    }
    digest = hashlib.sha256(
        json.dumps(normalized_payload, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return digest[:32]


def _default_cache_dir() -> Path:
    xdg_cache_home = os.environ.get("XDG_CACHE_HOME")
    if xdg_cache_home:
        return Path(xdg_cache_home) / "kpubdata" / "responses"
    return Path.home() / ".cache" / "kpubdata" / "responses"


def _normalize_mapping(values: Mapping[str, object] | None) -> list[tuple[str, str]]:
    if values is None:
        return []

    normalized_items: list[tuple[str, str]] = []
    for key, value in values.items():
        normalized_value = (
            _REDACTED_VALUE if key.casefold() in _SENSITIVE_CACHE_KEY_NAMES else str(value)
        )
        normalized_items.append((key.casefold(), normalized_value))
    normalized_items.sort()
    return normalized_items


def _is_expired(payload: _CachePayload) -> bool:
    created_at = payload.get("created_at")
    ttl_seconds = payload.get("ttl_seconds")
    if not isinstance(created_at, int | float) or not isinstance(ttl_seconds, int | float):
        return True
    if ttl_seconds < 0:
        return True
    return time.time() >= created_at + ttl_seconds


def _load_payload(payload_path: Path) -> _CachePayload | None:
    raw_payload = cast(object, json.loads(payload_path.read_text(encoding="utf-8")))
    if not isinstance(raw_payload, dict):
        return None
    payload = cast(_CachePayload, cast(object, raw_payload))
    body_b64 = payload.get("body_b64")
    created_at = payload.get("created_at")
    ttl_seconds = payload.get("ttl_seconds")
    if not isinstance(body_b64, str):
        return None
    if not isinstance(created_at, int | float) or not isinstance(ttl_seconds, int | float):
        return None
    return payload


__all__ = ["ResponseCache", "make_cache_key"]
