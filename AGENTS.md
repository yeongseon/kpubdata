# AGENTS.md

## Purpose

This repository is built for agentic coding and Codex-heavy development.

The project is a Python 3.10+ framework with a small stable public API and provider-specific adapters.

## Read these first

1. `VALIDATION.md`
2. `PRD.md`
3. `ARCHITECTURE.md`
4. `CANONICAL_MODEL.md`
5. `PROVIDER_ADAPTER_CONTRACT.md`
6. `API_SPEC.md`
7. `PACKAGING.md`

## Rules of engagement

- Keep the public API small.
- Do not turn provider quirks into fake universal semantics.
- Do not remove raw escape hatches.
- Do not mark a capability as supported unless tests prove it.
- Keep provider complexity in provider adapters.
- Update tests and docs with every behavior change.

## When to write a plan

Before multi-file or architecture-affecting work, create or update a task plan in a local plan file.

The plan should include:

- scope
- touched modules
- risks
- validation steps

## Quality gates

Run before marking work complete:

```bash
uv sync --extra dev
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
uv run python -m build
```

## Adapter work rules

When adding a provider adapter:

- add fixture responses
- add unit tests
- add contract tests
- document capabilities honestly
- keep `call_raw` working

## Public API change rule

If a public method, public model, or canonical exception changes:

- update `API_SPEC.md`
- update `PRD.md` if requirements changed
- add release note/changelog entry

