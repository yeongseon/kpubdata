# 파일럿 로그 (Phase 4, #381)

> dataset-request 이슈를 에이전트 절차로 처리한 기록. 실패 원인 분류:
> `doc-wrong` / `auth-blocked` / `schema-unstable` / `agent-misread` / `spec-schema-gap` / `tooling`

| # | 이슈 | 데이터셋 | 반복 | 통과 | 사람 수정 | 실패 원인 | 비고 |
|---|---|---|---|---|---|---|---|
| 1 | #396 | datago.air_station | 2 | ✅ | 없음 | doc-wrong (1회) | 요청 서비스(약국) 폐기 → 정준 변경. pm25 선택 필드 실측 교훈 |
| 2 | #398 | datago.ultra_srt_fcst | 1 | ✅ | 없음 | — | 1회 통과. 초단기 카테고리 T1H/RN1 (단기 TMP/PCP와 상이 — 함정 추가) |
| 3 | #399 | (수행 안 함) | - | ➖ | - | doc-wrong | 미세먼지 예보 서비스 전 경로 폐기 — needs-human (활용신청 필요) |
| 4 | #400 | (수행 안 함) | - | ➖ | - | duplicate | neis.school_info 이미 존재 |
| 5 | #401 | (수행 안 함) | - | ➖ | - | doc-wrong + already-covered | Dev 변형 폐기, 기존 apt_rent(비Dev) 정상 — 중복 |
| 6 | #402 | (수행 안 함) | - | ➖ | - | doc-wrong + already-covered | Dev 변형 폐기, 기존 offi_trade(비Dev) 정상 — 중복 |

## 집계 (업데이트: 2026-09-09, 1차 라운드 종료)
- 구현 시도 2건 / 통과 2건 / 무수정 merge 2건 → **구현 통과율 100% (n=2)**
- 요청 6건 중 반려 4건(폐기 3·중복 2·활용신청 필요 1 — #399는 폐기+신청 복합): 프로브 선행이 무효 요청을 즉시 걸러냄
- 원인 분포: doc-wrong 4 / duplicate 2(중복 포함 시) / auth-blocked(신청 필요) 1
- 개선 반영: 함정 목록에 "Dev 변형은 폐기된 경우 다수 — 비Dev 기존 서비스 확인" 추가 예치
