# SGIS Provider Plan (Issue #150)

## Scope
- SGIS 행정구역 경계(시도/시군구/읍면동) 조회를 위한 신규 provider adapter(`sgis`)를 추가한다.
- SGIS의 2단계 인증(consumer_key + consumer_secret -> accessToken)을 어댑터 내부에서 처리한다.
- 경계 응답(GeoJSON FeatureCollection)을 `RecordBatch.items` 단위 레코드로 정규화한다.
- fixture/unit/contract 테스트를 추가하고 SUPPORTED_DATA/CHANGELOG/README를 동기화한다.

## Touched modules
- 구현
  - `src/kpubdata/providers/sgis/__init__.py`
  - `src/kpubdata/providers/sgis/auth.py`
  - `src/kpubdata/providers/sgis/adapter.py`
  - `src/kpubdata/providers/sgis/catalogue.json`
- 코어 연결
  - `src/kpubdata/client.py` (builtin provider lazy registration에 `sgis` 추가)
  - `src/kpubdata/config.py` (`KPUBDATA_SGIS_CONSUMER_SECRET` 조회 확장)
- 테스트/fixture
  - `tests/fixtures/sgis/*`
  - `tests/unit/providers/sgis/test_auth.py`
  - `tests/unit/providers/sgis/test_adapter.py`
  - `tests/contract/test_sgis.py`
- 문서
  - `SUPPORTED_DATA.md`
  - `CHANGELOG.md`
  - `README.md` (provider 목록이 있는 경우)

## Risks
- SGIS 응답은 localdata/datago의 표준 envelope과 달리 GeoJSON 직접 반환이므로, 에러 감지 누락 위험이 있다.
- accessToken 만료 시점(`accessTimeout`) 처리 실패 시 연쇄적인 인증 실패가 발생할 수 있다.
- `consumer_secret` 확장 방식이 기존 `KPubDataConfig` 사용자를 깨뜨릴 위험이 있다.
- SGIS 오류코드 문서가 버전별로 산재되어 있어 오류 매핑이 과소/과대될 수 있다.

## Validation steps
1. 정적 검증
   - `uv run ruff check .`
   - `uv run ruff format --check .`
   - `uv run mypy src`
2. 테스트
   - `uv run pytest`
   - SGIS unit/contract 테스트가 포함되어 통과하는지 확인
3. 패키징
   - `uv run python -m build`
4. 수동 확인
   - `client.dataset("sgis.boundary.sido").list(...)` 호출 경로에서 adapter가 registry에 로드되는지 확인
   - `call_raw`가 원본 FeatureCollection을 손실 없이 반환하는지 확인
