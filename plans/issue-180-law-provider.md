# Law Provider Plan (Issue #180)

## Scope
- 법제처 국가법령정보 공동활용 Open API용 신규 provider `law`를 추가한다.
- `law_search`, `law_detail`, `ordin_search` 데이터셋 3종을 카탈로그/어댑터/manifest에 등록한다.
- fixture, unit test, contract test, `SUPPORTED_DATA.md`를 같은 작업에서 갱신한다.
- law.go.kr의 고유 규칙(인증 `OC`, root-level JSON, `display`/`page` 페이지네이션)을 datago와 분리해 정직하게 반영한다.

## Touched modules
- 구현
  - `src/kpubdata/providers/law/__init__.py`
  - `src/kpubdata/providers/law/adapter.py`
  - `src/kpubdata/providers/law/catalogue.json`
  - `src/kpubdata/providers/manifest.py`
- 테스트/fixture
  - `tests/fixtures/law/success_law_search.json`
  - `tests/fixtures/law/success_law_detail.json`
  - `tests/fixtures/law/success_ordin_search.json`
  - `tests/unit/providers/law/test_adapter.py`
  - `tests/contract/test_law.py`
- 문서
  - `SUPPORTED_DATA.md`

## Risks
- law.go.kr 응답은 datago-style `response.header/body` envelope이 없어서 공통 파서 재사용 시 잘못된 에러 해석 위험이 있다.
- `law_detail` 응답 구조는 중첩 객체/배열이 섞여 있으므로 raw escape hatch만 제공하고 fake universal semantics를 만들지 않아야 한다.
- root-level 배열 키(`law`, `ordin`)와 `totalCnt`가 dataset별로 달라서 metadata-driven item key 선택이 누락되면 빈 결과로 파싱될 수 있다.
- `SUPPORTED_DATA.md`는 fixture/unit/contract 기준으로만 `테스트 검증` 상태를 써야 한다.

## Validation steps
1. 정적 검증
   - `uv run ruff check .`
   - `uv run ruff format --check .`
   - `uv run mypy src`
2. 테스트
   - `uv run pytest -x -q`
3. 패키징/추가 게이트
   - `uv run python -m build`
4. 완료 확인
   - `client.datasets.list()`에서 `law.*` 데이터셋 3종이 provider metadata와 함께 노출되는지 확인
   - `query_records()`가 `law_search`/`ordin_search`에서 `RecordBatch.items`, `total_count`, `next_page`를 정확히 계산하는지 확인
   - `call_raw()`가 `law_detail` 원본 JSON을 손실 없이 반환하는지 확인
