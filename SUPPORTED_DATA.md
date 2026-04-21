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
>
> **실API 최종 검증일**
>
> - 실API 검증을 마지막으로 성공한 날짜 (`YYYY-MM-DD`). 테스트 검증만 완료된 데이터셋은 `-`로 표기합니다.
> - 검증일이 90일을 초과한 데이터셋은 재검증을 권장합니다.

## 현재 지원

| 상태 | 검증 | 실API 최종 검증일 | Provider | Dataset ID | 데이터셋명 | 인증 | 공식 문서 | 비고 |
|---|---|---|---|---|---|---|---|---|
| 지원 | 실API 검증 | 2026-04-21 | 공공데이터포털 (`datago`) | `apt_trade` | 아파트매매 실거래가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 국토교통부 제공 |
| 지원 | 실API 검증 | 2026-04-21 | 공공데이터포털 (`datago`) | `apt_rent` | 아파트 전월세 실거래가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 국토교통부 제공 |
| 지원 | 실API 검증 | 2026-04-21 | 공공데이터포털 (`datago`) | `offi_trade` | 오피스텔 매매 실거래가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 국토교통부 제공 |
| 지원 | 실API 검증 | 2026-04-21 | 공공데이터포털 (`datago`) | `offi_rent` | 오피스텔 전월세 실거래가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 국토교통부 제공 |
| 지원 | 테스트 검증 | - | 공공데이터포털 (`datago`) | `rh_trade` | 연립다세대 매매 실거래가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 국토교통부 제공, 활용신청 승인 반영 대기 (2026-04-21 시점 403) |
| 지원 | 실API 검증 | 2026-04-21 | 공공데이터포털 (`datago`) | `rh_rent` | 연립다세대 전월세 실거래가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 국토교통부 제공 |
| 지원 | 실API 검증 | 2026-04-21 | 공공데이터포털 (`datago`) | `sh_trade` | 단독/다가구 매매 실거래가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 국토교통부 제공 |
| 지원 | 실API 검증 | 2026-04-21 | 공공데이터포털 (`datago`) | `sh_rent` | 단독/다가구 전월세 실거래가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 국토교통부 제공 |
| 지원 | 실API 검증 | 2026-04-21 | 공공데이터포털 (`datago`) | `village_fcst` | 단기예보 조회서비스 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 기상청 제공 |
| 지원 | 실API 검증 | 2026-04-21 | 공공데이터포털 (`datago`) | `ultra_srt_ncst` | 초단기실황 조회서비스 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 기상청 제공 |
| 지원 | 실API 검증 | 2026-04-21 | 공공데이터포털 (`datago`) | `air_quality` | 대기오염정보 조회서비스 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | |
| 지원 | 실API 검증 | 2026-04-21 | 공공데이터포털 (`datago`) | `bus_arrival` | 경기도 버스도착정보 조회서비스 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 경기도 v2 endpoint (`getBusArrivalListv2`) + 자체 envelope (`msgHeader`/`msgBody`) |
| 지원 | 실API 검증 | 2026-04-21 | 공공데이터포털 (`datago`) | `hospital_info` | 병원정보서비스 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | |
| 지원 | 실API 검증 | 2026-04-20 | 공공데이터포털 (`datago`) | `tour_kor_area` | 한국관광공사 지역기반 관광정보 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr/15101578](https://www.data.go.kr/data/15101578/openapi.do) | TourAPI KorService2 / `areaBasedList2` |
| 지원 | 실API 검증 | 2026-04-20 | 공공데이터포털 (`datago`) | `tour_kor_location` | 한국관광공사 위치기반 관광정보 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr/15101578](https://www.data.go.kr/data/15101578/openapi.do) | TourAPI KorService2 / `locationBasedList2` |
| 지원 | 실API 검증 | 2026-04-20 | 공공데이터포털 (`datago`) | `tour_kor_keyword` | 한국관광공사 키워드 검색 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr/15101578](https://www.data.go.kr/data/15101578/openapi.do) | TourAPI KorService2 / `searchKeyword2` |
| 지원 | 실API 검증 | 2026-04-20 | 공공데이터포털 (`datago`) | `tour_kor_festival` | 한국관광공사 행사정보 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr/15101578](https://www.data.go.kr/data/15101578/openapi.do) | TourAPI KorService2 / `searchFestival2` |
| 지원 | 테스트 검증 | - | 공공데이터포털 (`datago`) | `metro_fare` | 서울교통공사 실시간 운임정보 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr/15143846](https://www.data.go.kr/data/15143846/openapi.do) | 서울교통공사 / `getRltmFare2` (실API 502: 게이트웨이→백엔드 SSL 검증 실패, 포털 측 인프라 이슈, [#139](https://github.com/yeongseon/kpubdata/issues/139)) |
| 지원 | 테스트 검증 | - | 공공데이터포털 (`datago`) | `metro_path` | 서울교통공사 최단경로 이동정보 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr/15143842](https://www.data.go.kr/data/15143842/openapi.do) | 서울교통공사 / `getShtrmPath` (필수 파라미터 `dptreStnNm`/`arvlStnNm` 등, 활용가이드 확인 필요, [#140](https://github.com/yeongseon/kpubdata/issues/140)) |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `general_restaurant` | 일반음식점 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, service_name 실API 검증 완료 (data.go.kr 이관) |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `rest_cafe` | 휴게음식점 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, service_name 실API 검증 완료 |
| 지원 | 테스트 검증 | - | 통계청 통계지리정보서비스 (`sgis`) | `boundary.sido` | 시도 행정구역 경계 | SGIS `consumer_key` + `consumer_secret` | [sgis.kostat.go.kr](https://sgis.kostat.go.kr/developer/html/main.html) | GeoJSON FeatureCollection 응답을 레코드 단위(`items`)로 정규화 |
| 지원 | 테스트 검증 | - | 통계청 통계지리정보서비스 (`sgis`) | `boundary.sigungu` | 시군구 행정구역 경계 | SGIS `consumer_key` + `consumer_secret` | [sgis.kostat.go.kr](https://sgis.kostat.go.kr/developer/html/main.html) | `boundary/hadmarea.geojson` + `low_search` 기반 조회 |
| 지원 | 테스트 검증 | - | 통계청 통계지리정보서비스 (`sgis`) | `boundary.emd` | 읍면동 행정구역 경계 | SGIS `consumer_key` + `consumer_secret` | [sgis.kostat.go.kr](https://sgis.kostat.go.kr/developer/html/main.html) | fixture/contract 검증 완료, 실API 검증은 후속 |
| 지원 | 테스트 검증 | - | 서울 열린데이터광장 (`seoul`) | `subway_realtime_arrival` | 서울시 지하철 실시간 도착정보 | [서울 열린데이터광장](https://data.seoul.go.kr/) 인증키 | [data.seoul.go.kr](https://data.seoul.go.kr/) | 경로 기반 인증키 + 서비스별 top-level envelope |
| 지원 | 테스트 검증 | - | 서울 열린데이터광장 (`seoul`) | `bike_rent_month` | 서울시 공공자전거 이용정보(월별) | [서울 열린데이터광장](https://data.seoul.go.kr/) 인증키 | [data.seoul.go.kr](https://data.seoul.go.kr/) | 경로 기반 인증키 + 인덱스 페이지네이션 |
| 지원 | 실API 검증 | 2025-04-15 | 한국은행 ECOS (`bok`) | `base_rate` | 한국은행 기준금리 | [ECOS](https://ecos.bok.or.kr/api/) 인증키 | [ecos.bok.or.kr](https://ecos.bok.or.kr/api/) | |
| 지원 | 실API 검증 | 2025-04-15 | 통계청 KOSIS (`kosis`) | `population_migration` | 시도별 이동자수 | [KOSIS](https://kosis.kr/openapi/index/index.jsp) 인증키 | [kosis.kr](https://kosis.kr/openapi/index/index.jsp) | |
| 지원 | 실API 검증 | 2025-04-16 | 지방재정365 (`lofin`) | `expenditure_budget` | 세출결산총괄 | [지방재정365](https://www.lofin365.go.kr) 인증키 | [lofin365.go.kr](https://www.lofin365.go.kr) | API 코드: AJGCF |
| 지원 | 실API 검증 | 2025-04-16 | 지방재정365 (`lofin`) | `revenue_budget` | 세입결산총괄 | [지방재정365](https://www.lofin365.go.kr) 인증키 | [lofin365.go.kr](https://www.lofin365.go.kr) | API 코드: IIBBH |
| 지원 | 실API 검증 | 2025-04-16 | 지방재정365 (`lofin`) | `expenditure_function` | 기능별세출 | [지방재정365](https://www.lofin365.go.kr) 인증키 | [lofin365.go.kr](https://www.lofin365.go.kr) | API 코드: GGNSE |
| 지원 | 실API 검증 | 2025-04-16 | 지방재정365 (`lofin`) | `debt_ratio` | 채무비율현황 | [지방재정365](https://www.lofin365.go.kr) 인증키 | [lofin365.go.kr](https://www.lofin365.go.kr) | API 코드: HEDFC |
| 지원 | 실API 검증 | 2025-04-16 | 지방재정365 (`lofin`) | `fiscal_independence` | 재정자립도현황 | [지방재정365](https://www.lofin365.go.kr) 인증키 | [lofin365.go.kr](https://www.lofin365.go.kr) | API 코드: JFIED |
| 지원 | 실API 검증 | 2025-04-17 | 지방재정365 (`lofin`) | `revenue_by_source` | 재원별 회계별 세입결산 | [지방재정365](https://www.lofin365.go.kr) 인증키 | [lofin365.go.kr](https://www.lofin365.go.kr) | API 코드: FIACRV |

## 진행 예정 / 진행 중

| 상태 | Provider | Dataset ID | 데이터셋명 | 메모 |
|---|---|---|---|---|
| 예정 | 기상청 | `weather_forecast` | 동네예보 | provider/adapter 구조 확정 후 착수 |

## 갱신 규칙

새로운 adapter를 추가할 때는 아래 절차에 따라 이 문서를 함께 업데이트합니다.

1. **기획 단계**: `진행 예정 / 진행 중` 표에 `예정`으로 추가
2. **구현 시작**: fixture 수집 또는 adapter skeleton이 생기면 `진행 중`으로 변경
3. **지원 전환**: fixture + unit test + contract test + 문서가 모두 포함된 PR이 merge되면 `현재 지원` 표로 이동하고 `지원`으로 표시
4. **README 동기화**: `지원` 항목만 [README.md](./README.md)의 요약 표에 추가
5. **명칭 규칙**: provider slug와 dataset id는 코드의 실제 이름과 정확히 일치시킬 것
6. **PR 포함**: adapter 추가/상태 변경 PR에는 이 문서의 업데이트를 반드시 포함

## 비상구 / 고급 기능 (Escape Hatches)

정규화된 데이터셋은 아니지만, 미등록 endpoint를 즉시 호출할 수 있게 해주는 raw 비상구입니다. 정규화·페이지네이션·스키마·엔드포인트별 호환은 보장되지 않으며, 호출자가 원본 응답을 직접 처리해야 합니다.

| Provider | 비상구 키 | 용도 | 제약 |
|---|---|---|---|
| 공공데이터포털 (`datago`) | `datago.generic` | 카탈로그에 없는 임의의 data.go.kr endpoint를 `call_raw(operation, _base_url=..., **params)`로 호출 | `list()` 미지원 · 표준 envelope 검증은 옵션 (`_envelope=False`) · 응답 정규화 없음 · `*.data.go.kr` 외 호스트는 경고 로그 |

특정 endpoint가 반복 사용된다면 비상구를 확장하지 말고 정식 dataset으로 등록(`기여자를 위한 새 데이터셋 추가 가이드` 참고)하는 것을 권장합니다.
