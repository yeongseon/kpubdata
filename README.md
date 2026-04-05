# KPubData — Korea Public Data

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI](https://github.com/yeongseon/kpubdata/actions/workflows/ci.yml/badge.svg)](https://github.com/yeongseon/kpubdata/actions/workflows/ci.yml)

**KPubData (Korea Public Data)** is a dialect-inspired, dataset-oriented Python framework
that gives users a consistent way to discover and query Korean public-data services
without pretending every provider works the same way.

## Installation

```bash
pip install kpubdata
```

## Quickstart

### 1. Configure your API key

Get a free API key from [data.go.kr](https://www.data.go.kr), then either pass it
directly or set an environment variable:

```bash
export KPUBDATA_DATAGO_API_KEY="your-service-key"
```

### 2. Create a client

```python
from kpubdata import Client

# From environment variables
client = Client.from_env()

# Or pass keys explicitly
client = Client(provider_keys={"datago": "YOUR_API_KEY"})
```

### 3. Discover datasets

```python
# List all available datasets
for ds in client.datasets.list():
    print(ds.id, ds.name)

# Search by keyword
for ds in client.datasets.search("forecast"):
    print(ds.id, ds.name, ds.operations)
```

### 4. Query records

```python
ds = client.dataset("datago.village_fcst")

result = ds.list(
    base_date="20250401",
    base_time="0500",
    nx="55",
    ny="127",
)

for item in result.items:
    print(item)
```

### 5. Raw API escape hatch

When the normalized layer doesn't cover what you need, drop down to the raw API:

```python
ds = client.dataset("datago.air_quality")

raw = ds.call_raw(
    "getCtprvnRltmMesureDnsty",
    sidoName="서울",
    numOfRows="5",
)
print(raw)
```

### Available datasets (v0.1)

| Dataset ID | Name | Description |
|---|---|---|
| `datago.village_fcst` | 동네예보 조회서비스 | KMA short-range forecast |
| `datago.ultra_srt_ncst` | 초단기실황 조회서비스 | KMA ultra short-term nowcast |
| `datago.air_quality` | 대기오염정보 조회서비스 | Real-time air quality (PM2.5, PM10) |
| `datago.bus_arrival` | 경기도 버스도착정보 조회서비스 | Gyeonggi-do bus arrival info |
| `datago.hospital_info` | 병원정보서비스 | Hospital / medical institution lookup |

## Project definition

KPubData (Korea Public Data) is a **Python data access framework** for Korean public data.

It is **not** a fake universal API that forces every provider into the same parameter model.
Instead, it provides:

- a small canonical core (`Query`, `RecordBatch`, `Capability`, `PublicDataError`)
- a dataset-oriented public surface (`client.dataset(...).list(...)`)
- provider-specific adapters that absorb structural differences
- an explicit raw escape hatch for anything the normalized layer cannot or should not hide

## Why this project exists

Korean public-data APIs differ along multiple axes:

- provider-specific auth and key injection
- REST-ish but inconsistent parameter naming
- XML, JSON, CSV, sheet, file-download, and mixed representations
- different pagination styles (`pageNo`, `numOfRows`, row ranges, cursors, none)
- different error conventions (HTTP status vs. payload code vs. message-only failures)
- weak or drifting schema guarantees

A good Python library should not force users to re-learn each provider from scratch, but it also should not lie about what is supported.

## What is standardized

KPubData standardizes **entry points and result envelopes**, not every provider's native shape.

### Standardized

- client construction
- dataset discovery
- operation entry points (`list`, `get`, `schema`, `call_raw`)
- capability declaration
- canonical result envelope
- canonical error hierarchy

### Not forcibly standardized

- every parameter name
- every filtering capability
- every pagination rule
- every schema
- every provider-specific operation

## Core design principles

1. **Dataset-oriented, provider-aware**
   - Users primarily think in datasets/services, not agencies.
   - The system still keeps provider identity explicit.

2. **Dialect-inspired architecture**
   - The core stays small and stable.
   - Provider adapters absorb auth, parameter, pagination, parse, and error differences.

3. **Capability-first honesty**
   - Supported operations are declared.
   - Unsupported operations fail explicitly.

4. **Pythonic public API**
   - Public APIs should feel natural to Python users.
   - Use snake_case, explicit objects, and readable method names.

5. **Canonical + raw together**
   - Normalized access is the default.
   - Raw access is always available.

## Mental model

```text
Client
  -> Catalog / dataset lookup
  -> ProviderAdapter
  -> Transport
  -> Parse / normalize
  -> RecordBatch or Record
```

## 📖 문서 가이드 (Document Guide)

KPubData의 설계 철학과 사용 방법을 안내하는 문서 목록입니다.

### 핵심 설계
- [ARCHITECTURE.md](./ARCHITECTURE.md): 시스템 전체 구조와 구성 요소 간의 상호작용 설계
- [CANONICAL_MODEL.md](./CANONICAL_MODEL.md): 다양한 API 응답을 하나로 통합하는 표준 데이터 모델 정의
- [PROVIDER_ADAPTER_CONTRACT.md](./PROVIDER_ADAPTER_CONTRACT.md): 새로운 데이터 제공 기관(Provider) 추가를 위한 어댑터 구현 규약

### API & 검증
- [API_SPEC.md](./API_SPEC.md): 사용자가 직접 사용하는 파이썬 API 명세 및 사용법
- [VALIDATION.md](./VALIDATION.md): 아키텍처 설계의 타당성 검증 및 핵심 결정 사항

### 개발 가이드
- [AGENTS.md](./AGENTS.md): AI 에이전트와 함께 개발할 때 준수해야 할 규칙 및 가이드
- [CONTRIBUTING.md](./CONTRIBUTING.md): 프로젝트 기여 방법 및 개발 환경 설정 안내
- [PACKAGING.md](./PACKAGING.md): 패키징 구조 및 배포 전략

### 프로젝트 관리
- [PRD.md](./PRD.md): 제품 요구사항 정의 및 핵심 가치
- [ROADMAP.md](./ROADMAP.md): 단계별 기능 구현 및 출시 계획

### 상세 참고 자료
- [architecture-diagrams.md](./docs/architecture-diagrams.md): 아키텍처 시각화 다이어그램
- [datago-api-reference.md](./docs/datago-api-reference.md): 공공데이터포털(data.go.kr) API 연동 참고 자료
- [ADRs](./docs/adrs/): 주요 기술적 결정 이력 (Architecture Decision Records)

---

## 📚 관련 문서

### KPubData Product Family
| 저장소 | 문서 | 설명 |
| :--- | :--- | :--- |
| [kpubdata-builder](https://github.com/yeongseon/kpubdata-builder) | [ARCHITECTURE.md](https://github.com/yeongseon/kpubdata-builder/blob/main/ARCHITECTURE.md) | Builder 아키텍처 |
| [kpubdata-studio](https://github.com/yeongseon/kpubdata-studio) | [ARCHITECTURE.md](https://github.com/yeongseon/kpubdata-studio/blob/main/ARCHITECTURE.md) | Studio 아키텍처 |

## Initial delivery target

### v0.1

- sync-only core
- canonical query/result/error/capability model
- provider adapter for data.go.kr (5 datasets)
- XML + JSON support
- raw access path
- pytest + type checking + lint gate

### v0.2

- dataset metadata enrichment
- provider plugin registration
- pandas adapter
- more providers (e.g. KOSIS/ECOS)

### v0.3

- thin MCP adapter on top of the stable core
