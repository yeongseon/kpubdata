# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
