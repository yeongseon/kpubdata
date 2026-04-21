# 서울 열린데이터광장 (seoul)

## 개요

서울 열린데이터광장은 서울시 교통·환경·행정 데이터를 Open API로 제공합니다. KPubData의 `seoul` provider는 서울 Open API의 경로 기반 인증키, 서비스별 top-level envelope, 시작/종료 인덱스 기반 페이지네이션을 그대로 존중하면서 `list()`와 `call_raw()`를 제공합니다.

- KPubData provider 이름: `seoul`
- 포털: <https://data.seoul.go.kr/>

## 인증키 발급 및 환경 변수 설정

1. [서울 열린데이터광장](https://data.seoul.go.kr/)에 가입합니다.
2. 사용하려는 Open API 페이지에서 인증키를 신청하거나 발급 상태를 확인합니다.
3. 마이페이지에서 인증키를 복사합니다.
4. 환경 변수에 설정합니다.

```bash
export KPUBDATA_SEOUL_API_KEY="your-seoul-api-key"
```

`Client.from_env()`는 위 환경 변수를 자동으로 읽습니다.

## 서울 Open API 호출 규칙

- 인증키는 **쿼리 파라미터가 아니라 URL 경로 세그먼트**입니다.
- 응답 형식은 `json`으로 고정합니다.
- 페이지네이션은 `start_index` / `end_index` 기반입니다.
- KPubData의 `list(page=..., page_size=...)`는 아래 규칙으로 변환됩니다.

```text
start_index = (page - 1) * page_size + 1
end_index = page * page_size
```

- 최대 `page_size`는 `1000`입니다.

### URL 패턴

#### 1) 지하철 실시간 도착정보

```text
http://swopenAPI.seoul.go.kr/api/subway/{KEY}/json/realtimeStationArrival/{START_INDEX}/{END_INDEX}/{stationName}
```

#### 2) 따릉이 이용정보(월별)

```text
http://openapi.seoul.go.kr:8088/{KEY}/json/tbCycleRentUseMonthInfo/{START_INDEX}/{END_INDEX}/{RENT_NM}
```

## 지원 데이터셋

### 1. `subway_realtime_arrival`

- 서비스명: `realtimeStationArrival`
- 필수 경로 파라미터: `stationName`
- 예시 값: `"강남"`

### 2. `bike_rent_month`

- 서비스명: `tbCycleRentUseMonthInfo`
- 필수 경로 파라미터: `RENT_NM`
- 예시 값: `"202401"`

## 에러 코드 매핑

| 코드 | 의미 | KPubData 예외 |
|---|---|---|
| `INFO-000` | 정상 처리 | 예외 없음 |
| `INFO-100` | 인증키 오류 | `AuthError` |
| `INFO-200` | 데이터 없음 | 빈 `RecordBatch` 반환 |
| `INFO-300` | 인증키 권한 없음 | `AuthError` |
| `INFO-400` | HTTP/요청 오류 | `InvalidRequestError` |
| `INFO-500` | 서버 오류 | `ProviderResponseError` |
| `ERROR-300` | 필수값 누락 | `InvalidRequestError` |
| `ERROR-301` | 서비스명 오류 | `InvalidRequestError` |
| `ERROR-310` | 서비스 미존재 | `InvalidRequestError` |
| `ERROR-336` | 페이지 인덱스 오류 | `InvalidRequestError` |
| `ERROR-500` | 일반 서버 오류 | `ProviderResponseError` |
| `ERROR-600` | 일반 서버 오류 | `ProviderResponseError` |
| `ERROR-601` | 일반 서버 오류 | `ProviderResponseError` |

알 수 없는 코드도 `ProviderResponseError`로 매핑합니다.

## 사용 예제

### 지하철 실시간 도착정보 `list()`

```python
from kpubdata import Client

client = Client.from_env()
ds = client.dataset("seoul.subway_realtime_arrival")

result = ds.list(stationName="강남", page_size=5)

for item in result.items:
    print(item["statnNm"], item["arvlMsg2"], item["arvlMsg3"])
```

### 지하철 실시간 도착정보 `call_raw()`

```python
raw = ds.call_raw("realtimeStationArrival", stationName="강남", page_no=1, page_size=5)
print(raw["realtimeStationArrival"]["RESULT"])
```

### 따릉이 월별 이용정보 `list()`

```python
from kpubdata import Client

client = Client.from_env()
ds = client.dataset("seoul.bike_rent_month")

result = ds.list(RENT_NM="202401", page=1, page_size=10)

for item in result.items:
    print(item["RENT_NO"], item["RENT_USE_CNT"], item["MOVE_METER"])
```

### 따릉이 월별 이용정보 `call_raw()`

```python
raw = ds.call_raw("tbCycleRentUseMonthInfo", RENT_NM="202401", page_no=1, page_size=10)
print(raw["tbCycleRentUseMonthInfo"]["list_total_count"])
```

## 참고

- `list()`는 한 번에 한 페이지만 반환하며, 다음 페이지가 있으면 `RecordBatch.next_page`가 채워집니다.
- 서울 Open API의 서비스명과 경로 파라미터 이름은 provider-specific semantics이므로 그대로 유지합니다.
- 실API 검증은 서울 인증키 확보 후 후속 PR에서 `SUPPORTED_DATA.md`의 검증 상태를 갱신할 예정입니다.
