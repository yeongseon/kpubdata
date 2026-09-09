---
name: kpubdata-dataset
description: kpubdata 데이터셋 추가·수리 표준 절차 (spec → make record → make verify). 데이터셋 작업 요청 시 이 스킬을 따른다.
---

# kpubdata 데이터셋 절차

## 데이터셋 추가 (기본 경로)

완성 여부는 `make verify DATASET={provider}.{dataset_key}` exit code로 기계 판정한다.

1. 이슈의 data.go.kr URL에서 활용가이드 확인 (`docs/sources/{dataset}/` 캐시 우선)
2. 골든 예제 복사 → `src/kpubdata/specs/{provider}/{dataset_key}.yaml`
   - 단순 `datago.hospital_info` / 페이지네이션 `datago.apt_trade` / XML `datago.village_fcst`
   - 계약 `src/kpubdata/specs/schema.json`, 검증 `uv run python scripts/validate_spec.py`
3. `make record DATASET=<id>` — 실API fixture 3종(raw/meta/expected) 기록
4. `examples/{provider}/{dataset_key}.py` — 파라미터는 spec examples[]와 동일(replay 계약), assert ≥1
5. `make verify DATASET=<id>` exit 0까지 반복
6. `SUPPORTED_DATA.md` 갱신 + `uv run python scripts/gen_docs_examples.py`

## 드리프트 수리

1. 재현 → 원인 분류(doc-wrong / schema-unstable / spec-schema-gap / tooling)
2. spec 필드 갱신 → `make record` 재기록 → 예제 확인 → `SUPPORTED_DATA.md` 검증일 갱신
3. spec-schema-gap이면 needs-human

## 공통 규칙

- 수정 허용: `src/kpubdata/specs/`, `examples/`, `tests/fixtures/`(record로만), `docs/datasets/`, `docs/sources/`, `SUPPORTED_DATA.md`
- 수정 금지: `src/kpubdata/core/`, `src/kpubdata/providers/`, `tests/contract/`, `tests/unit/`, `scripts/`, `Makefile`, `.github/`
- 금지: fixture 수동 작성, 테스트 skip, assert 약화, `status: broken` 회피
- 3회 실패 → `needs-human` + 원인 요약 후 중단
- 함정 목록: AGENTS.md "흔한 함정" 참조 (영문 필드명, TMP/PCP, base_date 최신성, envelope 4종)
