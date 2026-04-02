# ADR 0001: Adopt a dialect-inspired architecture

## Status
Accepted

## Context
Korean public-data providers differ materially in auth, request shape, representation format, pagination, and error signaling.

## Decision
Use a small stable canonical core and put provider-specific behavior into adapters.

## Consequences

### Positive
- easier incremental provider growth
- stable public API
- explicit separation of concerns

### Negative
- adapters still require manual implementation
- some duplication may remain local to providers

