# ADR 0002: Standardize UX, not every native API shape

## Status
Accepted

## Context
A single perfect universal query language for all Korean public-data providers would be misleading and fragile.

## Decision
Standardize entry points and result envelopes while allowing provider-specific parameters and raw access.

## Consequences

### Positive
- more honest abstraction
- easier debugging
- better long-term adapter compatibility

### Negative
- some provider-specific knowledge still leaks into advanced use cases

