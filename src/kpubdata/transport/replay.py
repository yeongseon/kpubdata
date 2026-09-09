"""재생(replay) 전송 계층 — 기록된 fixture로 실호출을 대체한다.

``KPUBDATA_MODE=replay`` 환경 변수가 설정되면 ``HttpTransport.request``가
이 모듈을 호출한다.

개입 조건(좁은 범위): 요청의 ``dataset_id``와 URL이 fixture 인덱스에
(데이터셋, 엔드포인트) 쌍으로 등록된 경우만 매칭을 시도한다. 그 외 요청은
``None``을 반환해 실호출 경로로 통과시킨다 — 전역 가로채기는 무관한 전송
계층 단위 테스트를 깨뜨리므로 하지 않는다.

- fixture 루트: ``KPUBDATA_REPLAY_DIR`` (기본: ``./tests/fixtures``)
- 매칭 키: 엔드포인트 + 민감(인증) 파라미터를 제외한 파라미터 전부
- 등록된 조합인데 파라미터가 다르면 "make record" 안내와 함께 실패한다 —
  지어낸 응답 없이, 결정적 검증만.
- 개발·CI 전용 모드다(설치 환경에서는 fixture가 없으므로 미지정이 기본).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import httpx

from kpubdata.exceptions import InvalidRequestError

_DEFAULT_ROOT = Path("tests") / "fixtures"
# 인증 계열 파라미터는 값이 환경마다 달라 매칭에서 제외한다.
_SENSITIVE_PARAM_KEYS = frozenset(
    {"servicekey", "service_key", "apikey", "api_key", "key", "token", "secret", "oc"}
)

_IndexEntry = tuple[str, str, str, Path]


def _iter_index(root: Path) -> list[_IndexEntry]:
    """fixture 인덱스를 (dataset_id, example, endpoint, meta 경로)로 순회한다."""
    index: list[_IndexEntry] = []
    for meta_path in sorted(root.rglob("*.meta.json")):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        index.append(
            (
                str(meta.get("dataset_id", "?")),
                str(meta.get("example", "?")),
                str(meta.get("endpoint", "")),
                meta_path,
            )
        )
    return index


def _signature(params: dict[str, str] | None) -> dict[str, str]:
    """민감 파라미터를 제외한 소문자 키 시그니처를 만든다."""
    return {
        key.lower(): value
        for key, value in (params or {}).items()
        if key.lower() not in _SENSITIVE_PARAM_KEYS
    }


def replay_response(
    method: str,
    url: str,
    *,
    params: dict[str, str] | None = None,
    dataset_id: str | None = None,
    provider: str | None = None,
) -> httpx.Response | None:
    """등록된 (데이터셋, 엔드포인트) 요청을 기록 응답으로 대체한다.

    반환값:
        기록 응답(매칭 성공) 또는 None(개입 대상 아님 — 실호출로 통과).

    예외:
        InvalidRequestError: 등록된 조합인데 파라미터가 매칭되지 않는 경우.
    """
    root = Path(os.environ.get("KPUBDATA_REPLAY_DIR", str(_DEFAULT_ROOT)))
    index = _iter_index(root) if root.is_dir() else []

    if dataset_id is None or (dataset_id, url) not in {
        (dataset, endpoint) for dataset, _, endpoint, _ in index
    }:
        return None

    signature = _signature(params)
    candidates: list[tuple[str, str, Path]] = []
    for dataset, example, endpoint, meta_path in index:
        if endpoint != url:
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta_params = _signature(
            {str(key): str(value) for key, value in dict(meta.get("params", {})).items()}
        )
        if meta_params == signature:
            raw_path = meta_path.with_name(meta_path.name.replace(".meta.json", ".raw.json"))
            if raw_path.is_file():
                candidates.append((dataset, example, raw_path))

    if not candidates:
        available = sorted({f"{did}.{ex}" for did, ex, _, _ in index})
        hint = f" — 사용 가능: {', '.join(available[:10])}" if available else ""
        msg = (
            f"replay 매칭 실패: {dataset_id} ({method} {url}, params={signature}). "
            f"`make record DATASET=...` 로 fixture를 먼저 기록하세요{hint}"
        )
        raise InvalidRequestError(msg, provider=provider, dataset_id=dataset_id)

    dataset, example, raw_path = candidates[0]
    payload_text = raw_path.read_text(encoding="utf-8")
    response = httpx.Response(
        status_code=200,
        content=payload_text.encode("utf-8"),
        headers={"content-type": "application/json"},
        request=httpx.Request(method, url),
    )
    response.extensions["kpubdata_replay"] = {"dataset_id": dataset, "example": example}
    return response


__all__ = ["replay_response"]
