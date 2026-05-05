# Data.go.kr DUR Co-use Taboo Plan (Issue #92)

## Scope
- Add only the data.go.kr `getUsjntTabooInfoList03` operation as `datago.dur_usjnt_taboo`.
- Keep the implementation metadata-driven through the existing `DataGoAdapter`.
- Do not add other DUR operations, shared DUR abstractions, or public API changes.
- Update fixture, unit, contract, and support-status documentation in the same change.

## Touched modules
- `src/kpubdata/providers/datago/catalogue.json`
- `tests/fixtures/datago/success_dur_usjnt_taboo.json`
- `tests/unit/providers/datago/test_fixtures.py`
- `tests/contract/test_datago.py`
- `SUPPORTED_DATA.md`

## Risks
- The official API supports both XML and JSON, but this change only proves the existing JSON envelope path through a sanitized fixture.
- `SUPPORTED_DATA.md` must remain conservative: this is test-verified only, not real-API verified.
- The operation-specific fields are provider-native and should not be normalized into broader DUR semantics.

## Validation steps
1. `uv run ruff check .`
2. `uv run ruff format --check .`
3. `uv run mypy src`
4. `uv run pytest`
5. `git diff --stat`
6. `git diff`
