"""릴리스 노트용 데이터셋 변경 집계 — 두 시점 사이의 추가/제거/검증 갱신을 뽑는다.

사용법:
    uv run python scripts/changelog_datasets.py --from v0.5.0 --to HEAD

출처:
- spec 디렉터리(git ls-tree)와 SUPPORTED_DATA.md 를 두 시점에서 비교해
  데이터셋 증감과 검증일 변화를 요약한다. 수기 입력 없이 git 기반으로만.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass


@dataclass
class Snapshot:
    """한 시점의 데이터셋 상태."""

    specs: set[str]
    catalogue: set[str]
    verified: dict[str, str]  # dataset_id -> 최종 검증일


def _git(args: list[str]) -> str:
    proc = subprocess.run(["git", *args], check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"git 오류: {proc.stderr[:200]}")
        return ""
    return proc.stdout


def _specs_at(rev: str) -> set[str]:
    """해당 리비전의 spec 파일 목록에서 데이터셋 id를 만든다."""
    out = _git(["ls-tree", "-r", "--name-only", rev, "src/kpubdata/specs"])
    found: set[str] = set()
    for line in out.splitlines():
        m = re.match(r"src/kpubdata/specs/([a-z0-9_]+)/([a-z0-9_]+)\.yaml$", line)
        if m:
            found.add(f"{m.group(1)}.{m.group(2)}")
    return found


def _catalogue_at(rev: str) -> set[str]:
    """해당 리비전의 catalogue 데이터셋 키 전체."""
    out = _git(["ls-tree", "-r", "--name-only", rev, "src/kpubdata/providers"])
    found: set[str] = set()
    for line in out.splitlines():
        m = re.match(r"src/kpubdata/providers/([a-z0-9_]+)/catalogue\.json$", line)
        if not m:
            continue
        content = _git(["show", f"{rev}:{line}"])
        try:
            import json

            entries = json.loads(content)
            found.update(f"{m.group(1)}.{e['dataset_key']}" for e in entries)
        except (json.JSONDecodeError, KeyError):
            continue
    return found


def _verified_at(rev: str) -> dict[str, str]:
    """SUPPORTED_DATA.md의 '실API 검증 | 날짜' 행을 파싱한다."""
    content = _git(["show", f"{rev}:SUPPORTED_DATA.md"])
    verified: dict[str, str] = {}
    for line in content.splitlines():
        m = re.match(r"\|[^|]+\| 실API 검증 \| ([0-9-]+) \|[^(]+\| `([a-z0-9_.]+)` \|", line)
        if m:
            verified[m.group(2)] = m.group(1)
    return verified


def snapshot(rev: str) -> Snapshot:
    """리비전 스냅샷을 만든다."""
    return Snapshot(specs=_specs_at(rev), catalogue=_catalogue_at(rev), verified=_verified_at(rev))


def report(old: Snapshot, new: Snapshot) -> str:
    """두 스냅샷의 차이를 릴리스 노트 마크다운으로 만든다."""
    lines: list[str] = ["## 데이터셋 변경", ""]
    added = sorted((new.specs | new.catalogue) - (old.specs | old.catalogue))
    removed = sorted((old.specs | old.catalogue) - (new.specs | new.catalogue))
    newly_verified = sorted(k for k, v in new.verified.items() if old.verified.get(k) != v)

    if added:
        lines.append(f"### 추가 ({len(added)}종)")
        lines.extend(f"- `{d}`" for d in added)
        lines.append("")
    if removed:
        lines.append(f"### 제거 ({len(removed)}종)")
        lines.extend(f"- `{d}`" for d in removed)
        lines.append("")
    if newly_verified:
        lines.append(f"### 실API 재검증 ({len(newly_verified)}종)")
        lines.extend(f"- `{d}` → {new.verified[d]}" for d in newly_verified)
        lines.append("")
    if not (added or removed or newly_verified):
        lines.append("변경 없음")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI 진입점."""
    parser = argparse.ArgumentParser(description="릴리스 노트용 데이터셋 변경 집계")
    parser.add_argument("--from", dest="from_rev", required=True)
    parser.add_argument("--to", dest="to_rev", default="HEAD")
    args = parser.parse_args(argv)
    print(report(snapshot(args.from_rev), snapshot(args.to_rev)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
