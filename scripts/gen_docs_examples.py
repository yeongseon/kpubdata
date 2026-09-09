"""문서용 예제 생성기 — examples/ 스크립트에서 docs/dataset-examples.md 를 만든다.

사용법:
    uv run python scripts/gen_docs_examples.py           # 생성
    uv run python scripts/gen_docs_examples.py --check   # 드리프트 검사(CI용, exit 1)

손으로 쓴 예제 블록 대신 항상 이 생성물을 인용한다(#379 2.3) —
예제 스크립트가 곧 검증 대상(replay 실행)이므로 문서와 코드가 어긋날 수 없다.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = REPO_ROOT / "examples"
OUTPUT_PATH = REPO_ROOT / "docs" / "dataset-examples.md"

_HEADER = """# 데이터셋 예제

> 이 문서는 `examples/` 스크립트에서 자동 생성했다 (`scripts/gen_docs_examples.py`).
> 직접 편집하지 않는다 — 스크립트를 고치고 다시 생성한다.

각 예제는 `KPUBDATA_MODE=replay` 환경에서 API 키 없이 결정적으로 실행된다
(`make verify` 4단계). 실호출은 해당 Provider API 키 설정 후 그대로 실행하면 된다.
"""


def generate(examples_dir: Path = EXAMPLES_DIR) -> str:
    """examples 트리에서 마크다운 문서 내용을 생성한다."""
    blocks: list[str] = [_HEADER]
    scripts = sorted(
        path
        for path in examples_dir.rglob("*.py")
        if path.name != "__init__.py"
        and path.parent != examples_dir
        # 배치 자동 생성 예제는 문서에서 제외(수록 규모·큐레이션 이유)
        and not path.read_text(encoding="utf-8").startswith("# auto-generated: docs-exclude")
    )
    if not scripts:
        return _HEADER + "\n(예제 스크립트가 없다.)\n"

    current_provider = ""
    for script in scripts:
        provider = script.parent.name
        if provider != current_provider:
            blocks.append(f"\n## {provider}\n")
            current_provider = provider
        dataset_id = f"{provider}.{script.stem}"
        blocks.append(f"\n### `{dataset_id}`\n")
        blocks.append(
            f"[소스](https://github.com/yeongseon/kpubdata/blob/main/examples/{provider}/{script.name})\n"
        )
        blocks.append("```python")
        blocks.append(script.read_text(encoding="utf-8").rstrip())
        blocks.append("```\n")
    return "\n".join(blocks) + "\n"


def main(argv: list[str] | None = None) -> int:
    """CLI 진입점 — 생성 또는 드리프트 검사."""
    parser = argparse.ArgumentParser(description="docs/dataset-examples.md 생성기")
    parser.add_argument("--check", action="store_true", help="생성 결과가 커밋과 일치하는지만 검사")
    args = parser.parse_args(argv)

    content = generate()
    if args.check:
        current = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.is_file() else ""
        if current != content:
            print(
                "드리프트: docs/dataset-examples.md 이(가) examples/ 와 불일치 — "
                "재생성 후 커밋하세요."
            )
            return 1
        print("일치: docs/dataset-examples.md 최신 상태")
        return 0

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(content, encoding="utf-8")
    shown = (
        OUTPUT_PATH.relative_to(REPO_ROOT) if OUTPUT_PATH.is_relative_to(REPO_ROOT) else OUTPUT_PATH
    )
    print(f"생성 완료: {shown}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
