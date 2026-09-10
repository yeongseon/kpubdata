"""데이터셋 검증 오케스트레이터 — `make verify`의 실체.

단계(하나라도 실패하면 exit 1):
1. spec 스키마·id·중복 검사 (scripts/validate_spec.py 위임)
2. fixture 무결성 — raw/meta/expected 3종 존재 + 해시 일치
3. replay 계약 — raw → envelope 검사 → items/total 추출이 expected와 일치

사용법:
    uv run python scripts/verify_spec.py                     # 전체 spec
    uv run python scripts/verify_spec.py --dataset datago.apt_trade
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from kpubdata.core.spec import SpecDefinition, discover_specs, find_spec

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_ROOT = REPO_ROOT / "tests" / "fixtures"


@dataclass
class StepResult:
    """단일 검증 단계 결과."""

    name: str
    passed: bool
    detail: str = ""


@dataclass
class DatasetVerifyResult:
    """데이터셋별 검증 결과."""

    dataset_id: str
    steps: list[StepResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """모든 단계 통과 여부."""
        return all(step.passed for step in self.steps)


def _canon_bytes(data: object) -> str:
    """해시 비교용 정규 JSON 직렬화(record.py의 규칙과 동일)."""
    return json.dumps(data, ensure_ascii=False, sort_keys=True, indent=1) + "\n"


def _verify_fixtures(spec: SpecDefinition) -> list[StepResult]:
    """fixture 무결성 + replay 계약을 검증한다."""
    results: list[StepResult] = []
    out_dir = FIXTURES_ROOT / spec.provider / spec.dataset_key
    if not out_dir.is_dir() or not list(out_dir.glob("*.raw.json")):
        shown = out_dir.relative_to(REPO_ROOT) if out_dir.is_relative_to(REPO_ROOT) else out_dir
        results.append(
            StepResult(
                "fixture 존재",
                passed=False,
                detail=(f"fixture 없음: {shown} — `make record DATASET={spec.id}` 로 생성"),
            )
        )
        return results

    for raw_path in sorted(out_dir.glob("*.raw.json")):
        example = raw_path.name.removesuffix(".raw.json")
        meta_path = raw_path.with_name(f"{example}.meta.json")
        expected_path = raw_path.with_name(f"{example}.expected.json")

        # 2-a. 3종 존재
        missing = [path.name for path in (raw_path, meta_path, expected_path) if not path.is_file()]
        if missing:
            results.append(
                StepResult(
                    f"fixture[{example}] 3종 존재",
                    passed=False,
                    detail=f"누락: {', '.join(missing)} (메타 없는 fixture는 검증 불가)",
                )
            )
            continue

        # 2-b. 해시 일치 (agent가 fixture를 지어내는 경로 차단)
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        digest = hashlib.sha256(_canon_bytes(payload).encode("utf-8")).hexdigest()
        if digest != meta.get("response_sha256"):
            results.append(
                StepResult(
                    f"fixture[{example}] 해시 일치",
                    passed=False,
                    detail="meta의 response_sha256과 raw 내용이 불일치 — fixture가 기록 후 수정됨",
                )
            )
            continue

        # 3. replay 계약 — spec 필드를 바꾸면 이 단계에서 실패해야 한다
        from kpubdata.core.executor import check_payload_error, extract_items, extract_total_count

        try:
            check_payload_error(spec, payload)
            items = extract_items(spec, payload)
            total = extract_total_count(spec, payload)
        except Exception as exc:  # noqa: BLE001 — 검증기는 모든 실패를 결과로 수집
            results.append(
                StepResult(f"replay[{example}] envelope 검사", passed=False, detail=str(exc))
            )
            continue

        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        if items != expected.get("items") or total != expected.get("total_count"):
            results.append(
                StepResult(
                    f"replay[{example}] 정규화 일치",
                    passed=False,
                    detail=(
                        f"expected 불일치: items {len(items)}건/total={total} vs 스냅샷 "
                        f"{len(expected.get('items', []))}건/total={expected.get('total_count')}"
                    ),
                )
            )
            continue

        results.append(StepResult(f"fixture[{example}] + replay", passed=True))

    return results


def run_verify(dataset_id: str | None = None) -> int:
    """전체(또는 단일) spec에 대해 검증을 수행하고 종료 코드를 반환한다."""
    specs: list[SpecDefinition]
    if dataset_id:
        spec = find_spec(dataset_id)
        if spec is None:
            print(f"오류: spec을 찾을 수 없습니다: {dataset_id}")
            return 1
        specs = [spec]
    else:
        specs = discover_specs()

    # 1. 스키마 검증 위임
    validate = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "validate_spec.py")],
        check=False,
        capture_output=True,
        text=True,
    )
    print(validate.stdout.rstrip())
    if validate.returncode != 0:
        if validate.stderr:
            print(validate.stderr.rstrip())
        return 1

    failed_any = False
    for spec in specs:
        result = DatasetVerifyResult(dataset_id=spec.id)
        result.steps.extend(_verify_fixtures(spec))
        result.steps.append(_run_example_script(spec))
        result.steps.append(_run_live_schema_diff(spec))

        status = "통과" if result.passed else "실패"
        print(f"[{status}] {spec.id}")
        for step in result.steps:
            if not step.passed:
                print(f"  오류({step.name}): {step.detail}")
        failed_any = failed_any or not result.passed

    total = len(specs)
    print(f"검증 결과: {total}개 데이터셋, {'실패 있음' if failed_any else '전체 통과'}")
    return 1 if failed_any else 0


def _run_live_schema_diff(spec: SpecDefinition) -> StepResult:
    """LIVE=1 시 실호출 스키마 diff를 수행한다(값 변화는 무시, 구조만 비교)."""
    import os

    if os.environ.get("LIVE") != "1":
        return StepResult("live 스키마 diff", passed=True, detail="건너뜀(LIVE=1 아님)")

    from kpubdata.config import KPubDataConfig
    from kpubdata.core.executor import SpecExecutor, check_payload_error, extract_items
    from kpubdata.core.models import Query
    from kpubdata.core.spec import ExampleSpec
    from kpubdata.transport.http import HttpTransport

    out_dir = FIXTURES_ROOT / spec.provider / spec.dataset_key
    meta_paths = sorted(out_dir.glob("*.meta.json"))
    if not meta_paths:
        return StepResult("live 스키마 diff", passed=True, detail="fixture 없음 — 건너뜀")

    meta = json.loads(meta_paths[0].read_text(encoding="utf-8"))
    example_name = str(meta.get("example", "default"))
    example = next(
        (ex for ex in spec.examples if ex.name == example_name),
        spec.examples[0] if spec.examples else ExampleSpec(name=example_name),
    )
    query = Query(
        filters=dict(example.params),
        page=example.page or 1,
        page_size=example.page_size or 10,
    )
    executor = SpecExecutor(HttpTransport(), KPubDataConfig.from_env())
    try:
        params, payload = executor.fetch(spec, query, format_hint=example.format)
        check_payload_error(spec, payload)
        live_items = extract_items(spec, payload)
    except Exception as exc:  # noqa: BLE001 — LIVE 검증은 실패를 결과로 수집
        return StepResult("live 스키마 diff", passed=False, detail=f"실호출 실패: {str(exc)[:120]}")

    expected = json.loads((out_dir / f"{example_name}.expected.json").read_text(encoding="utf-8"))
    fixture_keys = (
        {k for item in expected.get("items", []) for k in item} if expected.get("items") else set()
    )
    live_keys = {k for item in live_items for k in item} if live_items else set()
    added = sorted(live_keys - fixture_keys)
    removed = sorted(fixture_keys - live_keys)
    if added or removed:
        detail = f"스키마 diff — 추가: {added or '없음'} / 제거: {removed or '없음'}"
        return StepResult("live 스키마 diff", passed=False, detail=detail)
    return StepResult("live 스키마 diff", passed=True, detail=f"구조 일치({len(live_keys)}필드)")


def _run_example_script(spec: SpecDefinition) -> StepResult:
    """예제 스크립트를 replay 모드로 실행한다(검증 4단계)."""
    import os
    import subprocess

    script = REPO_ROOT / "examples" / spec.provider / f"{spec.dataset_key}.py"
    if not script.is_file():
        return StepResult(
            "examples 실행",
            passed=False,
            detail=(f"예제 스크립트 없음: {script} — examples/README.md 규약(#379 2.3)"),
        )
    env = {**os.environ, "KPUBDATA_MODE": "replay"}
    proc = subprocess.run(
        [sys.executable, str(script)],
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
        env=env,
    )
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout).strip().splitlines()[-3:]
        return StepResult(
            "examples 실행",
            passed=False,
            detail="replay 실행 실패: " + " / ".join(tail),
        )
    return StepResult("examples 실행", passed=True)


def main(argv: list[str] | None = None) -> int:
    """CLI 진입점."""
    parser = argparse.ArgumentParser(description="spec 데이터셋 검증 (make verify)")
    parser.add_argument("--dataset", help="단일 데이터셋 id (예: datago.apt_trade)")
    args = parser.parse_args(argv)
    return run_verify(args.dataset)


if __name__ == "__main__":
    sys.exit(main())
