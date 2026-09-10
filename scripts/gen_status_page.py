"""데이터셋 상태 페이지 생성 — 검증 현황을 JSON+마크다운으로 남긴다.

사용법:
    uv run python scripts/gen_status_page.py [--check]

산출물:
- ``docs/status/latest.json`` — 기계 판독용 스냅샷(생성 시각·spec 검증일·Provider별 수)
- ``docs/status.md`` — mkdocs 페이지(사람용 요약)

월간 집계(#384 6.5)와 smoke 리포트의 기준 데이터가 된다.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from kpubdata.core.spec import discover_specs

REPO_ROOT = Path(__file__).resolve().parents[1]
STATUS_DIR = REPO_ROOT / "docs" / "status"
STATUS_JSON = STATUS_DIR / "latest.json"
STATUS_MD = REPO_ROOT / "docs" / "status.md"
SUPPORTED = REPO_ROOT / "SUPPORTED_DATA.md"


def _catalogue_counts() -> dict[str, int]:
    """catalogue Provider별 데이터셋 수."""
    counts: dict[str, int] = {}
    for catalogue in sorted((REPO_ROOT / "src/kpubdata/providers").glob("*/catalogue.json")):
        counts[catalogue.parent.name] = len(json.loads(catalogue.read_text(encoding="utf-8")))
    return counts


def _supported_summary() -> dict[str, int]:
    """SUPPORTED_DATA 상태 열 요약(지원/폐기/기타)."""
    counts: dict[str, int] = {}
    content = SUPPORTED.read_text(encoding="utf-8") if SUPPORTED.is_file() else ""
    known = {"지원", "폐기", "예정"}
    for line in content.splitlines():
        m = re.match(r"\| ([^|]+) \| ([^|]+) \|", line)
        if m and m.group(1).strip() in known:
            status = m.group(1).strip()
            counts[status] = counts.get(status, 0) + 1
    return counts


def build_status() -> dict[str, object]:
    """현재 상태 스냅샷을 만든다."""
    specs = discover_specs()
    today = date.today().isoformat()
    verified = [s for s in specs if s.last_verified]
    fresh = [
        s for s in verified if s.last_verified and s.last_verified.isoformat() >= _recent_cutoff()
    ]
    return {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        "spec_datasets": {
            "total": len(specs),
            "verified": len(verified),
            "verified_recent_90d": len(fresh),
            "per_dataset": {
                s.id: {
                    "last_verified": s.last_verified.isoformat() if s.last_verified else None,
                    "status": s.status,
                }
                for s in sorted(specs, key=lambda x: x.id)
            },
        },
        "catalogue_datasets": _catalogue_counts(),
        "supported_rows": _supported_summary(),
    }


def _recent_cutoff() -> str:
    """90일 전 ISO 날짜."""
    from datetime import timedelta

    return (date.today() - timedelta(days=90)).isoformat()


def render_md(status: dict[str, object]) -> str:
    """상태 JSON을 사람용 마크다운으로 바꾼다."""
    spec = status["spec_datasets"]  # type: ignore[index]
    catalogue = status["catalogue_datasets"]  # type: ignore[index]
    supported = status["supported_rows"]  # type: ignore[index]
    lines = [
        "# 데이터셋 검증 상태",
        "",
        f"> 생성: `{status['generated_at']}` — `scripts/gen_status_page.py` (직접 편집 금지)",
        "",
        "## 요약",
        "",
        f"- spec 데이터셋: **{spec['total']}종** (검증 {spec['verified']}종, 최근 90일 {spec['verified_recent_90d']}종)",  # type: ignore[index]
        f"- catalogue 데이터셋: {sum(catalogue.values())}종"  # type: ignore[call-arg]
        + " ("
        + ", ".join(f"{p} {n}" for p, n in sorted(catalogue.items()))
        + ")",  # type: ignore[union-attr]
        f"- SUPPORTED_DATA 행 분포: {supported}",  # type: ignore[str-format]
        "",
        "## spec 데이터셋별 최종 검증일",
        "",
        "| 데이터셋 | 최종 검증 | 상태 |",
        "|---|---|---|",
    ]
    per = spec["per_dataset"]  # type: ignore[index]
    for dataset_id, info in per.items():  # type: ignore[union-attr]
        info_dict = info  # type: ignore[assignment]
        lines.append(
            f"| `{dataset_id}` | {info_dict['last_verified'] or '-'} | {info_dict['status']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI 진입점 — 생성 또는 드리프트 검사."""
    parser = argparse.ArgumentParser(description="데이터셋 상태 페이지 생성")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    status = build_status()
    STATUS_DIR.mkdir(parents=True, exist_ok=True)
    json_text = json.dumps(status, ensure_ascii=False, indent=2) + "\n"
    md_text = render_md(status)
    if args.check:
        json_ok = STATUS_JSON.is_file() and STATUS_JSON.read_text(encoding="utf-8") == json_text
        md_ok = STATUS_MD.is_file() and STATUS_MD.read_text(encoding="utf-8") == md_text
        if not (json_ok and md_ok):
            print(
                "드리프트: 상태 페이지가 최신이 아님 — 재생성 후 커밋하세요 (generated_at 제외하고 비교 권장)."
            )
            return 1
        print("일치: 상태 페이지 최신")
        return 0
    STATUS_JSON.write_text(json_text, encoding="utf-8")
    STATUS_MD.write_text(md_text, encoding="utf-8")
    print(f"생성: {STATUS_JSON.relative_to(REPO_ROOT)}, {STATUS_MD.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
