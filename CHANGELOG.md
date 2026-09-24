# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- localdata 가 `resultCode "03"`(NODATA)을 예외로 올리던 것을 semas 와 같이 빈 결과로 처리 (#470). 필터를 걸어 조회했는데 결과가 없는 흔한 경우가 한쪽 provider 에서만 오류였다.
- localdata/semas 의 `_normalize_items` 가 빈 래퍼(`{"items": {}}`)와 XML `<items><item/></items>` 를 1건으로 승격하던 **유령 행** 제거 (#482 회귀). datago 본가 동작에 맞춘다.
- localdata 의 `base_url` 끝 슬래시 미처리로 `//` 가 생기던 것 수정 (#470).
- `datago.g2b_catalog` 의 필수 파라미터 `inqryDiv` 자동 전송 (#414). 사용자 필터가 우선하며 키 대소문자를 구분하지 않는다.
- HTTP 전송 계층 로그/예외 메시지에서 API 키가 포함된 query parameter가 `[REDACTED]`로 마스킹되도록 수정 (#260)
- Canonical Query validation now prevents invalid canonical query values from reaching provider adapters (#264)
- `Dataset.list()` now validates canonical query parameters (`page`, `page_size`, `cursor`, `start_date`, `end_date`, `fields`, `sort`) before adapter invocation
- Canonical keys are now routed by name (not by type) to prevent bypass via type mismatch (e.g., `dataset.list(page="1")` now raises `InvalidRequestError` instead of falling through to filters)
- Date fields now reject empty strings and whitespace-only values
- All query validation errors now raise `InvalidRequestError` instead of generic `TypeError`/`ValueError`
- bok 어댑터가 URL 경로에 실은 API 키를 `secret_values` 로 전달해 로그·예외에서 마스킹 (#475). law 의 `OC` 파라미터를 마스킹 목록에 추가.
- spec 로더가 `_parse_date`/`_parse_params`/`_parse_license` 의 검증 오류를 버리던 것 수정 (#476). `last_verified: "2026-13-45"` 가 조용히 `None` 이 되지 않는다. **동작 변경**: 잘못된 `license` 필드가 이제 spec 로드를 실패시킨다.
- `Retry-After` 힌트에 상한을 둔다 — `TransportConfig.max_retry_delay`(기본 60s) (#477). 상한을 넘으면 기다리지 않고 retryable `RateLimitError` 로 즉시 반환한다.
- data.go.kr 게이트웨이 거부(`OpenAPI_ServiceResponse/cmmMsgHeader`)를 "Malformed response envelope" 가 아니라 원인대로 보고 (#478, datago 어댑터 경로).
- spec 우선 실행 경로(`core/executor.py`)도 게이트웨이 거부를 인식한다. #478 은 datago 어댑터만 고쳐서, spec 을 타는 20여 종은 여전히 "응답 envelope에서 에러 코드를 찾을 수 없습니다" 로 실패했다.
- sgis 의 `accessToken`/`consumer_key`/`consumer_secret` 을 마스킹 목록에 추가. 목록이 부분 문자열이 아니라 정확한 이름을 보므로 `consumer_key` 는 `key` 를 포함해도 걸리지 않았다.
- 종단 HTTP 상태 오류에 `status_code` 를 실어 보낸다. URL 마스킹 시 예외 체인을 끊기 때문에 원래 응답이 함께 사라져, 호출자가 401 과 503 을 메시지 문자열로만 구분할 수 있었다. 재시도를 소진한 429 는 `RateLimitError` 로 올린다.
- 응답 캐시를 임시 파일 + `os.replace` 로 원자적으로 쓴다. 중간에 끊긴 파일이 완성된 엔트리로 읽혀 TTL 만료까지 깨진 값이 반복됐다.

### Removed

- 저장소에 커밋돼 있던 `.omx/` 에이전트 도구 로그·상태 파일 10개 삭제, `.gitignore` 에 추가.

### Added

- spec 기반 데이터셋 18종 → 23종.
- datago 카탈로그 메타데이터 보강 (#376): `request_parameters`, `application`, ASOS 계열 `fixed_query_params`, HTTPS endpoint. `required_query_filters` 와 `request_parameters` 의 필수 표시가 어긋나지 않도록 테스트로 고정.

### Changed

- Query validation now performs type checking and basic value validation at Query creation time
- Empty cursor strings (`""`) are now rejected as invalid

## [0.6.0] — 2026-09-09

### 제거 (Breaking)
- **폐기 서비스 데이터셋 141종 제거** (#412): localdata 136종, datago 5종(building_area·building_floor·building_recap_title·building_title·metro_path).
  2026-09-09 본문 전수 프로브(`tests/fixtures/batch-reclass.json`)로 NO_OPENAPI_SERVICE 확정.
  해당 catalogue 항목·fixture·테스트를 함께 제거했다. 활용신청 필요 94종은 유지(#409).

### 추가
- spec 기반 데이터셋 18종(골든 3 + air_station + ultra_srt_fcst + air_quality + ultra_srt_ncst + 부동산 6 + localdata 3 + airkorea_forecast + metro_fare) — `make verify` 4단계 기계 검증.
- 대량 전환 도구: `gen_specs_from_catalogue.py`·`batch_record.py`·`gen_example_scripts.py`.


## [0.5.0] - 2026-04-28

### Added
- `krx` provider — 한국거래소 시세 어댑터 (선택적 `pykrx` 백엔드, authless 구성). 새로운 `requires_api_key` 프로토콜 플래그와 `Client.iter_authenticated_providers()` 도입 (#199)
- `krx.kospi_index` — 코스피 지수 일별 시세 (#200)
- `krx.investor_flow` — 투자자별 순매수 추이 (`net_value = buy_value - sell_value`) (#200)
- `krx.market_valuation` — 시장 밸류에이션 지표 (per-day `get_market_fundamental_by_ticker` 집계) (#200)
- `bok.usd_krw` — 원/달러 환율 ECOS 일별 시세 (731Y003/0000003) (#197)
- `bok.bond_yield_3y` — 국고채 3년 ECOS 일별 시세 (817Y002/010200000) (#198)
- `kosis.industrial_production` — 광공업생산지수 (DT_1J22003) (#196)
- KOSIS 어댑터의 dataset-level `default_query_params` 지원 (objL1-objL8/itmId/prdSe/newEstPrdCnt/prdInterval allowlist; caller filters override defaults) (#196)
- `pandas-stubs` dev 의존성 추가로 `core/models.py`의 `# type: ignore` 제거
- ODcloud `provider_family` 프로토콜 지원: `api.odcloud.kr` 기반 엔드포인트를 위한 별도 페이지네이션(`page`/`perPage`) 및 응답 파싱(`data[]` 플랫 배열) 처리
- k-eco-navigator 연동용 3개 데이터셋 추가:
  - `datago.g2b_contract` — 나라장터 조달계약정보 (`apis.data.go.kr/1230000/ao/CntrctInfoService`)
  - `datago.social_enterprise` — 사회적기업 인증현황 (`api.odcloud.kr/api/socialEnterpriseList/v1`, ODcloud 프로토콜)
  - `datago.g2b_catalog` — 나라장터 종합쇼핑몰 품목정보 (`apis.data.go.kr/1230000/at/ShoppingMallPrdctInfoService`)

### Changed
- `social_enterprise` 데이터셋은 `apis.data.go.kr`이 아닌 `api.odcloud.kr` 엔드포인트 사용 (ODcloud 프로토콜)

### Removed
- `datago.coop` (협동조합 설립현황) 데이터셋 삭제 — 전국 단위 API 미존재 확인

## [0.3.1] - 2026-04-23

### Fixed
- Source `__version__` from `importlib.metadata` instead of hardcoded string (#127)
- Add 활용신청 (activation request) hint to datago 403 `AuthError` and document API key activation requirement (#128)
- Add required parameters to metro integration tests (#140)

## [0.3.0] - 2026-04-22

### Added
- `localdata` provider: expand permit datasets from 26 to **195**, covering all official KSIC categories — health (13), animal (18), culture (53), living (26), food (32), resources & environment (37), other (16)
- `sgis` provider adapter for administrative boundary GeoJSON datasets:
  - `sgis.boundary.sido`
  - `sgis.boundary.sigungu`
  - `sgis.boundary.emd`
- SGIS access-token authentication flow (`consumer_key` + `consumer_secret`) with in-memory token cache and refresh-on-auth-failure behavior
- Unit and contract tests plus SGIS fixture responses for boundary and auth/error scenarios
- Full fixture, unit test, and contract test coverage for all 195 localdata datasets

## [0.2.3] - 2026-04-19

### Fixed
- `LofinAdapter` SSL context ignored when `Client` passes shared transport

### Added
- 7 real estate transaction datasets to datago provider (`apt_rent`, `offi_trade`, `offi_rent`, `rh_trade`, `rh_rent`, `sh_trade`, `sh_rent`)
- Treat `resultCode` `'000'` as success for RTMS endpoints

## [0.2.2] - 2026-04-17

### Added
- Cursor pagination support and pagination documentation

## [0.2.1] - 2026-04-17

### Added
- `SUPPORTED_DATA.md` 실API 최종 검증일 컬럼 추가
- Single-page pagination contract and `list_all()` implementation

## [0.2.0] - 2026-04-17

### Added
- Single-page pagination contract for all adapters (datago, bok, lofin, kosis)
- `Dataset.list_all()` generator for automatic multi-page iteration
- `RecordBatch.to_pandas()` for pandas DataFrame conversion (optional `pandas` dependency)
- Unit tests for BOK and LOFIN adapters

### Changed
- Default `page_size` increased from 10 to 100
- **Breaking**: `query_records()` now returns a single page instead of auto-draining all pages

### Removed
- Unreachable single-record adapter stubs
- Single-record access from the provider and dataset public APIs

## [0.1.0] - 2026-04-10

### Added

- Core framework: `Client`, `Dataset`, `Catalog`, `Query`, `RecordBatch` public API
- Canonical error hierarchy with structured context (`PublicDataError` and subclasses)
- `DataGoAdapter` for data.go.kr with 6 curated datasets:
  - `datago.village_fcst` — KMA short-range forecast
  - `datago.ultra_srt_ncst` — KMA ultra short-term nowcast
  - `datago.air_quality` — real-time air quality (PM2.5/PM10)
  - `datago.bus_arrival` — Gyeonggi-do bus arrival info
  - `datago.hospital_info` — hospital/medical institution lookup
  - `datago.apt_trade` — MOLIT apartment trade price
- `BokAdapter` for ecos.bok.or.kr (Bank of Korea):
  - `bok.base_rate` — BOK base interest rate historical data
- `KosisAdapter` for kosis.kr (KOSTAT):
  - `kosis.population_migration` — inter-regional population migration statistics
- Environment-based configuration for all providers (`KPUBDATA_BOK_API_KEY`, `KPUBDATA_KOSIS_API_KEY`)
- Dataset discovery via `client.datasets.list()` and `client.datasets.search()`
- Record querying via `client.dataset("datago.village_fcst").list(**params)`
- Raw API escape hatch via `dataset.call_raw(operation, **params)`
- Schema metadata via `dataset.schema()` (catalogue-backed)
- XML and JSON response decoding with automatic content-type detection
- HTTP transport with configurable retry and exponential backoff
- Rate-limit aware retry with `Retry-After` header support (delta-seconds and HTTP-date)
- DEBUG-level request/response logging with credential redaction (`_sanitize_params`)
- Environment-based configuration (`KPUBDATA_DATAGO_API_KEY`)
- Provider adapter protocol with registration-time validation
- Contract test framework for adapter conformance
- GitHub Actions CI (lint, type check, test on Python 3.10–3.13, build)
- 90%+ unit test coverage for core framework modules (291 tests)
- PEP 257 docstrings for full public API surface
- MIT LICENSE
