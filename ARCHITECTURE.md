# Architecture — KPubData

## 1. Architectural style

KPubData uses a **dialect-inspired layered architecture**.

It borrows the philosophy of systems like SQLAlchemy:

- keep a small and stable core
- isolate backend-specific behavior in adapters/dialects
- offer a uniform developer-facing entry point
- preserve an escape hatch to lower-level behavior

It does **not** try to recreate SQL itself or a universal query language.

## 2. Core idea

```text
Client
  -> Catalog / discovery
  -> Dataset binding
  -> ProviderAdapter
  -> Transport
  -> Parse / normalize
  -> Canonical result
```

## 3. Layers

### 3.1 Core layer

Stable contracts shared across the whole framework.

Contains:

- `DatasetRef`
- `Representation`
- `Capability`
- `Query`
- `RecordBatch`
- `SchemaDescriptor`
- `PublicDataError` hierarchy

Design rule:

- the core changes slowly
- no provider-specific hacks unless repeated across multiple adapters

### 3.2 Catalog layer

Responsible for discovering and resolving datasets.

Responsibilities:

- listing/searching descriptors
- provider-aware lookup
- binding descriptors into dataset objects

### 3.3 Provider adapter layer

Each provider family implements an adapter that understands its own conventions.

Responsibilities:

- auth injection
- request building
- parameter transformation
- response parsing
- provider-specific error interpretation
- capability declaration
- raw-call support

### 3.4 Transport layer

Shared HTTP and parsing infrastructure.

Responsibilities:

- session management
- timeouts
- retries
- content-type detection
- common XML/JSON helpers

### 3.5 Public API layer

The developer-facing surface.

Responsibilities:

- ergonomic `Client`
- dataset-oriented operations
- convenience aliases where helpful

### 3.6 Optional adapters layer

Not part of the core runtime contract.

Examples:

- pandas export
- MCP adapter
- plugin loaders

## 4. Main abstractions

### 4.1 Client

Top-level entry point.

Responsibilities:

- initialization/config
- provider registry access
- catalog access
- dataset binding

### 4.2 Dataset

A provider-aware bound object representing a queryable service/dataset.

Responsibilities:

- expose operations (`list`, `get`, `schema`, `call_raw`)
- surface capabilities
- preserve provider identity

### 4.3 ProviderAdapter

The extension point.

Responsibilities:

- compile canonical intent into provider-native requests
- parse provider-native responses into canonical results
- define supported capabilities

## 5. Why dataset-oriented instead of agency-oriented

End users usually want data like “subway arrivals” or “apartment trades,” not “the Ministry X API client.”

The public API should therefore prioritize datasets/services as the first-class mental model while still retaining provider identity for auth, debugging, and routing.

## 6. Why capabilities matter

Different datasets genuinely support different operations.

Examples:

- list only
- list + pagination
- single record lookup
- schema metadata
- raw download
- real-time feed semantics

A capability model prevents the framework from lying.

## 7. Why raw access is mandatory

Public-data APIs often:

- return errors in 200 bodies
- drift from docs
- mix XML and JSON expectations
- omit metadata in normalized forms

Therefore, every adapter must provide a raw escape hatch.

## 8. Recommended package structure

```text
src/kpubdata/
  client.py
  config.py
  catalog.py
  exceptions.py
  registry.py
  core/
    capability.py
    dataset.py
    query.py
    result.py
    schema.py
    representation.py
  transport/
    http.py
    auth.py
    parse.py
    retry.py
  providers/
    datago/
      adapter.py
      discovery.py
      mappings.py
    seoul/
      adapter.py
      discovery.py
      mappings.py
    airkorea/
      adapter.py
      discovery.py
      mappings.py
  adapters/
    pandas.py
    mcp.py
```

## 9. Execution flow

### 9.1 Discovery flow

```text
Client.datasets.search("지하철")
  -> Catalog.search()
  -> ProviderAdapter.search_datasets() or static registry metadata
  -> DatasetRef[]
```

### 9.2 Query flow

```text
client.dataset("molit.apartment_trades").list(...)
  -> Dataset.list(...)
  -> build Query
  -> ProviderAdapter.query_records(dataset_ref, query)
  -> Transport request
  -> parse / normalize
  -> RecordBatch
```

### 9.3 Raw flow

```text
dataset.call_raw(operation="list", params={...})
  -> ProviderAdapter.call_raw(...)
  -> raw payload / raw response object
```

## 10. Rules for core evolution

Promote something into the core only when at least one of these is true:

1. three or more adapters need it
2. it materially simplifies the public API
3. it improves correctness across providers

Do **not** change the core just because one adapter is weird.

## 11. Design constraints

- avoid deep inheritance trees
- prefer composition and small protocols
- keep canonical models minimal
- keep provider-specific richness in metadata and raw channels
- treat representation (`openapi`, `file`, `sheet`, `download`) as real metadata, not a footnote

