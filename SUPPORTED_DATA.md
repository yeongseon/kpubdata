# 지원 공공데이터 현황

이 문서는 KPubData가 지원하는 공공데이터 목록과 진행 현황을 관리하는 기준 문서입니다.

> **상태 정의**
>
> - 지원: 구현 완료 + fixture/unit/contract 테스트 통과
> - 진행 중: 구현 중이지만 아직 테스트가 완료되지 않음
> - 예정: 후보 단계 (이슈 등록 또는 아이디어)
>
> **검증 정의**
>
> - 테스트 검증: fixture 기반 unit 테스트 + contract 테스트 통과
> - 실API 검증: 위 조건 + 실 API integration 테스트 통과 ([#80](https://github.com/yeongseon/kpubdata/issues/80))

## 현재 지원

| 상태 | 검증 | Provider | Dataset ID | 데이터셋명 | 인증 | 공식 문서 | 비고 |
|---|---|---|---|---|---|---|---|
| 지원 | 테스트 검증 | 공공데이터포털 (`datago`) | `apt_trade` | 아파트매매 실거래가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 국토교통부 제공 |
| 지원 | 테스트 검증 | 공공데이터포털 (`datago`) | `village_fcst` | 단기예보 조회서비스 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 기상청 제공 |
| 지원 | 테스트 검증 | 공공데이터포털 (`datago`) | `ultra_srt_ncst` | 초단기실황 조회서비스 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 기상청 제공 |
| 지원 | 테스트 검증 | 공공데이터포털 (`datago`) | `air_quality` | 대기오염정보 조회서비스 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | |
| 지원 | 테스트 검증 | 공공데이터포털 (`datago`) | `bus_arrival` | 경기도 버스도착정보 조회서비스 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | |
| 지원 | 테스트 검증 | 공공데이터포털 (`datago`) | `hospital_info` | 병원정보서비스 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | |
| 지원 | 실API 검증 | 한국은행 ECOS (`bok`) | `base_rate` | 한국은행 기준금리 | [ECOS](https://ecos.bok.or.kr/api/) 인증키 | [ecos.bok.or.kr](https://ecos.bok.or.kr/api/) | |
| 지원 | 실API 검증 | 통계청 KOSIS (`kosis`) | `population_migration` | 시도별 이동자수 | [KOSIS](https://kosis.kr/openapi/index/index.jsp) 인증키 | [kosis.kr](https://kosis.kr/openapi/index/index.jsp) | |
| 지원 | 실API 검증 | 지방재정365 (`lofin`) | `expenditure_budget` | 세출결산총괄 | [지방재정365](https://www.lofin365.go.kr) 인증키 | [lofin365.go.kr](https://www.lofin365.go.kr) | API 코드: AJGCF |
| 지원 | 실API 검증 | 지방재정365 (`lofin`) | `revenue_budget` | 세입결산총괄 | [지방재정365](https://www.lofin365.go.kr) 인증키 | [lofin365.go.kr](https://www.lofin365.go.kr) | API 코드: IIBBH |
| 지원 | 실API 검증 | 지방재정365 (`lofin`) | `expenditure_function` | 기능별세출 | [지방재정365](https://www.lofin365.go.kr) 인증키 | [lofin365.go.kr](https://www.lofin365.go.kr) | API 코드: GGNSE |
| 지원 | 실API 검증 | 지방재정365 (`lofin`) | `debt_ratio` | 채무비율현황 | [지방재정365](https://www.lofin365.go.kr) 인증키 | [lofin365.go.kr](https://www.lofin365.go.kr) | API 코드: HEDFC |
| 지원 | 실API 검증 | 지방재정365 (`lofin`) | `fiscal_independence` | 재정자립도현황 | [지방재정365](https://www.lofin365.go.kr) 인증키 | [lofin365.go.kr](https://www.lofin365.go.kr) | API 코드: JFIED |
| 지원 | 실API 검증 | 지방재정365 (`lofin`) | `revenue_by_source` | 재원별 회계별 세입결산 | [지방재정365](https://www.lofin365.go.kr) 인증키 | [lofin365.go.kr](https://www.lofin365.go.kr) | API 코드: FIACRV |

## 진행 예정 / 진행 중

| 상태 | Provider | Dataset ID | 데이터셋명 | 메모 |
|---|---|---|---|---|
| 예정 | 공공데이터포털 (`datago`) | `apt_rent` | 아파트 전월세 실거래가 | `apt_trade`와 인접한 확장 후보 |
| 예정 | 기상청 | `weather_forecast` | 동네예보 | provider/adapter 구조 확정 후 착수 |

## 갱신 규칙

새로운 adapter를 추가할 때는 아래 절차에 따라 이 문서를 함께 업데이트합니다.

1. **기획 단계**: `진행 예정 / 진행 중` 표에 `예정`으로 추가
2. **구현 시작**: fixture 수집 또는 adapter skeleton이 생기면 `진행 중`으로 변경
3. **지원 전환**: fixture + unit test + contract test + 문서가 모두 포함된 PR이 merge되면 `현재 지원` 표로 이동하고 `지원`으로 표시
4. **README 동기화**: `지원` 항목만 [README.md](./README.md)의 요약 표에 추가
5. **명칭 규칙**: provider slug와 dataset id는 코드의 실제 이름과 정확히 일치시킬 것
6. **PR 포함**: adapter 추가/상태 변경 PR에는 이 문서의 업데이트를 반드시 포함
