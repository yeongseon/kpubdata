"""드리프트 리포트 — 스모크 결과에서 "2회 연속 실패" 데이터셋을 추출한다.

사용법 (GitHub Actions smoke.yml의 report 잡 또는 로컬):
    gh run list --workflow=smoke.yml --limit 3   # 전제: 스모크 실행 기록
    GH_TOKEN=... uv run python scripts/report_drift.py [--dry-run]

동작:
1. 최근 스모크 실행들의 로그에서 실패한 통합테스트(데이터셋) 목록을 추출
2. 직전 2회 연속 실패한 데이터셋만 선별 (일시 장애와 지속 드리프트 구분)
3. 각 데이터셋에 대해 기존 열린 drift 이슈가 있으면 코멘트 갱신, 없으면 신규 발행
4. ``--dry-run`` 은 이슈 발행 없이 판정만 출력

의존: gh CLI + 쓰기 권한 토큰(GH_TOKEN/GITHUB_TOKEN).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field

REPO = "yeongseon/kpubdata"
WORKFLOW = "smoke.yml"
# 통합테스트 함수명 패턴: test_datago_village_fcst → datago.village_fcst
_TEST_RE = re.compile(r"FAILED\s+\S*test_(?P<provider>[a-z]+)_(?P<key>[a-z0-9_]+)\b")


@dataclass
class DriftReport:
    """드리프트 판정 결과."""

    consecutive_failures: list[str] = field(default_factory=list)
    recent_runs: list[dict[str, object]] = field(default_factory=list)


def _gh(args: list[str]) -> str:
    """gh CLI를 실행하고 표준출력을 반환한다."""
    proc = subprocess.run(
        ["gh", *args, "--repo", REPO],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print(f"gh 오류: {proc.stderr.strip()[:200]}")
        return ""
    return proc.stdout


def _failed_datasets_from_run(run_id: str) -> set[str]:
    """실행 로그에서 실패한 데이터셋 id 집합을 추출한다."""
    log = _gh(["run", "view", run_id, "--log"])
    found: set[str] = set()
    for match in _TEST_RE.finditer(log):
        provider = match.group("provider")
        key = match.group("key")
        # test_datago_village_fcst → provider=datago, key=village_fcst
        found.add(f"{provider}.{key}")
    return found


def collect(consecutive_required: int = 2, limit: int = 6) -> DriftReport:
    """최근 스모크 실행을 분석해 N회 연속 실패 데이터셋을 판정한다."""
    listing = _gh(
        [
            "run",
            "list",
            "--workflow",
            WORKFLOW,
            "--limit",
            str(limit),
            "--json",
            "databaseId,status,conclusion,createdAt",
        ]
    )
    if not listing:
        return DriftReport()
    runs = [run for run in json.loads(listing) if run.get("conclusion")]
    failures_per_run: list[tuple[str, set[str]]] = []
    for run in runs:
        run_id = str(run["databaseId"])
        conclusion = str(run.get("conclusion"))
        if conclusion == "success":
            failures_per_run.append((run_id, set()))
        else:
            failures_per_run.append((run_id, _failed_datasets_from_run(run_id)))

    report = DriftReport(
        recent_runs=[{"id": rid, "failures": sorted(f)} for rid, f in failures_per_run]
    )
    if len(failures_per_run) < consecutive_required:
        return report

    _latest_id, latest = failures_per_run[0]
    for dataset in sorted(latest):
        streak = 0
        for _rid, failures in failures_per_run[:consecutive_required]:
            if dataset in failures:
                streak += 1
        if streak >= consecutive_required:
            report.consecutive_failures.append(dataset)
    return report


def _existing_drift_issue(dataset: str) -> int | None:
    """데이터셋에 대한 열린 drift 이슈 번호를 찾는다(데이터셋당 1개 원칙)."""
    out = _gh(
        ["issue", "list", "--search", f'"{dataset}" is:open label:drift', "--json", "number,title"]
    )
    if not out:
        return None
    issues = json.loads(out)
    for issue in issues:
        if dataset in str(issue.get("title", "")):
            return int(issue["number"])
    return None


def file_or_update(dataset: str, report: DriftReport, dry_run: bool) -> None:
    """2회 연속 실패 데이터셋을 이슈로 발행하거나 기존 이슈를 갱신한다."""
    title = f"[drift] {dataset} 실API 스모크 연속 실패"
    body_lines = [
        f"## 대상\n{dataset}",
        "",
        "## 증상",
        f"최근 {len(report.recent_runs)}회 스모크 중 직전 실행부터 연속 실패.",
    ]
    for run in report.recent_runs:
        failures = run.get("failures", [])
        mark = "실패" if failures else "성공"
        body_lines.append(f"- 실행 {run['id']}: {mark} {sorted(failures) if failures else ''}")
    dataset_key = dataset.split(".", 1)[1]
    reproduce = (
        "KPUBDATA_DATAGO_API_KEY=... uv run pytest -m integration "
        f"-k '{dataset_key}' tests/integration/test_datago_live.py"
    )
    body_lines += [
        "",
        "## 재현",
        f"`{reproduce}`",
        "",
        "## 수리 절차",
        "drift-fixer 에이전트 절차를 따른다 (fixture는 반드시 make record로 재기록).",
    ]
    body = "\n".join(body_lines)

    if dry_run:
        print(f"[dry-run] {title}")
        return

    existing = _existing_drift_issue(dataset)
    if existing is not None:
        _gh(
            [
                "issue",
                "comment",
                str(existing),
                "--body",
                "스모크 연속 실패 지속 (자동 갱신):\n" + body,
            ]
        )
        print(f"갱신: #{existing} {dataset}")
        return
    out = _gh(["issue", "create", "--title", title, "--body", body, "--label", "drift"])
    print(f"발행: {out.strip()} {dataset}")


def main(argv: list[str] | None = None) -> int:
    """CLI 진입점."""
    parser = argparse.ArgumentParser(description="스모크 드리프트 리포트")
    parser.add_argument("--dry-run", action="store_true", help="이슈 발행 없이 판정만")
    args = parser.parse_args(argv)

    report = collect()
    if not report.recent_runs:
        print("스모크 실행 기록이 부족하여 판정 불가 (최소 2회 필요)")
        return 0
    streak_text = report.consecutive_failures or "없음"
    print(f"최근 실행 {len(report.recent_runs)}회 분석 — 연속 실패: {streak_text}")
    for dataset in report.consecutive_failures:
        file_or_update(dataset, report, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
