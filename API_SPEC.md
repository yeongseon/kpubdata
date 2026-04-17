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
        "bok": "...",
    },
    timeout=10.0,
)
```

### Environment construction

```python
client = Client.from_env()
```

## 3. Discovery API

```python
client.datasets.list()
client.datasets.search("지하철")
client.dataset("datago.apt_trade")
```

## 4. Bound dataset operations

### List/query

```python
dataset = client.dataset("datago.apt_trade")
result = dataset.list(LAWD_CD="11680", DEAL_YMD="202503")
```

`list()` returns exactly one page of results. When another page is available,
the returned `RecordBatch.next_page` is set.

### List all pages

```python
dataset = client.dataset("datago.apt_trade")
for batch in dataset.list_all(LAWD_CD="11680", DEAL_YMD="202503"):
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
raw = dataset.call_raw(operation="list", LAWD_CD="11680", DEAL_YMD="202503")
```

## 5. Convenience aliases

Optional convenience aliases may be added for common datasets, but only if they do not obscure the canonical dataset id.

Example:

```python
client.apt_trade.list(LAWD_CD="11680", DEAL_YMD="202503")
```

Rules:

- convenience aliases are secondary
- docs should always show the canonical `client.dataset(...)` path

## 6. Return values

### `list()`

Returns `RecordBatch`.

### `list_all()`

Returns a generator of `RecordBatch` values, one per page.

### `to_pandas()`

`RecordBatch.to_pandas()` converts items to a pandas DataFrame.
Requires optional `pandas` dependency (`pip install kpubdata[pandas]`).
Returns `object` (a `pandas.DataFrame` at runtime).

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
client.dataset("datago.village_fcst").list(base_date="20250401", base_time="0500", nx="55", ny="127")
```

Acceptable advanced usage:

```python
client.dataset("datago.village_fcst").call_raw("getVilageFcst", base_date="20250401", base_time="0500", nx="55", ny="127")
```

Discouraged as the main public entry point:

```python
client.call_provider_endpoint("datago", "getVilageFcst", ...)
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
