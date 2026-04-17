# Packaging and release strategy — KPubData

## 1. Packaging goals

- modern Python packaging
- Python 3.10+
- minimal core dependencies
- optional extras for heavier integrations
- reproducible local development for human and agentic workflows

## 2. Recommended choices

### Build backend

Use `hatchling` as the build backend.

Why:

- simple and modern
- PEP 517/518 friendly
- good fit for a typed library with `src/` layout

### Project metadata

Use PEP 621 metadata in `pyproject.toml`.

### Environment/workflow tool

Use `uv` for local sync/install/test workflows.

This keeps packaging standards-based while making developer workflows fast.

## 3. Python support policy

- minimum: Python 3.10
- tested: 3.10, 3.11, 3.12, 3.13

## 4. Dependency policy

### Core dependencies

Keep core lean.

Expected core set:

- `httpx` or `requests`-style HTTP client (choose one)
- XML parsing support only if truly needed in core
- typing/runtime helpers only when justified

### Optional extras

- `xml`
- `pandas`
- `mcp`
- `dev`
- `docs`

## 5. Recommended package structure

```text
src/
  kpubdata/
```

Reasons:

- avoids accidental import-from-project-root mistakes
- works well with modern build backends and type checking

## 6. Build and release steps

### Local

```bash
uv sync --extra dev
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
uv run python -m build
```

### Release

1. bump version
2. update changelog
3. run full quality gates
4. build sdist + wheel
5. publish to TestPyPI/PyPI

## 7. Versioning policy

Use SemVer with public API discipline.

- `0.x`: fast iteration, but still document breaking changes
- `1.0`: only when the public Python API and adapter contract feel stable

## 8. Naming policy

- project name: `KPubData`
- package/import name: `kpubdata`
- repository name: preferably `kpubdata` or `kpubdata-framework`

### 빌드 및 배포 파이프라인

```mermaid
graph LR
    Dev[개발] --> Lint[Lint/Format]
    Lint --> Type[Type Check]
    Type --> Test[Test]
    Test --> Build[Build]
    Build --> Release[Release]
```

### 의존성 요약

| 구분 | 패키지 | 용도 |
|---|---|---|
| 코어 | `httpx` | HTTP 클라이언트 |
| 선택 (xml) | XML 파서 | XML 응답 처리 |
| 선택 (pandas) | `pandas` | DataFrame 변환 |
| 선택 (dev) | `ruff`, `mypy`, `pytest` | 개발 도구 |
| 빌드 | `hatchling` | PEP 517 빌드 백엔드 |

---

## 관련 문서

### 이 저장소 내 문서
| 문서 | 설명 |
| :--- | :--- |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 시스템 아키텍처 설계 |
| [API_SPEC.md](./API_SPEC.md) | 파이썬 API 명세 |
| [VALIDATION.md](./VALIDATION.md) | 아키텍처 타당성 검증 |

