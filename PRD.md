# PRD — KPubData

## 1. Document information

- Product name: `KPubData`
- Product type: Python data access framework / SDK
- Target runtime: Python 3.10+
- Primary users: Python developers, backend developers, data engineers, agent/MCP developers
- Product stage: architecture and bootstrap

## 2. Problem statement

Korean public-data APIs are difficult to use consistently because they vary by provider and service family in:

- authentication conventions
- parameter naming and validation
- response envelopes and error signaling
- representation format (JSON, XML, file, sheet, mixed)
- pagination semantics
- schema stability and metadata quality

As a result, developers repeatedly rebuild the same glue code:

- auth/key injection
- request construction
- XML/JSON parsing
- result normalization
- provider-specific error handling
- schema probing
- debugging around raw payloads

## 3. Product vision

KPubData will provide a **Pythonic, dataset-oriented, provider-aware** framework for accessing Korean public-data services through a small canonical core, while preserving the ability to drop down to provider-specific/raw behavior when needed.

## 4. Product definition

KPubData is **not** a single fake standard API.
It is a **dialect-inspired integration layer**:

- a stable core defines canonical contracts
- adapters absorb provider differences
- users interact through a consistent dataset-oriented Python API

## 5. Target users

### 5.1 Application developers

Need to integrate Korean public data into product features without learning every provider from scratch.

### 5.2 Data engineers / analysts

Need repeatable access, metadata visibility, and raw/debug paths for pipelines.

### 5.3 Agent / MCP developers

Need a stable core library so that the future MCP layer can remain thin.

### 5.4 Contributors

Need a predictable adapter contract and a clear definition of done when adding a provider.

## 6. Jobs to be done

1. Discover datasets/services without manually browsing each portal.
2. Query datasets through a consistent Python entry point.
3. Know which operations each dataset supports.
4. Access raw payloads when normalization is insufficient.
5. Add a new provider adapter without changing the whole framework.

## 7. Product principles

1. **Dataset-oriented, provider-aware**
2. **Small stable core, provider complexity pushed outward**
3. **Capability-first honesty**
4. **Canonical + raw together**
5. **Modern Python packaging and typing discipline**
6. **Agentic-development friendly repository structure**

## 8. Goals

### 8.1 Product goals

- provide a canonical query/result/error/capability model
- support multiple heterogeneous provider families under one public interface
- preserve provider identity and raw access
- keep the public API small and learnable
- make adapter authoring systematic

### 8.2 Success criteria for the first meaningful release

- three materially different provider/service families integrated
- each provider passes contract tests for its declared capabilities
- first successful query possible within 10 minutes for a developer with keys
- public API docs cover common discovery and query workflows
- raw access remains available in every provider adapter

## 9. Non-goals for v0.1

- complete coverage of all Korean public-data APIs
- universal query language across all providers
- async support
- built-in scheduling/caching/warehouse loading
- full MCP server in the initial release
- full field-level semantic standardization across every provider

## 10. Functional requirements

### FR-1. Client initialization

The framework must support explicit config and environment-based config.

Acceptance:

- `Client(...)`
- `Client.from_env()`
- provider key lookup order documented

### FR-2. Provider registry

The framework must register and retrieve provider adapters by identifier.

Acceptance:

- duplicate registration blocked
- lazy loading allowed
- adapter metadata available

### FR-3. Dataset discovery

Users must be able to list and search dataset descriptors.

Acceptance:

- `client.datasets.list()`
- `client.datasets.search(text)`
- each descriptor exposes `id`, `provider`, `name`, `representation`, `capabilities`

### FR-4. Dataset binding

Users must be able to bind a dataset reference into an object with operations.

Acceptance:

- `client.dataset("provider.dataset")`
- unknown dataset raises a clear exception

### FR-5. Record listing/query

A list/query operation must return a canonical result envelope.

Acceptance:

- `dataset.list(...)`
- returns `RecordBatch`
- includes `items`
- includes `raw`
- includes metadata about pagination and provider

### FR-6. Single-record access

Supported datasets may expose a single-record get operation.

Acceptance:

- `dataset.get(...)`
- unsupported datasets raise `UnsupportedCapabilityError`

### FR-7. Schema/metadata access

Datasets may expose schema or field metadata.

Acceptance:

- `dataset.schema()`
- returns `SchemaDescriptor | None`

### FR-8. Raw access

Every provider adapter must expose a raw-call path.

Acceptance:

- `dataset.call_raw(...)` or provider raw call equivalent
- raw payload preserved without normalization loss

### FR-9. Error normalization

Provider-specific failures must map to canonical error types.

Acceptance:

- transport, auth, parse, unsupported capability, and provider-response failures mapped explicitly
- original status/message retained in exception metadata

### FR-10. Representation handling

The framework must support multiple content and representation types through adapters.

Acceptance:

- XML and JSON in core scope
- representation metadata attached to dataset descriptors
- file/sheet/download capability represented even if not normalized in v0.1

## 11. Non-functional requirements

### NFR-1. Python quality bar

- Python 3.10+
- type hints throughout public API
- `pyproject.toml` packaging
- `src/` layout

### NFR-2. Quality gates

- lint
- format
- typecheck
- unit tests
- contract tests

### NFR-3. Public API stability

- public contracts documented
- breaking changes require changelog and versioning discipline

### NFR-4. Observability and debugging

- raw response access
- structured exception metadata
- optional logging hooks

## 12. UX requirements

The API must read like Python, not like a copied portal endpoint name.

Preferred style:

```python
client.dataset("molit.apartment_trades").list(lawd_code="11680", deal_ym="202503")
```

Avoid as the primary public surface:

```python
client.getRTMSDataSvcAptTradeDev(...)
```

## 13. Release plan

### v0.1

- core contracts
- sync transport
- 3 adapters
- XML/JSON
- raw access
- tests/docs/release skeleton

### v0.2

- richer discovery metadata
- plugin loading
- pandas adapter
- broader provider coverage

### v0.3

- thin MCP adapter
- provider scaffolding tools
- improved docs/examples

## 14. Risks

1. Over-abstracting into a fake universal API
2. Letting one provider's quirks contaminate the core model
3. Under-investing in raw/debug paths
4. Treating dataset metadata as optional rather than foundational
5. Allowing the public API surface to grow too fast

## 15. Mitigations

- keep the canonical core intentionally small
- add capabilities instead of pretending support exists
- enforce adapter contract tests
- keep raw access mandatory
- require architecture documentation for public-surface changes

---

## 📚 관련 문서

### 이 저장소 내 문서
| 문서 | 설명 |
| :--- | :--- |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 시스템 아키텍처 설계 |
| [ROADMAP.md](./ROADMAP.md) | 프로젝트 로드맵 및 단계별 계획 |
| [API_SPEC.md](./API_SPEC.md) | 파이썬 API 명세 |

### KPubData Product Family
| 저장소 | 문서 | 설명 |
| :--- | :--- | :--- |
| [kpubdata-builder](https://github.com/yeongseon/kpubdata-builder) | [PRD.md](https://github.com/yeongseon/kpubdata-builder/blob/master/PRD.md) | Builder 제품 요구사항 |
| [kpubdata-studio](https://github.com/yeongseon/kpubdata-studio) | [PRD.md](https://github.com/yeongseon/kpubdata-studio/blob/main/PRD.md) | Studio 제품 요구사항 |


