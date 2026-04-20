# Public API specification — KPubData

## 1. Top-level API

```python
from kpubdata import Client
```

## 2. Client construction

### Explicit construction

```python
client = Client(
    provider_keys={
        "datago": "...",
        "seoul": "...",
    },
    timeout=10.0,
    cache=True,
    cache_ttl_seconds=3600,
)
```

`Client(...)` supports these transport/cache options:

- `timeout: float = 30.0`
- `max_retries: int = 3`
- `cache: bool | ResponseCache = False`
  - `False`: disable cache (default)
  - `True`: use default disk cache directory
  - `ResponseCache(...)`: use a caller-supplied cache instance
- `cache_ttl_seconds: int = 86400`

### Environment construction

```python
client = Client.from_env()
```

`Client.from_env()` additionally honors:

- `KPUBDATA_CACHE=1`
- `KPUBDATA_CACHE_DIR=/custom/cache/path`
- `KPUBDATA_CACHE_TTL=3600`

## 3. Discovery API

```python
client.datasets.list()
client.datasets.search("지하철")
client.dataset("molit.apartment_trades")
```

## 4. Bound dataset operations

### List/query

```python
dataset = client.dataset("molit.apartment_trades")
result = dataset.list(lawd_code="11680", deal_ym="202503")
```

`list()` returns exactly one page of results. When another page is available,
the returned `RecordBatch.next_page` is set.

### List all pages

```python
dataset = client.dataset("molit.apartment_trades")
for batch in dataset.list_all(lawd_code="11680", deal_ym="202503"):
    for item in batch.items:
        print(item)
```

`list_all()` yields one `RecordBatch` per page and follows `next_page`
automatically until pagination is exhausted.

### Schema

```python
schema = dataset.schema()
```

### Raw

```python
raw = dataset.call_raw(operation="list", lawd_code="11680", deal_ym="202503")
```

## 5. Convenience aliases

Optional convenience aliases may be added for common datasets, but only if they do not obscure the canonical dataset id.

Example:

```python
client.apartment_trades.list(lawd_code="11680", deal_ym="202503")
```

Rules:

- convenience aliases are secondary
- docs should always show the canonical `client.dataset(...)` path

## 6. Return values

### `list()`

Returns `RecordBatch`.

### `list_all()`

Returns a generator of `RecordBatch` values, one per page.

### `schema()`

Returns `SchemaDescriptor | None`.

### `call_raw()`

Returns provider-native payload / response object.

## 7. Public API promises

KPubData promises stability for:

- `Client`
- `Client.from_env()`
- dataset discovery methods
- `Dataset.list/list_all/schema/call_raw`
- canonical model classes
- canonical error types

KPubData does **not** promise stability for:

- internal adapter helper functions
- internal transport implementation details
- provider-specific metadata layout beyond documented keys

## 8. Anti-goals for the API surface

Avoid turning the public API into:

- copied endpoint names from providers
- a giant generic `query()` with dozens of weakly-defined arguments
- a mandatory dataframe API
- a fake SQL-like language

## 9. Suggested usage style

Preferred:

```python
client.dataset("seoul.subway.arrivals").list(station_name="강남")
```

Acceptable advanced usage:

```python
client.dataset("seoul.subway.arrivals").call_raw(operation="list", stationNm="강남")
```

Discouraged as the main public entry point:

```python
client.call_provider_endpoint("seoul", "SearchSTNTimeTableByIDService", ...)
```

---

## 관련 문서

### 이 저장소 내 문서
| 문서 | 설명 |
| :--- | :--- |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 시스템 아키텍처 설계 |
| [CANONICAL_MODEL.md](./CANONICAL_MODEL.md) | 표준 데이터 모델 정의 |
| [PROVIDER_ADAPTER_CONTRACT.md](./PROVIDER_ADAPTER_CONTRACT.md) | 어댑터 구현 규약 |
| [VALIDATION.md](./VALIDATION.md) | 아키텍처 타당성 검증 |

### KPubData Product Family
| 저장소 | 문서 | 설명 |
| :--- | :--- | :--- |
| [kpubdata-builder](https://github.com/yeongseon/kpubdata-builder) | [API_CONTRACT.md](https://github.com/yeongseon/kpubdata-builder/blob/main/API_CONTRACT.md) | Builder API 규약 |
| [kpubdata-studio](https://github.com/yeongseon/kpubdata-studio) | [API_CONTRACT.md](https://github.com/yeongseon/kpubdata-studio/blob/main/API_CONTRACT.md) | Studio API 규약 |
