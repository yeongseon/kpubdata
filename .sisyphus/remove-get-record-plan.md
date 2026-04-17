## Scope
- Remove `get_record` from the provider protocol, registry validation, dataset binding, tests, and docs.

## Touched modules
- `src/kpubdata/core/protocol.py`
- `src/kpubdata/core/dataset.py`
- `src/kpubdata/registry.py`
- affected unit/integration/contract tests
- API and architecture docs describing removed single-record access

## Risks
- Public `Dataset.get()` removal can leave stale docs/tests behind.
- Registry validation and protocol changes can break fake adapters in tests.

## Validation steps
- Run LSP diagnostics on changed source and test files.
- Run `uv run pytest`.
- Run `uv run mypy src`.
