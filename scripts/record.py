"""Fixture 기록 도구 — spec의 examples[]로 실API를 호출해 검증 자산을 남긴다.

사용법:
    KPUBDATA_DATAGO_API_KEY=... uv run python scripts/record.py datago.apt_trade
    make record DATASET=datago.apt_trade

데이터셋별 examples 각각에 대해 세 파일을 남긴다:
- ``{example}.raw.json``     — 정화된 원본 페이로드
- ``{example}.meta.json``    — 호출 시각·endpoint·파라미터(키 제외)·해시·실행 주체
- ``{example}.expected.json``— 정규화 결과 스냅샷(items·total_count)

meta가 없는 fixture는 verify에서 실패 처리된다(agent가 fixture를 지어내는 경로 차단).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from redact import redact_mapping

from kpubdata.config import KPubDataConfig
from kpubdata.core.executor import (
    SpecExecutor,
    check_payload_error,
    extract_items,
    extract_total_count,
)
from kpubdata.core.models import Query
from kpubdata.core.spec import find_spec
from kpubdata.transport.http import HttpTransport

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_ROOT = REPO_ROOT / "tests" / "fixtures"
_DEFAULT_PAGE_SIZE = 10


def _canon(obj: object) -> str:
    """해시 비교용 정규 JSON 직렬화(ensure_ascii=False·개행 고정)."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=1) + "\n"


def record_dataset(
    dataset_id: str,
    *,
    fixtures_root: Path = FIXTURES_ROOT,
    config: KPubDataConfig | None = None,
    transport: HttpTransport | None = None,
    recorded_by: str | None = None,
) -> list[Path]:
    """데이터셋의 모든 example을 실호출해 fixture 3종을 저장한다.

    예외:
        SystemExit: spec이 없거나 키가 없는 경우(사람이 읽는 안내와 함께).
    """
    spec = find_spec(dataset_id)
    if spec is None:
        print(f"오류: spec을 찾을 수 없습니다: {dataset_id}")
        return []

    resolved_config = config or KPubDataConfig.from_env()
    resolved_transport = transport or HttpTransport()
    executor = SpecExecutor(resolved_transport, resolved_config)

    provider_key = spec.auth.provider_key or spec.provider
    api_key = resolved_config.get_provider_key(provider_key)
    if api_key is None:
        print(
            f"오류: {provider_key} API 키가 없습니다. "
            f"KPUBDATA_{provider_key.upper()}_API_KEY 를 설정하세요."
        )
        return []

    out_dir = fixtures_root / spec.provider / spec.dataset_key
    out_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for example in spec.examples:
        query = Query(
            filters=dict(example.params),
            page=example.page or 1,
            page_size=example.page_size or _DEFAULT_PAGE_SIZE,
        )
        params, payload = executor.fetch(spec, query, format_hint=example.format)
        check_payload_error(spec, payload)

        safe_params = redact_mapping(params, secrets=(api_key,))
        safe_payload = redact_mapping(payload, secrets=(api_key,))
        # expected는 정화된 raw와 동일 출처에서 추출한다 — verify가 정화본을
        # 재생하므로 쌍이 일치해야 한다(전화번호 등 항목 치환 반영).
        items = extract_items(spec, safe_payload)
        total = extract_total_count(spec, safe_payload)
        payload_text = _canon(safe_payload)

        raw_path = out_dir / f"{example.name}.raw.json"
        meta_path = out_dir / f"{example.name}.meta.json"
        expected_path = out_dir / f"{example.name}.expected.json"

        meta = {
            "dataset_id": spec.id,
            "example": example.name,
            "recorded_at": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
            "endpoint": f"{spec.endpoint.base_url.rstrip('/')}/{spec.endpoint.operation}",
            "params": safe_params,
            "format": example.format or spec.response.format,
            "response_sha256": hashlib.sha256(payload_text.encode("utf-8")).hexdigest(),
            "recorded_by": recorded_by
            or os.environ.get("KPUBDATA_RECORDER")
            or ("ci" if os.environ.get("CI") else "human"),
        }

        raw_path.write_text(payload_text, encoding="utf-8")
        meta_path.write_text(_canon(meta), encoding="utf-8")
        expected_path.write_text(_canon({"items": items, "total_count": total}), encoding="utf-8")
        written.extend([raw_path, meta_path, expected_path])
        shown = raw_path.relative_to(REPO_ROOT) if raw_path.is_relative_to(REPO_ROOT) else raw_path
        print(f"기록: {shown} ({len(items)}건, total={total})")

    # spec에서 제거된 예제의 낡은 fixture 정리(도구 위생 — 수동 수정 아님)
    declared = {example.name for example in spec.examples}
    for stale in out_dir.glob("*.raw.json"):
        stale_name = stale.name.removesuffix(".raw.json")
        if stale_name not in declared:
            for suffix in (".raw.json", ".meta.json", ".expected.json"):
                (out_dir / f"{stale_name}{suffix}").unlink(missing_ok=True)
            print(f"정리: 낡은 예제 fixture {stale_name}")

    return written


def _spec_ids() -> list[str]:
    """번들 spec id 목록을 반환한다."""
    from kpubdata.core.spec import discover_specs

    return [spec.id for spec in discover_specs()]


def main(argv: list[str] | None = None) -> int:
    """CLI 진입점."""
    parser = argparse.ArgumentParser(description="spec examples 실호출 fixture 기록")
    parser.add_argument("dataset", nargs="?", help="데이터셋 id (예: datago.apt_trade)")
    parser.add_argument("--list", action="store_true", help="기록 가능한 spec id 나열")
    args = parser.parse_args(argv)

    if args.list or not args.dataset:
        for spec_id in _spec_ids():
            print(spec_id)
        return 0

    written = record_dataset(args.dataset)
    return 0 if written else 1


if __name__ == "__main__":
    sys.exit(main())
