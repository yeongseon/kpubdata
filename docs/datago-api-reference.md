# data.go.kr API Reference

This document summarizes the public API conventions of **data.go.kr**
(공공데이터포털) as they affect KPubData's `DataGoAdapter`.

## 1. Scope

**v0.1 targets the `apis.data.go.kr` endpoint family only.**

The portal also hosts datasets under `api.odcloud.kr`, which uses a
different auth mechanism, envelope shape, and pagination model.
A separate adapter (or dialect section) will cover odcloud in a future
release.

## 2. Authentication

Every request requires a `serviceKey` query parameter.

- Keys are issued per-user at <https://www.data.go.kr> after registering
  for a specific dataset.
- Some legacy APIs spell the parameter `ServiceKey` (capital S).
  The adapter should default to `serviceKey` but allow dataset metadata
  to override the parameter name.
- The portal exposes both encoded and decoded key variants. The adapter
  should accept the **decoded** form and let the HTTP library handle
  percent-encoding transparently — **do not double-encode**.

```python
params = {"serviceKey": api_key, "pageNo": 1, "numOfRows": 10}
```

## 3. Base URLs

There is **no single unified endpoint**. Each dataset registered under
`apis.data.go.kr` has its own base URL:

| Pattern | Example |
|---|---|
| `http(s)://apis.data.go.kr/{org}/{service}` | `http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0` |

The adapter receives the base URL from the `DatasetRef.endpoint` field.
Operation resolution (e.g. `/getVilageFcst`) comes from dataset
metadata and **must not be hardcoded** in the adapter.

## 4. Response format

### 4.1 Choosing format

Most APIs support both JSON and XML, controlled by:

- `resultType=json` (or `type=json` on some APIs)
- Default is usually XML if the parameter is omitted.

KPubData prefers JSON when supported. If a dataset only supports XML,
the transport layer parses it via `xmltodict` and the resulting dict
mirrors the JSON shape.

### 4.2 Standard envelope

```json
{
  "response": {
    "header": {
      "resultCode": "00",
      "resultMsg": "NORMAL SERVICE."
    },
    "body": {
      "items": {
        "item": [ ... ]
      },
      "numOfRows": 10,
      "pageNo": 1,
      "totalCount": 150
    }
  }
}
```

Key paths:

| Field | Path | Description |
|---|---|---|
| Success flag | `response.header.resultCode == "00"` | `"00"` means OK |
| Error message | `response.header.resultMsg` | Human-readable status |
| Records | `response.body.items.item` | See §4.3 for normalization |
| Total count | `response.body.totalCount` | Advisory — see §5 |
| Page number | `response.body.pageNo` | Current page (1-based) |
| Page size | `response.body.numOfRows` | Rows per page |

### 4.3 Item normalization quirks

The `items.item` field is **not always a list**:

| Condition | `items.item` value |
|---|---|
| Multiple results | `list[dict]` |
| Single result | `dict` (not wrapped in a list) |
| Zero results | `null`, missing, or `items` itself is missing |

The adapter **must** normalize to `list[dict]` in all cases before
returning records.

### 4.4 String-typed numerics

Numeric fields like `pageNo`, `numOfRows`, and `totalCount` may arrive
as **strings**. The adapter must cast these to `int` defensively.

### 4.5 XML variant

XML uses the same logical structure. `items > item` becomes repeated
`<item>` elements. Use `xmltodict` for conversion; the resulting dict
mirrors the JSON shape but is even more likely to return single items
as dicts rather than lists.

## 5. Pagination

Page-based with two parameters:

| Parameter | Default | Description |
|---|---|---|
| `pageNo` | `1` | 1-indexed page number |
| `numOfRows` | `10` | Rows per page (max varies by API) |

The adapter should **always send paging parameters explicitly**, even
when defaults seem sufficient, to ensure deterministic behavior.

### Stop conditions (defensive)

The adapter should stop iterating pages when **any** of these hold:

1. The returned item list is **empty** after normalization.
2. The returned item count is **less than** the requested `numOfRows`
   (short page = last page).
3. `pageNo * numOfRows >= totalCount` (advisory upper bound).

