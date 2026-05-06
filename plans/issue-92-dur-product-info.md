# DUR품목정보 조회 추가 계획 (Issue #92)

## 범위
- 공공데이터포털(data.go.kr) 식품의약품안전처 의약품안전사용서비스(DUR)품목정보 API 중 `getDurPrdlstInfoList03` operation 하나만 추가한다.
- 데이터셋 키는 `dur_product_info`를 사용한다.
- 한국어 명칭은 API 목록의 `DUR품목정보 조회`를 기준으로 문서와 카탈로그에 반영한다.
- 전체 DUR API를 한 번에 구현하지 않고, 기존 `dur_usjnt_taboo`, `dur_older_adult_caution`과 같은 metadata-only 패턴을 따른다.
- `DataGoAdapter` 구조나 public API는 변경하지 않는다.

## 수정 대상
- `src/kpubdata/providers/datago/catalogue.json`
- `tests/fixtures/datago/success_dur_product_info.json`
- `tests/unit/providers/datago/test_fixtures.py`
- `tests/contract/test_datago.py`
- `SUPPORTED_DATA.md`

## 리스크
- fixture 기반 테스트 검증만 수행하므로 `SUPPORTED_DATA.md`에는 `실API 검증`이 아닌 `테스트 검증`으로 표기한다.
- operation-specific 원본 필드는 provider-native 형태로 유지하며, 공통 DUR 모델이나 추상화를 만들지 않는다.
- data.go.kr API가 JSON+XML을 제공하지만 이번 변경은 기존 datago JSON envelope 경로만 검증한다.
- 실 API integration 테스트가 없으므로 포털의 실제 응답 필드 추가/변경 가능성은 남아 있다.

## 검증 단계
1. `uv run ruff check .`
2. `uv run ruff format --check .`
3. `uv run mypy src`
4. `uv run pytest`
