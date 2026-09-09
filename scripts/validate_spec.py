"""데이터셋 spec 검증 CLI — 스키마 계약·id 규칙·중복 검사를 수행한다.

사용법:
    uv run python scripts/validate_spec.py              # 전체 spec 검증
    uv run python scripts/validate_spec.py --spec datago.apt_trade
    uv run python scripts/validate_spec.py --specs-dir PATH --schema PATH

검사 항목:
1. YAML 파싱
2. ``specs/schema.json`` (JSON Schema draft 2020-12) 위반 여부
3. id == "{provider}.{파일명 stem}" 및 파일 경로({provider}/) 일치
4. 전체 spec 간 id 중복
5. examples[].name 중복(데이터셋 내부)
6. 동일 키의 catalogue.json 항목 존재 시 공존 NOTICE 출력(실패 아님 — 파일럿 병존 설계)

CI(ci.yml)에서 의존성 설치 후 실행되며, 하나라도 실패하면 exit 1을 반환한다.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

import jsonschema
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPECS_DIR = REPO_ROOT / "src" / "kpubdata" / "specs"
DEFAULT_SCHEMA_PATH = DEFAULT_SPECS_DIR / "schema.json"
PROVIDERS_DIR = REPO_ROOT / "src" / "kpubdata" / "providers"


@dataclass
class SpecCheckResult:
    """단일 spec 검사 결과."""

    spec_id: str
    path: Path
    errors: list[str] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """오류가 없으면 True를 반환한다."""
        return not self.errors


@dataclass
class ValidationReport:
    """전체 검증 보고서."""

    results: list[SpecCheckResult] = field(default_factory=list)

    @property
    def passed_count(self) -> int:
        """통과한 spec 수를 반환한다."""
        return sum(1 for result in self.results if result.passed)

    @property
    def failed_count(self) -> int:
        """실패한 spec 수를 반환한다."""
        return sum(1 for result in self.results if not result.passed)

    @property
    def ok(self) -> bool:
        """전체 통과 여부를 반환한다."""
        return bool(self.results) and self.failed_count == 0


def _load_schema(schema_path: Path) -> dict[str, object]:
    """스키마 파일을 읽어 dict로 반환한다."""
    import json

    data = json.loads(schema_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        msg = f"스키마 파일이 객체가 아닙니다: {schema_path}"
        raise ValueError(msg)
    return data


def _catalogue_dataset_keys(provider: str) -> set[str]:
    """해당 Provider의 catalogue.json 데이터셋 키 집합을 반환한다(없으면 빈 집합)."""
    catalogue_path = PROVIDERS_DIR / provider / "catalogue.json"
    if not catalogue_path.is_file():
        return set()
    import json

    entries = json.loads(catalogue_path.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        return set()
    keys: set[str] = set()
    for entry in entries:
        if isinstance(entry, dict) and isinstance(entry.get("dataset_key"), str):
            keys.add(entry["dataset_key"])
    return keys


def validate_spec_file(
    path: Path,
    schema: dict[str, object],
    seen_ids: dict[str, Path],
) -> SpecCheckResult:
    """spec 파일 하나를 스키마·id 규칙에 따라 검사한다."""
    spec_id = path.stem
    result = SpecCheckResult(spec_id=spec_id, path=path)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        result.errors.append(f"YAML 파싱 실패: {exc}")
        return result

    if not isinstance(data, dict):
        result.errors.append("spec 루트는 매핑이어야 합니다.")
        return result

    declared_id = data.get("id")
    declared_id = declared_id if isinstance(declared_id, str) else ""
    provider = data.get("provider")
    provider = provider if isinstance(provider, str) else ""

    # jsonschema 검사 — 오류 메시지를 사람이 읽을 수 있는 형태로 축약한다.
    validator_cls = jsonschema.Draft202012Validator
    validator = validator_cls(schema)
    for error in sorted(validator.iter_errors(data), key=lambda item: list(item.absolute_path)):
        location = ".".join(str(part) for part in error.absolute_path) or "(루트)"
        result.errors.append(f"스키마 위반 [{location}]: {error.message}")

    # id ↔ 파일명/디렉터리 규칙
    if declared_id and declared_id != f"{provider}.{path.stem}":
        result.errors.append(
            f"id({declared_id!r})는 '{{provider}}.{{파일명}}' 규칙과 불일치합니다 "
            f"(기대: {provider}.{path.stem!r})"
        )
    expected_dir = path.parent.name
    if provider and expected_dir != provider:
        result.errors.append(
            f"파일이 {expected_dir!r} 디렉터리에 있지만 provider는 {provider!r}입니다."
        )

    # 전역 중복 id
    if declared_id:
        existing = seen_ids.get(declared_id)
        if existing is not None and existing != path:
            result.errors.append(
                f"id 중복: {declared_id!r}이(가) {existing}에도 정의되어 있습니다."
            )
        else:
            seen_ids[declared_id] = path

    # examples[].name 중복
    examples = data.get("examples")
    if isinstance(examples, list):
        names: list[str] = [
            ex.get("name")
            for ex in examples
            if isinstance(ex, dict) and isinstance(ex.get("name"), str)
        ]
        duplicated = sorted({name for name in names if names.count(name) > 1})
        if duplicated:
            result.errors.append(f"examples[].name 중복: {', '.join(duplicated)}")

    # catalogue 공존 NOTICE (실패 아님)
    dataset_key = path.stem
    if dataset_key in _catalogue_dataset_keys(provider):
        result.notices.append(
            f"공존: {provider} catalogue.json에도 {dataset_key!r}이(가) 있습니다 "
            "(파일럿 병존 설계 — 전환 완료 시 catalogue 항목 제거)"
        )

    return result


def validate_specs(specs_dir: Path, schema_path: Path) -> ValidationReport:
    """specs 디렉터리 전체를 검증해 보고서를 반환한다."""
    schema = _load_schema(schema_path)
    report = ValidationReport()
    seen_ids: dict[str, Path] = {}
    for path in sorted(specs_dir.rglob("*.yaml")) + sorted(specs_dir.rglob("*.yml")):
        if path.name == "schema.json":
            continue
        report.results.append(validate_spec_file(path, schema, seen_ids))
    return report


def format_report(report: ValidationReport) -> str:
    """보고서를 사람이 읽는 요약 문자열로 변환한다."""
    lines: list[str] = []
    for result in report.results:
        status = "통과" if result.passed else "실패"
        shown_path = (
            result.path.relative_to(REPO_ROOT)
            if result.path.is_relative_to(REPO_ROOT)
            else result.path
        )
        lines.append(f"[{status}] {shown_path}")
        for notice in result.notices:
            lines.append(f"  참고: {notice}")
        for error in result.errors:
            lines.append(f"  오류: {error}")
    lines.append(f"검증 결과: {report.passed_count}개 통과, {report.failed_count}개 실패")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI 진입점 — 검증을 실행하고 종료 코드를 반환한다."""
    parser = argparse.ArgumentParser(description="데이터셋 spec 검증")
    parser.add_argument("--spec", help="이 id의 spec만 검증 (예: datago.apt_trade)")
    parser.add_argument("--specs-dir", type=Path, default=DEFAULT_SPECS_DIR, help="specs 디렉터리")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA_PATH, help="스키마 경로")
    args = parser.parse_args(argv)

    if not args.specs_dir.is_dir():
        print(f"오류: specs 디렉터리가 없습니다: {args.specs_dir}")
        return 1

    report = validate_specs(args.specs_dir, args.schema)
    if args.spec:
        # 매칭은 "provider.파일명" 전체 id 또는 파일명(stem) 둘 다 허용한다.
        report.results = [
            result
            for result in report.results
            if args.spec in (result.spec_id, f"{result.path.parent.name}.{result.spec_id}")
        ]
        if not report.results:
            print(f"오류: spec을 찾을 수 없습니다: {args.spec}")
            return 1

    print(format_report(report))
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
