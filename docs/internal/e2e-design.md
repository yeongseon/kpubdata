# Cross-Repo E2E 테스트 설계 (#282)

## 목표
kpubdata → Builder → Studio 전체 경로를 자동 검증한다.

## 3단계 접근

### Phase 1: kpubdata 내부 E2E (본 PR)
- 실API fetch → 정규화 → fixture 검증 → BuildSpec YAML 생성 가능성 확인
- `tests/e2e/test_pipeline.py` — 하나의 데이터셋에 대해:
  1. Client.dataset(id) 조회
  2. RecordBatch 구조 검증 (items, total_count, next_page)
  3. fields[] 정규화 규칙 동작 확인
  4. `make verify` 4단계 통과 = E2E 성공

### Phase 2: kpubdata ↔ Builder 연동 (향후)
- kpubdata Client로 fetch → Builder BuildSpec으로 변환 → Builder 빌드 실행
- prerequisite: Builder 로컬 서버 기동 또는 in-process BuilderService
- 검증: Build 결과 gold 산출물이 kpubdata RecordBatch와 필드 일치

### Phase 3: 전체 경로 (Studio 포함, 향후)
- Studio e2e (Playwright) → Builder API 호출 → kpubdata 데이터 조회 → UI 렌더링
- prerequisite: Studio 개발 서버 + Builder API + kpubdata API 키
- 검증: Studio 화면에 실데이터 표시

## 기술 결정
- Phase 1은 기존 `@pytest.mark.integration` marker 재사용
- Phase 2는 별도 marker `@pytest.mark.e2e_builder` 예정
- Phase 3은 Studio e2e 하우스 내부 (Playwright) — 이 리포 범위 밖

## 현재 상태
- Phase 1: 본 PR에서 구현
- Phase 2~3: Builder/Studio 개발 서버 필요 → 별도 이슈로 추적
