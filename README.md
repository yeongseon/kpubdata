# KPubData

> Korean public data access framework for Python 3.10+
>
> A dialect-inspired, dataset-oriented framework that gives Python users a consistent way to discover and query Korean public-data services without pretending every provider works the same way.

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

## Example usage

```python
from kpubdata import Client

client = Client.from_env()

result = client.dataset("molit.apartment_trades").list(
    lawd_code="11680",
    deal_ym="202503",
)

for item in result.items:
    print(item)

print(result.raw)
```

## Example with discovery

```python
from kpubdata import Client

client = Client.from_env()

for ds in client.datasets.search("지하철"):
    print(ds.id, ds.name, ds.capabilities)
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
- `pyproject.toml` — initial packaging skeleton

## Initial delivery target

### v0.1

- Python 3.10+
- sync-only core
- canonical query/result/error/capability model
- provider adapters for 3 distinct service families
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

