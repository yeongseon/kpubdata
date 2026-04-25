# Building Registry Plan (Issue #179)

## Scope
- 기존 `datago` provider 카탈로그에 건축물대장 정보 서비스 v2 기반 데이터셋 4종을 추가한다.
- 각 데이터셋(`building_title`, `building_recap_title`, `building_floor`, `building_area`)에 대해 fixture와 fixture 기반 unit test를 추가한다.
- 지원 상태 문서 `SUPPORTED_DATA.md`를 동일 PR에서 갱신한다.
- 기존 generic `DataGoAdapter`를 그대로 사용하고 provider-specific parsing 로직은 추가하지 않는다.

## Touched modules
- 구현
  - `src/kpubdata/providers/datago/catalogue.json`
- 테스트/fixture
  - `tests/fixtures/datago/success_building_title.json`
  - `tests/fixtures/datago/success_building_recap_title.json`
  - `tests/fixtures/datago/success_building_floor.json`
  - `tests/fixtures/datago/success_building_area.json`
  - `tests/unit/providers/datago/test_fixtures.py`
- 문서
  - `SUPPORTED_DATA.md`

## Risks
- 건축물대장 API의 JSON 지원이 환경별로 다를 수 있어 fixture는 표준 datago envelope 기준으로 유지해야 한다.
- 기존 카탈로그 정렬/형식을 깨뜨리면 unrelated dataset discovery 테스트에 영향이 갈 수 있다.
- `SUPPORTED_DATA.md` 상태/검증 정의와 실제 테스트 수준이 어긋나지 않도록 `테스트 검증`으로만 표기해야 한다.

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
   - 새 데이터셋 4종이 `client.datasets.list()`에 노출되는 카탈로그 메타데이터 구조를 유지하는지 확인
   - fixture test에서 `RecordBatch.items`와 `total_count`가 기대대로 파싱되는지 확인
