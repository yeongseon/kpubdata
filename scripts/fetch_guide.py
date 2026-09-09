"""활용가이드 문서 캐시 — data.go.kr 데이터셋 페이지를 텍스트로 저장한다.

사용법:
    uv run python scripts/fetch_guide.py \
        --url "https://www.data.go.kr/data/15001241/openapi.do" --id datago.hospital_info

출력: ``docs/sources/{id}/guide.txt`` (+ ``url`` 파일). agent는 브라우징 대신
이 캐시를 우선 읽는다(AGENTS.md 데이터셋 추가 절차 1단계).

정직한 제약: data.go.kr 상세 페이지는 동적 렌더링이 많아 정적 fetch로는
목록·기본 정보 위주만 담긴다. 부족하면 URL 원문을 직접 확인해야 한다.
실패해도 exit 0으로 끝내지 않고 상태를 보고한다(캐시 부재를 숨기지 않는다).
"""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_DIR = REPO_ROOT / "docs" / "sources"


class _TextExtractor(HTMLParser):
    """HTML에서 스크립트/스타일을 제외한 텍스트를 모은다."""

    _SKIP = {"script", "style", "noscript"}

    def __init__(self) -> None:
        super().__init__()
        self.chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """스킵 태그 진입 깊이를 센다."""
        if tag in self._SKIP:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        """스킵 태그를 벗어난다."""
        if tag in self._SKIP and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        """텍스트 노드를 모은다(스킵 중이 아닐 때)."""
        if self._skip_depth == 0 and data.strip():
            self.chunks.append(data.strip())


def extract_text(html: str) -> str:
    """HTML을 줄 단위 텍스트로 정리한다."""
    parser = _TextExtractor()
    parser.feed(html)
    lines = [line for line in parser.chunks if len(line) > 1]
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def fetch_guide(url: str, dataset_id: str, *, sources_dir: Path = SOURCES_DIR) -> Path | None:
    """가이드 페이지를 받아 텍스트 캐시로 저장한다."""
    out_dir = sources_dir / dataset_id
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        response = httpx.get(
            url,
            timeout=30,
            follow_redirects=True,
            headers={"User-Agent": "kpubdata-guide-cache/1.0"},
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        print(f"실패: {url} — {exc}")
        return None
    text = extract_text(response.text)
    out_path = out_dir / "guide.txt"
    out_path.write_text(f"source: {url}\n\n{text}\n", encoding="utf-8")
    (out_dir / "url").write_text(url, encoding="utf-8")
    print(f"캐시됨: {out_path} ({len(text)}자)")
    if len(text) < 500:
        print("주의: 정적 fetch로 얻은 내용이 짧다(동적 렌더링 추정) — URL 원문 확인 필요")
    return out_path


def main(argv: list[str] | None = None) -> int:
    """CLI 진입점."""
    parser = argparse.ArgumentParser(description="data.go.kr 활용가이드 캐시")
    parser.add_argument("--url", required=True, help="데이터셋 페이지 URL")
    parser.add_argument("--id", required=True, help="데이터셋 id (예: datago.hospital_info)")
    args = parser.parse_args(argv)
    result = fetch_guide(args.url, args.id)
    return 0 if result is not None else 1


if __name__ == "__main__":
    sys.exit(main())
