"""배치 녹화기 — Provider의 모든 spec을 fast-fail 설정으로 기록하고 결과를 수집한다.

사용법:
    uv run python scripts/batch_record.py --provider localdata [--limit N]

- 전송 설정: timeout 15s·재시도 0 (실패 데이터셋이 배치를 늦추지 않게)
- 결과: 성공/실패 목록을 JSON으로 ``tests/fixtures/batch-record-{provider}.json`` 에 남긴다
- 실패(필수 파라미터·폐기·권한)는 정상 결과다 — 스킵 후 백로그로 분류한다
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from record import record_dataset

from kpubdata.config import KPubDataConfig
from kpubdata.core.spec import discover_specs
from kpubdata.transport.http import HttpTransport, TransportConfig

REPO_ROOT = Path(__file__).resolve().parents[1]


def batch_record(provider: str, *, limit: int | None = None) -> dict[str, list[str]]:
    """Provider spec 전체를 녹화하고 성공/실패 요약을 반환한다."""
    config = KPubDataConfig.from_env()
    fast_transport = HttpTransport(config=TransportConfig(timeout=15, max_retries=0, cache=None))
    specs = [spec for spec in discover_specs() if spec.provider == provider]
    if limit is not None:
        specs = specs[:limit]

    ok: list[str] = []
    failed: list[list[str]] = []
    for spec in specs:
        try:
            written = record_dataset(
                spec.id, config=config, transport=fast_transport, recorded_by="batch-agent"
            )
            if written:
                ok.append(spec.id)
            else:
                failed.append([spec.id, "키 없음"])
        except Exception as exc:  # noqa: BLE001 — 배치는 모든 실패를 수집한다
            failed.append([spec.id, f"{type(exc).__name__}: {str(exc)[:120]}"])
            print(f"실패 {spec.id}: {type(exc).__name__}: {str(exc)[:100]}")

    summary = {"ok": ok, "failed": failed}
    out = REPO_ROOT / "tests" / "fixtures" / f"batch-record-{provider}.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[{provider}] 성공 {len(ok)} / 실패 {len(failed)} → {out.relative_to(REPO_ROOT)}")
    return summary


def main(argv: list[str] | None = None) -> int:
    """CLI 진입점."""
    parser = argparse.ArgumentParser(description="Provider 단위 배치 녹화")
    parser.add_argument("--provider", required=True)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args(argv)
    summary = batch_record(args.provider, limit=args.limit)
    return 0 if summary["ok"] or not summary["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
