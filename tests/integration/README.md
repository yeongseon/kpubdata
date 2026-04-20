# Integration test notes

`tests/integration/test_datago_live.py` includes a small opt-in gate for endpoints that require extra 활용신청 scope on top of `KPUBDATA_DATAGO_API_KEY`.

## data.go.kr live test env gates

- Base data.go.kr live tests run when `KPUBDATA_DATAGO_API_KEY` is set.
- Real-estate scoped endpoints and the current `bus_arrival` live check additionally require:

```bash
export KPUBDATA_DATAGO_REALESTATE_ENABLED=1
```

Keep this flag **off by default** unless the current key has already been approved for the required 활용신청 scope. Otherwise those tests skip with a message explaining how to enable them.

## Why this exists

- 기상청 date-bound live tests use runtime KST dates so they do not expire.
- 국토부 RTMS 계열 API는 서비스키가 있어도 API별 활용신청 승인 전까지 403/404가 날 수 있어 기본 실행에서는 skip 처리합니다.
- 서울교통공사 metro live tests are unconditionally skipped until upstream issues are resolved:
  - `metro_fare`: issue [#139](https://github.com/yeongseon/kpubdata/issues/139)
  - `metro_path`: issue [#140](https://github.com/yeongseon/kpubdata/issues/140)
