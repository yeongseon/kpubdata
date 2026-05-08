# Issue 229: BOK 통화량(M2) dataset

## 범위

- BOK ECOS dataset `bok.money_supply` 하나만 추가한다.
- 기존 BOK catalogue 기반 adapter 동작을 그대로 사용한다.
- 실API 테스트와 실제 API key는 추가하지 않는다.

## 수정 대상

- `src/kpubdata/providers/bok/catalogue.json`
- `tests/fixtures/bok/money_supply_success.json`
- `tests/unit/providers/bok/test_bok_adapter.py`
- `tests/contract/test_bok.py`
- `docs/providers/bok.md`
- `SUPPORTED_DATA.md`

## 리스크

- ECOS 항목코드는 `101Y003`의 M2 총계 시계열과 일치해야 한다.
- 실API 검증을 수행하지 않으므로 지원 상태는 fixture/test 기반으로 유지해야 한다.

## 검증

- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src`
- `uv run pytest`
