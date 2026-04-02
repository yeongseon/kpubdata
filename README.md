# KPubData

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI](https://github.com/yeongseon/kpubdata/actions/workflows/ci.yml/badge.svg)](https://github.com/yeongseon/kpubdata/actions/workflows/ci.yml)

A dialect-inspired, dataset-oriented framework that gives Python users a consistent
way to discover and query Korean public-data services without pretending every
provider works the same way.

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

KPubData is a **Python data access framework** for Korean public data.

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

## Document map

- `VALIDATION.md` — why the architecture is valid
- `PRD.md` — product requirements
- `ARCHITECTURE.md` — system architecture
- `CANONICAL_MODEL.md` — core data model
- `API_SPEC.md` — public Python API proposal
- `PROVIDER_ADAPTER_CONTRACT.md` — adapter contract and authoring rules
- `PACKAGING.md` — packaging and release strategy
- `AGENTS.md` — repo rules for agentic/Codex development
- `ROADMAP.md` — staged delivery plan

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