Use `totalCount` as an advisory upper bound, **not** the sole
termination condition — some APIs return stale or incorrect counts.

### Malformed envelope handling

If the response lacks `response.header.resultCode` entirely, raise
`ProviderResponseError`. If JSON/XML parsing fails, raise `ParseError`.

## 6. Error codes

Errors are returned **inside** the response envelope, not via HTTP status
codes (most responses return HTTP 200 even on error).

| `resultCode` | `resultMsg` | Meaning |
|---|---|---|
| `"00"` | NORMAL SERVICE | Success |
| `"01"` | APPLICATION ERROR | Server-side application error |
| `"02"` | DB ERROR | Database error on the provider side |
| `"10"` | INVALID REQUEST PARAMETER | Bad query parameter |
| `"12"` | NO OPEN API SERVICE ERROR | Service ID not found / not open |
| `"20"` | SERVICE ACCESS DENIED ERROR | Key not authorised for this API |
| `"22"` | 일일 트래픽 초과 | Daily traffic quota exceeded |
| `"30"` | KEY IS NOT REGISTERED | Invalid or revoked key |
| `"31"` | DEADLINE HAS EXPIRED | Key validity period ended |
| `"32"` | UNREGISTERED IP | Caller IP not whitelisted |

### Mapping to KPubData exceptions

| Code(s) | KPubData exception | Notes |
|---|---|---|
| `"30"`, `"31"`, `"20"`, `"32"` | `AuthError` | Use `provider_code` to distinguish sub-cases |
| `"22"` | `RateLimitError` | Set `retryable=False` — this is daily quota exhaustion, not transient throttling |
| `"10"` | `InvalidRequestError` | |
| `"12"` | `DatasetNotFoundError` | Service/dataset not resolved |
| `"01"`, `"02"` | `ServiceUnavailableError` | Upstream provider failure, `retryable=True` |
| Malformed envelope | `ProviderResponseError` | Missing `resultCode` or violated contract |
| Invalid JSON/XML | `ParseError` | Transport-level decode failure |

## 7. Rate limits

- Daily call quota per service key (error code `"22"`).
- Quota is **dataset- and account-specific**, shown on each dataset's
  portal page. There is no single universal limit.
- No `Retry-After` header is provided. On code `"22"`, the adapter
  raises `RateLimitError` with `retryable=False` — daily quota
  exhaustion cannot be retried within the same day.

## 8. Common query parameters

| Parameter | Required | Description |
|---|---|---|
| `serviceKey` | | API key |
| `pageNo` | (always send) | Page number (default 1) |
| `numOfRows` | (always send) | Page size (default 10) |
| `resultType` | | `json` or `xml` (default XML) |
| *dataset-specific* | varies | Search filters, date ranges, etc. |

## 9. Adapter design implications

1. **No catalogue endpoint** — dataset discovery is external
   (the portal website). `list_datasets` returns a curated static list
   or reads from a local catalogue file.
2. **Per-dataset base URL** — stored in `DatasetRef.endpoint`.
   Operation resolution comes from dataset metadata, not hardcoded
   path construction.
3. **JSON preferred** — send `resultType=json` when the dataset
   supports it. If JSON is unsupported, let transport parse XML.
4. **Error-in-body** — check `resultCode` before processing `body`.
   HTTP 200 does not imply success.
5. **Defensive page iteration** — `query_records` must auto-paginate
   using `pageNo` / `numOfRows` with the stop conditions in §5.
6. **`call_raw`** — pass through arbitrary params and return the
   **minimally processed** provider response dict. Do not flatten or
   canonicalize — this preserves the raw escape hatch.
7. **Unsupported capabilities** — `get_record` and `get_schema` are
   **not supported** by default unless dataset metadata explicitly
   proves otherwise. Do not mark these as supported.
8. **Item normalization** — always coerce `items.item` to `list[dict]`
   as described in §4.3.

## 10. Reference implementations

- [data-go-mcp-servers](https://github.com/Koomook/data-go-mcp-servers) —
  MCP server wrappers for NPS, NTS, PPS data.go.kr APIs.
  Demonstrates auth, pagination, and error handling patterns.
