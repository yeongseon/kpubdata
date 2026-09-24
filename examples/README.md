# 예제 스크립트 규약

데이터셋당 파일 1개, **파일 경로 = 데이터셋 id**(``examples/{provider}/{dataset_key}.py``).
예제는 문서이자 검증 대상이다 — ``make verify`` 4단계에서 replay 모드로 실행된다.

## 규칙

1. **파라미터는 spec의 examples[]와 동일**하게 쓴다 — replay 모드가 fixture를
   찾는 조건이다. 파라미터를 바꾸려면 spec과 fixture(``make record``)를 함께 갱신.
2. **의미 있는 assert 최소 1개** — 필수 필드 존재, 값 범위, 총건수 등.
   ``assert True`` 금지(검증 약화).
3. **``if __name__ == "__main__"``** 로 단독 실행 가능해야 한다.
4. 실행 모드:
   - ``KPUBDATA_MODE=replay`` — fixture 재생, 키 불필요(더미 키 사용), CI/에이전트용
   - 미지정 — 실호출(해당 Provider API 키 필요)
5. replay 모드에서 API 키는 더미로 대체 가능하다 — 인증 파라미터는 fixture
   매칭에서 제외된다(``kpubdata.transport.replay`` 참조).

## 목록

| 예제 | 골든 범주 | 설명 |
|---|---|---|
| ``datago/hospital_info.py`` | 단순 | 필수 필터 없음, 총건수 확인 |
| ``datago/apt_trade.py`` | 페이지네이션 | 필수 필터 + 필드 구조 검증 |
| ``datago/village_fcst.py`` | XML 응답 | 카테고리 구조 + 예보 항목 검증 |
| ``datago/air_station.py`` | 네이스트 배열 items | 선택 필드(pm25) 처리 + 측정 구조 검증 |
| ``datago/ultra_srt_fcst.py`` | 시간 민감 파라미터 | 초단기 카테고리(T1H/RN1) 검증 |

## 문서 생성

``uv run python scripts/gen_docs_examples.py`` — 본 디렉터리의 스크립트에서
``docs/dataset-examples.md`` 를 생성한다(수정 후 커밋 필수).
