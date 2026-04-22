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
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `bakery` | 제과점 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, KSIC I56 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `hospital` | 병원 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, KSIC Q86 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `clinic` | 의원 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, KSIC Q86 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `pharmacy` | 약국 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, KSIC Q86 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `animal_hospital` | 동물병원 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 동물병원 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `optical_shop` | 안경업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, KSIC S96 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `public_bath` | 목욕장업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, KSIC S96 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `laundry` | 세탁업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, KSIC S96 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `barber_shop` | 이용업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, KSIC S96 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `beauty_salon` | 미용업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, KSIC S96 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `pet_grooming` | 동물미용업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, KSIC S96 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `dance_academy` | 무도학원업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, KSIC P85 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `karaoke` | 노래연습장업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, KSIC R90 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `singing_bar` | 단란주점 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, KSIC R90 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `billiard_hall` | 당구장업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, KSIC R90 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `performance_hall` | 공연장업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, KSIC R90 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `movie_theater` | 영화상영관 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, KSIC R91 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `swimming_pool` | 수영장업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, KSIC R93 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `fitness_center` | 체력단련장업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, KSIC R93 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `ice_rink` | 빙상장업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, KSIC R93 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `golf_course` | 골프장업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, KSIC R93 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `golf_practice_range` | 골프연습장업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, KSIC R93 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `horse_riding` | 승마장업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, KSIC R93 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `ski_resort` | 스키장업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, KSIC R93 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `affiliated_medical_institution` | 부속의료기관 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 건강/의료기관 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `postpartum_care` | 산후조리업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 건강/의료기관 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `safe_over_the_counter_drug_store` | 안전상비의약품판매업소 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 건강/의료기관 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `emergency_patient_transport` | 응급환자이송업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 건강/의료기관 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `medical_foundation` | 의료법인 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 건강/의료기관 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `quasi_medical_business` | 의료유사업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 건강/의료기관 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `medical_device_repair` | 의료기기수리업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 건강/의료기기 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `dental_lab` | 치과기공소 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 건강/의료기기 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `medical_device_sales` | 의료기기판매업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 건강/의료기기 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `animal_breeding` | 동물생산업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 동물/동물 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `animal_import` | 동물수입업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 동물/동물 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `animal_care_service` | 동물위탁관리업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 동물/동물 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `animal_transport` | 동물운송업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 동물/동물 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `animal_funeral` | 동물장묘업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 동물/동물 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `animal_exhibition` | 동물전시업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 동물/동물 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `animal_sales` | 동물판매업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 동물/동물 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `animal_crematorium` | 동물화장장업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 동물/동물 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `animal_training` | 동물훈련업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 동물/동물 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `companion_animal_related_business` | 반려동물관련업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 동물/동물 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `livestock_farming` | 가축사육업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 동물/축산 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `livestock_artificial_insemination_center` | 가축인공수정소 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 동물/축산 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `slaughterhouse` | 도축업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 동물/축산 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `hatchery` | 부화업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 동물/축산 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `feed_manufacturing` | 사료제조업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 동물/축산 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `breeding_stock` | 종축업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 동물/축산 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `game_distribution` | 게임물배급업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/게임 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `game_manufacturing` | 게임물제작업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/게임 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `game_provider` | 게임제공업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/게임 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `composite_game_provider` | 복합유통게임제공업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/게임 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `internet_computer_game_facility` | 인터넷컴퓨터게임시설제공업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/게임 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `youth_game_provider` | 청소년게임제공업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/게임 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `electronic_distribution` | 전자유통배급업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/게임 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `tourist_performance_hall` | 관광공연장업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/공연 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `tourist_theater_entertainment` | 관광극장유흥업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/공연 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `tourist_track` | 관광궤도업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/관광 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `tourism_business` | 관광사업자 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/관광 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `tourist_excursion_boat` | 관광유람선업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/관광 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `tourism_convenience_facility` | 관광편의시설업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/관광 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `international_conference_facility` | 국제회의시설업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/관광 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `foreign_tourist_city_homestay` | 외국인관광도시민박업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/관광 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `amusement_facility` | 유원시설업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/관광 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `general_amusement_facility` | 일반유원시설업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/관광 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `comprehensive_amusement_facility` | 종합유원시설업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/관광 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `comprehensive_resort_business` | 종합휴양업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/관광 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `specialized_resort_business` | 전문휴양업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/관광 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `hanok_experience` | 한옥체험업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/관광 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `tourism_duty_free` | 관광면세업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/관광 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `international_conference_planning` | 국제회의기획업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/문화기획 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `popular_culture_arts_planning` | 대중문화예술기획업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/문화기획 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `culture_industry_company` | 문화산업전문회사 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/문화기획 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `video_viewing_room` | 비디오물감상실업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/비디오 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `video_distribution` | 비디오물배급업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/비디오 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `video_small_theater` | 비디오물소극장업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/비디오 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `video_viewing_service` | 비디오물시청제공업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/비디오 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `video_production` | 비디오물제작업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/비디오 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `tourist_accommodation` | 관광숙박업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/숙박 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `tourist_pension` | 관광펜션업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/숙박 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `rural_guesthouse` | 농어촌민박업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/숙박 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `small_hotel` | 소형호텔업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/숙박 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `foreign_tourist_city_homestay_lodging` | 외국인관광도시민박업(숙박) 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/숙박 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `general_lodging` | 일반숙박업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/숙박 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `hanok_experience_lodging` | 한옥체험업(숙박) 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/숙박 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `residential_accommodation` | 생활숙박업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/숙박 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `domestic_travel` | 국내여행업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/여행 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `domestic_international_travel` | 국내외여행업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/여행 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `comprehensive_travel` | 종합여행업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/여행 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `movie_distribution` | 영화배급업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/영화 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `movie_screening` | 영화상영업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/영화 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `movie_import` | 영화수입업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/영화 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `movie_production` | 영화제작업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/영화 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `online_music_service` | 온라인음악서비스제공업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/음악 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `record_distribution` | 음반물배급업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/음악 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `record_production` | 음반물제작업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/음악 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `music_video_distribution` | 음악영상물배급업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/음악 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `music_video_production` | 음악영상물제작업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 문화/음악 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `medical_linen_processing` | 의료기관세탁물처리업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 생활/세탁 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `multilevel_sales` | 다단계판매업체 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 생활/유통 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `large_store` | 대규모점포 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 생활/유통 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `door_to_door_sales` | 방문판매업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 생활/유통 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `prepaid_installment_trade` | 선불식할부거래업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 생활/유통 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `ecommerce` | 전자상거래업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 생활/유통 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `mail_order_sales` | 통신판매업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 생활/유통 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `dance_hall` | 무도장업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 생활/체육 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `yacht_marina` | 요트장업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 생활/체육 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `motor_racing_course` | 자동차경주장업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 생활/체육 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `comprehensive_sports_facility` | 종합체육시설업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 생활/체육 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `martial_arts_gym` | 체육도장업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 생활/체육 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `boxing_gym` | 권투전용체육시설 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 생활/체육 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `contract_foodservice` | 위탁급식영업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/급식 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `group_cafeteria` | 집단급식소 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/급식 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `health_functional_food_retail` | 건강기능식품일반판매업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/제조·가공·판매 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `health_functional_food_specialty` | 건강기능식품전문판매업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/제조·가공·판매 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `health_functional_food_distributor` | 건강기능식품유통전문판매업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/제조·가공·판매 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `food_cold_storage` | 식품냉동냉장업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/제조·가공·판매 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `food_repackaging` | 식품소분업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/제조·가공·판매 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `food_transportation` | 식품운반업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/제조·가공·판매 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `food_vending_machine` | 식품자동판매기영업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/제조·가공·판매 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `food_manufacturing` | 식품제조가공업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/제조·가공·판매 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `food_additive_manufacturing` | 식품첨가물제조업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/제조·가공·판매 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `edible_ice_sales` | 식용얼음판매업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/제조·가공·판매 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `onggi_manufacturing` | 옹기류제조업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/제조·가공·판매 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `distribution_specialized_sales` | 유통전문판매업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/제조·가공·판매 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `instant_food_manufacturing` | 즉석판매제조가공업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/제조·가공·판매 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `milk_collection` | 집유업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/제조·가공·판매 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `livestock_processing` | 축산물가공업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/제조·가공·판매 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `livestock_storage` | 축산물보관업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/제조·가공·판매 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `livestock_transportation` | 축산물운반업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/제조·가공·판매 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `livestock_sales` | 축산물판매업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/제조·가공·판매 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `imported_livestock_sales` | 축산물수입판매업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/제조·가공·판매 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `container_packaging_manufacturing` | 용기포장류제조업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/제조·가공·판매 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `other_food_sales` | 기타식품판매업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/제조·가공·판매 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `imported_food_sales` | 식품등수입판매업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/제조·가공·판매 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `entertainment_bar` | 유흥주점영업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/유흥주점 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `tourist_restaurant` | 관광식당 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/음식점 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `foreigner_exclusive_entertainment_restaurant` | 외국인전용유흥음식점업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/음식점 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `tourist_entertainment_restaurant` | 관광유흥음식점업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 식품/음식점 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `timber_import_distribution` | 목재수입유통업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/목재 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `log_production` | 원목생산업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/목재 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `sawmill` | 제재업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/목재 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `meter_repair` | 계량기수리업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/에너지 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `high_pressure_gas` | 고압가스업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/에너지 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `petroleum_sales` | 석유판매업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/에너지 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `petroleum_import_export` | 석유수출입업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/에너지 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `energy_saving_company` | 에너지절약전문기업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/에너지 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `lpg_charging` | 액화석유가스충전사업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/에너지 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `lpg_collective_supply` | 액화석유가스집단공급사업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/에너지 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `lpg_sales` | 액화석유가스판매사업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/에너지 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `electrical_construction` | 전기공사업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/에너지 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `electrical_safety_management_agency` | 전기안전관리대행사업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/에너지 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `electricity_sales` | 전기판매사업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/에너지 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `city_gas` | 도시가스사업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/에너지 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `gas_appliance_manufacturing` | 가스용품제조사업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/에너지 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `groundwater_construction` | 지하수시공업체 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/지하수 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `groundwater_impact_assessment` | 지하수영향조사기관 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/지하수 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `groundwater_purification` | 지하수정화업체 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/지하수 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `building_sanitation_management` | 건물위생관리업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/환경관리 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `water_tank_cleaning` | 저수조청소업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/환경관리 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `disinfection_business` | 소독업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/환경관리 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `sanitary_product_manufacturing` | 위생용품제조업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/환경관리 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `sanitation_treatment` | 위생처리업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/환경관리 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `waste_treatment` | 폐기물처리업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/환경관리 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `waste_collection_transportation` | 폐기물수집운반업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/환경관리 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `night_soil_collection_transportation` | 분뇨수집운반업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/환경관리 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `environmental_measurement_agency` | 환경측정대행업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/환경관리 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `environmental_impact_assessment` | 환경영향평가업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/환경관리 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `air_pollution_prevention_facility` | 대기오염방지시설업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/환경관리 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `water_pollution_prevention_facility` | 수질오염방지시설업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/환경관리 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `soil_remediation` | 토양정화업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/환경관리 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `noise_vibration_prevention_facility` | 소음진동방지시설업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/환경관리 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `waste_recycling` | 폐기물재활용업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/환경관리 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `medical_waste_treatment` | 의료폐기물처리업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/환경관리 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `marine_environment_management` | 해양환경관리업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/환경관리 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `environmental_consulting` | 환경컨설팅업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 자원환경/환경관리 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `outdoor_advertising` | 옥외광고업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 기타/미디어 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `printing_house` | 인쇄사 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 기타/미디어 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `publisher` | 출판사 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 기타/미디어 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `tobacco_wholesale` | 담배도매업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 기타/담배 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `tobacco_retail` | 담배소매업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 기타/담배 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `tobacco_import_sales` | 담배수입판매업체 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 기타/담배 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `international_freight_forwarding` | 국제물류주선업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 기타/물류 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `logistics_warehouse` | 물류창고업체 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 기타/물류 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `civil_defense_water_supply` | 민방위급수시설 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 기타/민방위 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `funeral_service` | 상조업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 기타/상조 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `elevator_maintenance` | 승강기유지관리업체 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 기타/엘리베이터 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `elevator_manufacturing_import` | 승강기제조및수입업체 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 기타/엘리베이터 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `caregiver_training_institution` | 요양보호사교육기관 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 기타/전문교육기관 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `funeral_director_training_institution` | 장례지도사교육기관 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 기타/전문교육기관 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `free_job_placement` | 무료직업소개소 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 기타/사무지원 |
| 지원 | 테스트 검증 | - | 지방행정인허가 (`localdata`) | `paid_job_placement` | 유료직업소개소 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, 기타/사무지원 | 스키장업 인허가 | [공공데이터포털](https://www.data.go.kr) 서비스키 | [data.go.kr](https://www.data.go.kr) | 행정안전부 제공, KSIC R93 |
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
