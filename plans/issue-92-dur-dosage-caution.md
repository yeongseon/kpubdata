# DUR 용량주의 정보조회 추가 계획 (Issue #92)

## 범위

- 공공데이터포털(data.go.kr) 식품의약품안전처 의약품안전사용서비스(DUR)품목정보 API 중 `getCpctyAtentInfoList03` operation 하나만 추가한다.
- 데이터셋 키는 `dur_dosage_caution`을 사용한다.
- 한국어 명칭은 API 목록의 `용량주의 정보조회`를 기준으로 카탈로그, 지원 현황, PR 본문에 반영한다.
- 전체 DUR API를 한 번에 구현하지 않고, 기존 `dur_usjnt_taboo`, `dur_older_adult_caution`과 같은 metadata-only 패턴을 따른다.

## 수정 대상

- `src/kpubdata/providers/datago/catalogue.json`
- `tests/fixtures/datago/success_dur_dosage_caution.json`
- `tests/unit/providers/datago/test_fixtures.py`
- `tests/contract/test_datago.py`
- `SUPPORTED_DATA.md`
- `plans/issue-92-dur-dosage-caution.md`

## 리스크

- 실제 API integration 테스트는 이번 작업 범위가 아니므로 `SUPPORTED_DATA.md`에는 `테스트 검증`으로만 표시한다.
- operation-specific 원본 필드는 provider-native 형태로 유지하며, 공통 DUR 모델이나 추상화를 만들지 않는다.
- API 키, serviceKey, token, secret은 코드, fixture, 문서에 포함하지 않는다.

## 검증

- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src`
- `uv run pytest`
