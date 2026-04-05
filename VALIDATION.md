# Validation of the architecture

## Conclusion

The current direction is valid **with one refinement**:

- keep the product **dataset-oriented rather than agency-oriented**
- but model the real world as **provider + dataset/service + representation + operation**

That refinement matters because Korean public-data portals expose metadata not only by provider, but also by dataset/service and form of provision (OpenAPI, file, sheet, etc.).

## What was validated

### 1. A dialect-inspired architecture is a good fit

SQLAlchemy documents that the `Engine` works with a `Dialect` and a `Pool`, and that dialect implementations cover DBAPI specifics. The SQLAlchemy internals docs also state that anything that varies between databases falls under the dialect concept. That makes the analogy useful: KPubData should keep a small core and push backend-specific behavior into provider adapters.

Why this transfers well:

- public-data providers vary in auth, parameter naming, transport conventions, response format, and result semantics
- the framework should unify access patterns without pretending every backend is semantically identical

### 2. Dataset/service orientation is more accurate than pure agency orientation

The Public Data Portal exposes open-data items with metadata such as provider, public-data name/description, category, and data type. The portal also classifies services by service type (for example REST, SOAP, download, LOD, etc.). Seoul Open Data similarly exposes dataset/service metadata and explicitly shows one service with both Sheet and Open API representations.

Therefore, the main abstraction should not just be “agency client”. It should be closer to:

- provider: who owns or serves it
- dataset/service: what the user wants
- representation: how it is exposed
- operation: what can be done with it

### 3. Standardizing UX is better than standardizing every native API shape

The right goal is **consistent Python entry points**, not a fake universal parameter schema.

That means these should be standardized:

- `client.dataset(id)`
- `dataset.list(...)`
- `dataset.get(...)`
- `dataset.schema()`
- `dataset.call_raw(...)`

But provider-specific parameters can still exist. Forcing every API into one perfect universal filter language would likely produce a leaky and misleading abstraction.

### 4. Raw escape hatches are necessary

Requests explicitly documents `Response.raw` for cases where raw bytes are needed, and reminds users that decoded content is not the same thing as the original transport payload. This supports keeping raw access in KPubData as a first-class feature.

For public-data APIs, raw access is even more important because:

- documentation often drifts from reality
- providers sometimes signal failure inside a 200 response body
- XML/JSON differences can matter during debugging

### 5. Capability-based design is the right honesty mechanism

Not every dataset supports the same operations. Some are queryable lists, some are single-record lookups, some only expose file downloads, and some publish metadata rather than domain records.

A capability model is the cleanest way to make those differences explicit without fragmenting the public API.

## Final validated definition

> KPubData is a provider-aware, dataset/service-oriented, capability-driven Python data access framework for Korean public data. It uses a small canonical query/result model, exposes Pythonic convenience APIs, and always preserves a raw escape hatch.

## Design decisions that remain valid

- dataset-oriented public API: **yes**
- small canonical `Query` and `RecordBatch`: **yes**
- capability-based support matrix: **yes**
- raw access path: **yes**
- SQLAlchemy-inspired philosophy: **yes**
- pretending every provider shares one true standard API: **no**

## Reference notes

The validation above was checked against official documentation from:

- SQLAlchemy docs on `Engine`, `Core`, and `Dialect`
- the Korean Public Data Portal metadata and service type pages
- Seoul Open Data dataset metadata
- Requests documentation on raw response handling


### Official references

- SQLAlchemy overview and dialect docs: https://docs.sqlalchemy.org/en/20/intro.html
- SQLAlchemy engine configuration: https://docs.sqlalchemy.org/en/latest/core/engines.html
- SQLAlchemy core internals / dialect: https://docs.sqlalchemy.org/en/latest/core/internals.html
- Public Data Portal list API metadata example: https://www.data.go.kr/data/15077093/openapi.do
- Public Data Portal service type filters: https://www.data.go.kr/
- Seoul Open Data service metadata example: https://data.seoul.go.kr/dataList/OA-2250/S/1/datasetView.do
- Requests raw response docs: https://requests.readthedocs.io/en/latest/user/quickstart/

---

## 📚 관련 문서

### 이 저장소 내 문서
| 문서 | 설명 |
| :--- | :--- |
| [API_SPEC.md](./API_SPEC.md) | 파이썬 API 명세 |
| [CANONICAL_MODEL.md](./CANONICAL_MODEL.md) | 표준 데이터 모델 정의 |
| [PROVIDER_ADAPTER_CONTRACT.md](./PROVIDER_ADAPTER_CONTRACT.md) | 어댑터 구현 규약 |

