# 파일럿 로그 (Phase 4, #381)

> dataset-request 이슈를 에이전트 절차로 처리한 기록. 실패 원인 분류:
> `doc-wrong` / `auth-blocked` / `schema-unstable` / `agent-misread` / `spec-schema-gap` / `tooling`

| # | 이슈 | 데이터셋 | 반복 | 통과 | 사람 수정 | 실패 원인 | 비고 |
|---|---|---|---|---|---|---|---|
| 1 | #396 | datago.air_station | 2 | ✅ | 없음 | doc-wrong (1회) | 요청 서비스(약국) 폐기 → 정준 변경. pm25 선택 필드 실측 교훈 |

## 집계 (업데이트: 2026-09-09)
- 시도 1건 / 통과 1건 / 무수정 merge 1건 → **통과율 100% (n=1)**
- 원인 분포: doc-wrong 1
