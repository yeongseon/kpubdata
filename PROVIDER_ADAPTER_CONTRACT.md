# Provider adapter contract — KPubData

## 1. Purpose

This document defines what it means to add a provider adapter to KPubData.

A provider adapter is the place where backend-specific behavior belongs.

## 2. Responsibilities

Every adapter must be responsible for:

- auth/key injection
- dataset discovery or dataset registration
- canonical-to-native parameter translation
- native-to-canonical result translation
- provider-specific error translation
- raw-call support
- honest capability declaration

## 3. Minimal protocol

```python
from typing import Protocol

class ProviderAdapter(Protocol):
    name: str

    def list_datasets(self) -> list[DatasetRef]: ...
    def search_datasets(self, text: str) -> list[DatasetRef]: ...
    def get_dataset(self, dataset_id: str) -> DatasetRef: ...
    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch: ...
    def get_record(self, dataset: DatasetRef, key: dict[str, object]) -> dict[str, object] | None: ...
    def get_schema(self, dataset: DatasetRef) -> SchemaDescriptor | None: ...
    def call_raw(self, dataset: DatasetRef, operation: str, params: dict[str, object]) -> object: ...
```

## 4. Capability rules

- declare only what the adapter truly supports
- if an operation is unavailable, raise `UnsupportedCapabilityError`
- do not silently emulate unsupported semantics unless documented

## 5. Raw rules

- every adapter must expose a raw path
- raw paths may be inconvenient; they must still be available
- raw payloads should not be lossy-normalized

## 6. Discovery rules

Adapters may support discovery via:

- static registrations
- provider metadata API
- cached generated manifests

At minimum, the adapter must surface enough metadata to populate `DatasetRef`.

## 7. Parse and normalization rules

Normalize only the common envelope and broadly reusable metadata.

Do not destroy provider-native fields. Prefer one of these approaches:

- preserve raw payload at `RecordBatch.raw`
- preserve unmapped fields in item-level metadata

## 8. Testing requirements

Every adapter must include:

- unit tests for mapping/parsing
- contract tests for declared capabilities
- fixture-based tests for representative success/failure responses

## 9. When to extend the core instead of the adapter

Only extend the core when:

- three or more adapters need the same concept
- it improves the public contract materially
- it reduces duplication without hiding semantics

Otherwise, keep the complexity local to the adapter.

## 10. Example adapter development checklist

1. define provider config and auth requirements
2. define dataset ids and metadata
3. implement discovery
4. implement `query_records`
5. implement `call_raw`
6. map provider errors
7. add fixtures and tests
8. document capabilities and caveats

