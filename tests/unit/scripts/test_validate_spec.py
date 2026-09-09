"""scripts/validate_spec.py 단위 테스트 — 순수 함수 기반 검증 규칙 확인."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "scripts" / "validate_spec.py"
SCHEMA_PATH = REPO_ROOT / "src" / "kpubdata" / "specs" / "schema.json"


def _load_script():
    """스크립트를 모듈로 로드한다(scripts는 패키지가 아니다)."""
    spec = importlib.util.spec_from_file_location("validate_spec", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["validate_spec"] = module
    spec.loader.exec_module(module)
    return module


VALID_SPEC = """\
id: test.sample
provider: test
title: 검증용 표본
endpoint:
  base_url: https://example.test/api
  operation: list
  method: GET
auth:
  type: none
response:
  format: json
  envelope: datago_standard
  items_path: response.body.items.item
  error:
    style: header_result_code
    code_path: response.header.resultCode
    ok_values: ["00"]
pagination:
  type: none
status: active
"""


def _write_spec(root: Path, provider: str, filename: str, content: str) -> Path:
    """임시 specs 트리에 spec 파일을 만든다."""
    provider_dir = root / provider
    provider_dir.mkdir(parents=True, exist_ok=True)
    path = provider_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture()
def module():
    return _load_script()


@pytest.fixture()
def specs_dir(tmp_path: Path) -> Path:
    """유효 spec 1개가 있는 임시 디렉터리."""
    _write_spec(tmp_path, "test", "sample.yaml", VALID_SPEC)
    return tmp_path


def test_valid_spec_passes(module, specs_dir: Path) -> None:
    """유효한 spec은 통과 보고된다."""
    report = module.validate_specs(specs_dir, SCHEMA_PATH)
    assert report.ok
    assert report.passed_count == 1
    assert not report.results[0].errors


def test_schema_violation_fails(module, specs_dir: Path) -> None:
    """enum 위반 등 스키마 위반이 오류로 보고된다."""
    content = (
        VALID_SPEC.replace("id: test.sample", "id: test.bad_enum")
        .replace("type: none", "type: bearer")
        .replace("envelope: datago_standard", "envelope: magic")
    )
    _write_spec(specs_dir, "test", "bad_enum.yaml", content)
    report = module.validate_specs(specs_dir, SCHEMA_PATH)
    assert report.failed_count == 1
    errors = report.results[0].errors
    assert any("스키마 위반" in err and "auth.type" in err for err in errors)
    assert any("스키마 위반" in err and "envelope" in err for err in errors)


def test_id_filename_mismatch_fails(module, specs_dir: Path) -> None:
    """id와 provider.파일명 규칙 불일치가 오류로 보고된다."""
    _write_spec(
        specs_dir,
        "test",
        "other_name.yaml",
        VALID_SPEC.replace("id: test.sample", "id: test.different"),
    )
    report = module.validate_specs(specs_dir, SCHEMA_PATH)
    assert report.failed_count == 1
    assert any("불일치" in err for err in report.results[0].errors)


def test_provider_directory_mismatch_fails(module, tmp_path: Path) -> None:
    """provider와 상위 디렉터리 불일치가 오류로 보고된다."""
    _write_spec(
        tmp_path,
        "alpha",
        "sample.yaml",
        VALID_SPEC.replace("id: test.sample", "id: beta.sample").replace(
            "provider: test", "provider: beta"
        ),
    )
    report = module.validate_specs(tmp_path, SCHEMA_PATH)
    assert report.failed_count == 1
    assert any("디렉터리" in err for err in report.results[0].errors)


def test_duplicate_ids_fail(module, specs_dir: Path) -> None:
    """동일 id가 두 파일에 있으면 둘 다 실패 처리된다."""
    _write_spec(specs_dir, "test", "sample2.yaml", VALID_SPEC)
    report = module.validate_specs(specs_dir, SCHEMA_PATH)
    assert report.failed_count >= 1
    assert any("id 중복" in err for result in report.results for err in result.errors)


def test_duplicate_example_names_fail(module, specs_dir: Path) -> None:
    """examples[].name 중복이 오류로 보고된다."""
    duplicated = (
        VALID_SPEC
        + """\
examples:
  - name: dup
    params: {}
  - name: dup
    params: {}
"""
    )
    path = specs_dir / "test" / "sample.yaml"
    path.write_text(duplicated, encoding="utf-8")
    report = module.validate_specs(specs_dir, SCHEMA_PATH)
    assert any("examples[].name 중복" in err for err in report.results[0].errors)


def test_catalogue_coexistence_is_notice_only(module, tmp_path: Path) -> None:
    """catalogue 공존은 NOTICE이지 실패가 아니다(파일럿 병존 설계)."""
    # 실제 골든 spec을 재활용: datago.apt_trade는 catalogue에도 존재한다.
    golden = REPO_ROOT / "src" / "kpubdata" / "specs" / "datago"
    report = module.validate_specs(golden, SCHEMA_PATH)
    assert report.ok
    apt_result = next(r for r in report.results if r.spec_id == "apt_trade")
    assert apt_result.passed
    assert any("공존" in notice for notice in apt_result.notices)


def test_zero_specs_reports_failure(module, tmp_path: Path) -> None:
    """spec이 없으면 보고서는 ok가 아니다."""
    empty = tmp_path / "empty"
    empty.mkdir()
    report = module.validate_specs(empty, SCHEMA_PATH)
    assert not report.ok


def test_cli_exit_codes(module, specs_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """CLI는 성공 0·실패 1을 반환하고 요약을 출력한다."""
    code = module.main(["--specs-dir", str(specs_dir), "--schema", str(SCHEMA_PATH)])
    captured = capsys.readouterr()
    assert code == 0
    assert "1개 통과" in captured.out

    _write_spec(
        specs_dir,
        "test",
        "broken.yaml",
        VALID_SPEC.replace("id: test.sample", "id: test.broken").replace(
            "pagination:\n  type: none", "pagination:\n  type: warp"
        ),
    )
    code = module.main(["--specs-dir", str(specs_dir), "--schema", str(SCHEMA_PATH)])
    captured = capsys.readouterr()
    assert code == 1
    assert "1개 실패" in captured.out


def test_schema_is_valid_draft202012() -> None:
    """번들 스키마 자체가 유효한 draft 2020-12 문서다."""
    import jsonschema

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    cls = jsonschema.Draft202012Validator
    cls.check_schema(schema)
