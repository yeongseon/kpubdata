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
client.dataset("molit.apartment_trades")
```

## 4. Bound dataset operations

### List/query

```python
dataset = client.dataset("molit.apartment_trades")
result = dataset.list(lawd_code="11680", deal_ym="202503")
```

### Single record

```python
record = dataset.get(id="...")
```

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

### `get()`

Returns one normalized record or `None`.

### `schema()`

Returns `SchemaDescriptor | None`.

### `call_raw()`

Returns provider-native payload / response object.

## 7. Public API promises

KPubData promises stability for:

- `Client`
- `Client.from_env()`
- dataset discovery methods
- `Dataset.list/get/schema/call_raw`
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

