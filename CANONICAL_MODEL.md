# Canonical model — KPubData

## 1. Purpose

The canonical model defines the smallest stable set of objects needed to make heterogeneous public-data services usable through one Python framework.

The model should be:

- small
- explicit
- typed
- extensible by metadata
- honest about unsupported behavior

## 2. Design rule

Canonical objects standardize the **framework contract**, not every semantic detail of every provider.

## 3. Core types

### 3.1 Capability

```python
from enum import Enum

class Capability(str, Enum):
    LIST = "list"
    GET = "get"
    SCHEMA = "schema"
    RAW = "raw"
    PAGEABLE = "pageable"
    FILTERABLE = "filterable"
    SORTABLE = "sortable"
    TIME_RANGE = "time_range"
    DOWNLOAD = "download"
    REALTIME = "realtime"
```

### 3.2 Representation

```python
from enum import Enum

class Representation(str, Enum):
    OPENAPI = "openapi"
    FILE = "file"
    SHEET = "sheet"
    DOWNLOAD = "download"
    OTHER = "other"
```

### 3.3 DatasetRef

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass(slots=True, frozen=True)
class DatasetRef:
    id: str
    provider: str
    dataset_key: str
    name: str
    representation: Representation
    capabilities: frozenset[Capability] = frozenset()
    raw_metadata: dict[str, Any] = field(default_factory=dict)
```

Notes:

- `id` is the stable bound identifier, e.g. `molit.apartment_trades`
- `representation` matters because the same logical dataset may be offered in more than one form

### 3.4 Query

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass(slots=True)
class Query:
    filters: dict[str, Any] = field(default_factory=dict)
    page: int | None = None
    page_size: int | None = None
    cursor: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    fields: list[str] | None = None
    sort: list[str] | None = None
    extra: dict[str, Any] = field(default_factory=dict)
```

Notes:

- `filters` covers the normal case
- `extra` exists so adapters can carry provider-native hints without contaminating the core model

### 3.5 RecordBatch

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass(slots=True)
class RecordBatch:
    items: list[dict[str, Any]]
    dataset: DatasetRef
    total_count: int | None = None
    next_page: int | None = None
    next_cursor: str | None = None
    raw: Any | None = None
    meta: dict[str, Any] = field(default_factory=dict)
```

### 3.6 SchemaDescriptor

```python
from dataclasses import dataclass, field

@dataclass(slots=True)
class FieldDescriptor:
    name: str
    title: str | None = None
    type: str | None = None
    description: str | None = None
    nullable: bool | None = None
    raw: dict[str, object] = field(default_factory=dict)

@dataclass(slots=True)
class SchemaDescriptor:
    dataset: DatasetRef
    fields: list[FieldDescriptor]
    raw: dict[str, object] = field(default_factory=dict)
```

## 4. Error model

```python
class PublicDataError(Exception): ...
class ConfigError(PublicDataError): ...
class AuthError(PublicDataError): ...
class TransportError(PublicDataError): ...
class TimeoutError(TransportError): ...
class ParseError(PublicDataError): ...
class InvalidRequestError(PublicDataError): ...
class ProviderResponseError(PublicDataError): ...
class UnsupportedCapabilityError(PublicDataError): ...
class DatasetNotFoundError(PublicDataError): ...
```

## 5. Bound Dataset object

A bound dataset object wraps `DatasetRef` plus registry/config context.

Suggested shape:

```python
class Dataset:
    ref: DatasetRef

    def list(self, **filters) -> RecordBatch: ...
    def get(self, **key) -> dict[str, object] | None: ...
    def schema(self) -> SchemaDescriptor | None: ...
    def call_raw(self, operation: str, **params) -> object: ...
```

## 6. What the model deliberately does not do

It does not attempt to fully standardize:

- every domain field
- every geographic key
- every date format
- every pagination style
- every schema guarantee

Those belong in provider-specific metadata, mappers, and raw payloads.

## 7. Normalization rule

Normalize only what is broadly useful across providers:

- paging metadata
- canonical error type
- dataset identity
- representation
- item list envelope

Do not erase provider-native detail.

