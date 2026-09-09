"""catalogue → spec 일괄 변환기 (migrate-to-spec 웨이브 도구).

data.go.kr standard envelope 계열(datago 직영 + localdata + semas + kipris)의
catalogue 엔트리를 spec YAML로 기계 생성한다. 실행기가 아직 지원하지 않는
변이/커스텀 Provider는 스킵 규칙으로 제외한다.

사용법:
    uv run python scripts/gen_specs_from_catalogue.py --provider localdata [--dry-run] [--limit N]

생성물:
- ``src/kpubdata/specs/{provider}/{dataset_key}.yaml`` (이미 있으면 건너뜀)
- 예제 1개(``default``: 필터 없음, page 1, page_size 10)

주의: 생성 후에는 반드시 ``make record DATASET=<id>`` 로 fixture를 만들어야
``make verify``가 통과한다. 녹화 실패(필수 파라미터·폐기) 목록은 로그로 남기고
해당 spec은 ``--prune-failures`` 로 제거한다.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SPECS_DIR = REPO_ROOT / "src" / "kpubdata" / "specs"
PROVIDERS_DIR = REPO_ROOT / "src" / "kpubdata" / "providers"

# 실행기/스키마 범위 밖 — 변환 금지 (Phase 0 커스텀 목록 + envelope 변형 + 비표준 인증/페이지네이션)
SKIP_KEYS: dict[str, set[str]] = {
    "datago": {
        # envelope 변형 / call_raw 전용 / odcloud 페이지네이션
        "bus_arrival",
        "road_traffic",
        "social_enterprise",
    },
}
# 변환 대상 Provider 화이트리스트: query_param 인증 + standard envelope + page_no_rows 조합만.
ELIGIBLE_PROVIDERS = frozenset({"datago", "localdata", "semas", "kipris"})

_TEMPLATE = """# catalogue 일괄 변환 생성 (scripts/gen_specs_from_catalogue.py) — 수동 보강 가능
id: {provider}.{dataset_key}
provider: {provider}
title: {title}
description: {description}

source:
  url: https://www.data.go.kr

endpoint:
  base_url: {base_url}
  operation: {operation}
  method: GET
  format_param:
    name: {format_param}
    values:
      json: json
      xml: xml

auth:
  type: query_param
  param_name: {service_key_param}
  provider_key: datago

params: []

response:
  format: json
  envelope: datago_standard
  items_path: response.body.items.item
  total_count_path: response.body.totalCount
  error:
    style: header_result_code
    code_path: response.header.resultCode
    ok_values: ["00", "000", 0]

pagination:
  type: page_no_rows
  page_param: pageNo
  size_param: numOfRows
  max_size: {max_size}

fields: []

examples:
  - name: default
    description: 필터 없음 첫 페이지
    params: {{}}
    page: 1
    page_size: 10

status: active
"""


def _quote(text: str) -> str:
    """YAML 스칼라 안전 인용 (콜론·특수문자 포함 시)."""
    if any(ch in text for ch in ":#{}[]'\"") or text != text.strip():
        return json.dumps(text, ensure_ascii=False)
    return text


def convert_provider(
    provider: str,
    *,
    dry_run: bool = False,
    limit: int | None = None,
) -> tuple[list[str], list[str]]:
    """Provider catalogue에서 변환 가능한 엔트리를 spec으로 만든다.

    반환값: (생성된 dataset id 목록, 스킵 목록 'key:사유').
    """
    catalogue_path = PROVIDERS_DIR / provider / "catalogue.json"
    entries = json.loads(catalogue_path.read_text(encoding="utf-8"))
    provider_dir = SPECS_DIR / provider
    skip = SKIP_KEYS.get(provider, set())

    created: list[str] = []
    skipped: list[str] = []
    for entry in entries:
        dataset_key = entry.get("dataset_key", "")
        dataset_id = f"{provider}.{dataset_key}"
        reason = ""
        if dataset_key in skip:
            reason = "변형/커스텀 (Phase 0 분류)"
        elif not entry.get("base_url") or not entry.get("default_operation"):
            reason = "엔드포인트 정보 없음(raw 전용 게이트 등)"
        elif (provider_dir / f"{dataset_key}.yaml").exists():
            reason = "spec 이미 존재"
        elif entry.get("service_key_param") != "serviceKey":
            reason = f"비표준 인증 파라미터({entry.get('service_key_param')!r})"
        elif entry.get("envelope_style"):
            reason = f"envelope 변형({entry['envelope_style']})"
        elif (
            entry.get("raw_metadata", {}).get("pagination_params")
            if isinstance(entry.get("raw_metadata"), dict)
            else False
        ):
            reason = "odcloud 페이지네이션"
        if reason:
            skipped.append(f"{dataset_key}: {reason}")
            continue
        if limit is not None and len(created) >= limit:
            break

        title = entry.get("name", dataset_key)
        description = entry.get("description") or f"{title} 데이터셋 (catalogue 일괄 변환)."
        content = _TEMPLATE.format(
            provider=provider,
            dataset_key=dataset_key,
            title=_quote(str(title)),
            description=_quote(str(description)),
            base_url=entry["base_url"],
            operation=entry["default_operation"],
            format_param=entry.get("format_param", "_type"),
            service_key_param=entry.get("service_key_param", "serviceKey"),
            max_size=int(entry.get("query_support", {}).get("max_page_size", 1000) or 1000),
        )
        if not dry_run:
            provider_dir.mkdir(parents=True, exist_ok=True)
            (provider_dir / f"{dataset_key}.yaml").write_text(content, encoding="utf-8")
        created.append(dataset_id)
    return created, skipped


def main(argv: list[str] | None = None) -> int:
    """CLI 진입점."""
    parser = argparse.ArgumentParser(description="catalogue → spec 일괄 변환")
    parser.add_argument("--provider", required=True, choices=sorted(ELIGIBLE_PROVIDERS))
    parser.add_argument("--dry-run", action="store_true", help="파일 생성 없이 개수만")
    parser.add_argument("--limit", type=int, help="최대 생성 수 (테스트/증분용)")
    args = parser.parse_args(argv)

    created, skipped = convert_provider(args.provider, dry_run=args.dry_run, limit=args.limit)
    print(f"[{args.provider}] 생성 {len(created)}건 / 스킵 {len(skipped)}건")
    for line in skipped[:10]:
        print(f"  스킵 {line}")
    if args.dry_run:
        for dataset_id in created[:5]:
            print(f"  (dry-run) {dataset_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
