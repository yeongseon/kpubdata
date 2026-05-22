# data.go.kr API 레퍼런스

이 문서는 KPubData의 `DataGoAdapter`에 영향을 주는 **data.go.kr**
(공공데이터포털)의 공개 API 관례를 정리합니다.

## 1. 범위

`datago` 어댑터는 `apis.data.go.kr`와 `api.odcloud.kr` 계열을 모두 지원합니다.
`provider_family: "odcloud"` 메타데이터로 프로토콜을 분기합니다.
(`social_enterprise` 데이터셋이 ODcloud 프로토콜을 사용합니다.)

## 2. 인증

모든 요청에는 `serviceKey` 쿼리 파라미터가 필요합니다.

- 키는 특정 데이터셋에 대해 활용신청한 뒤 <https://www.data.go.kr>에서 사용자별로 발급됩니다.
- 일부 레거시 API는 파라미터를 `ServiceKey`(대문자 S)로 표기합니다.
  어댑터는 기본적으로 `serviceKey`를 사용하되, 데이터셋 메타데이터로
  파라미터 이름을 재정의할 수 있어야 합니다.
- 포털은 인코딩된 키와 디코딩된 키를 모두 제공합니다. 어댑터는
  **디코딩된** 형태를 받아들이고, HTTP 라이브러리가 퍼센트 인코딩을
  투명하게 처리하도록 해야 합니다 — **중복 인코딩하지 마세요**.

```python
params = {"serviceKey": api_key, "pageNo": 1, "numOfRows": 10}
```

## 3. 기본 URL

**단일 통합 엔드포인트는 없습니다**. `apis.data.go.kr`에 등록된 각
데이터셋은 자체 base URL을 가집니다:

| 패턴 | 예시 |
|---|---|
| `http(s)://apis.data.go.kr/{org}/{service}` | `http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0` |

어댑터는 base URL을 `DatasetRef.endpoint` 필드에서 받습니다.
오퍼레이션 결정(예: `/getVilageFcst`)은 데이터셋 메타데이터에서 오며
어댑터에 **하드코딩하면 안 됩니다**.

## 4. 응답 형식

### 4.1 형식 선택

대부분의 API는 다음 방식으로 JSON과 XML을 모두 지원합니다:

- `resultType=json` (일부 API는 `type=json`)
- 보통 이 파라미터를 생략하면 기본값은 XML입니다.

KPubData는 지원되는 경우 JSON을 우선 사용합니다. 데이터셋이 XML만
지원하면 전송 계층이 `xmltodict`로 이를 파싱하며, 결과 dict는
JSON 형태를 따릅니다.

### 4.2 표준 envelope

```json
{
  "response": {
    "header": {
      "resultCode": "00",
      "resultMsg": "NORMAL SERVICE."
    },
    "body": {
      "items": {
        "item": [ ... ]
      },
      "numOfRows": 10,
      "pageNo": 1,
      "totalCount": 150
    }
  }
}
```

주요 경로:

| 필드 | 경로 | 설명 |
|---|---|---|
| 성공 여부 | `response.header.resultCode == "00"` | `"00"`이면 정상 |
| 오류 메시지 | `response.header.resultMsg` | 사람이 읽을 수 있는 상태 메시지 |
| 레코드 | `response.body.items.item` | 정규화는 §4.3 참고 |
| 전체 건수 | `response.body.totalCount` | 참고용 — §5 참고 |
| 페이지 번호 | `response.body.pageNo` | 현재 페이지 (1부터 시작) |
| 페이지 크기 | `response.body.numOfRows` | 페이지당 행 수 |

### 4.3 `item` 정규화 특이사항

`items.item` 필드는 **항상 리스트가 아닙니다**:

| 조건 | `items.item` 값 |
|---|---|
| 결과가 여러 개 | `list[dict]` |
| 결과가 한 개 | `dict` (리스트로 감싸지 않음) |
| 결과가 0개 | `null`, 누락, 또는 `items` 자체가 없음 |

어댑터는 레코드를 반환하기 전에 모든 경우를 `list[dict]`로
정규화해야 합니다.

### 4.4 문자열로 전달되는 숫자값

`pageNo`, `numOfRows`, `totalCount` 같은 숫자 필드는
**문자열**로 올 수 있습니다. 어댑터는 방어적으로 이를 `int`로
변환해야 합니다.

### 4.5 XML 변형

XML도 동일한 논리 구조를 사용합니다. `items > item`은 반복되는
`<item>` 요소가 됩니다. 변환에는 `xmltodict`를 사용하세요. 결과 dict는
JSON 형태를 따르지만, 단일 항목을 리스트 대신 dict로 반환할 가능성이
더 높습니다.

## 5. 페이지네이션

두 개의 파라미터를 사용하는 페이지 기반 방식입니다:

| 파라미터 | 기본값 | 설명 |
|---|---|---|
| `pageNo` | `1` | 1부터 시작하는 페이지 번호 |
| `numOfRows` | `10` | 페이지당 행 수 (최대값은 API마다 다름) |

어댑터는 기본값으로 충분해 보여도 **항상 페이지 파라미터를 명시적으로
전송해야** 동작이 결정적으로 유지됩니다.

### 중단 조건 (방어적)

어댑터는 다음 조건 중 **하나라도** 만족하면 페이지 순회를 멈춰야 합니다:

1. 정규화 후 반환된 item 리스트가 **비어 있음**
2. 반환된 item 수가 요청한 `numOfRows`보다 **작음**
   (짧은 페이지 = 마지막 페이지)
3. `pageNo * numOfRows >= totalCount` (참고용 상한)

`totalCount`는 **참고용 상한**으로만 사용하고, 유일한 종료 조건으로
쓰면 안 됩니다 — 일부 API는 오래되었거나 잘못된 건수를 반환합니다.

### 잘못된 envelope 처리

응답에 `response.header.resultCode`가 아예 없으면
`ProviderResponseError`를 발생시킵니다. JSON/XML 파싱이 실패하면
`ParseError`를 발생시킵니다.

## 6. 오류 코드

오류는 HTTP 상태 코드가 아니라 응답 envelope **안에**
들어옵니다 (대부분 오류여도 HTTP 200을 반환합니다).

| `resultCode` | `resultMsg` | 의미 |
|---|---|---|
| `"00"` | NORMAL SERVICE | 성공 |
| `"01"` | APPLICATION ERROR | 서버 측 애플리케이션 오류 |
| `"02"` | DB ERROR | 제공기관 측 데이터베이스 오류 |
| `"10"` | INVALID REQUEST PARAMETER | 잘못된 쿼리 파라미터 |
| `"12"` | NO OPEN API SERVICE ERROR | 서비스 ID를 찾을 수 없거나 비공개 상태 |
| `"20"` | SERVICE ACCESS DENIED ERROR | 이 API에 대해 키 권한이 없음 |
| `"22"` | 일일 트래픽 초과 | 일일 트래픽 할당량 초과 |
| `"30"` | KEY IS NOT REGISTERED | 유효하지 않거나 폐기된 키 |
| `"31"` | DEADLINE HAS EXPIRED | 키 유효기간 만료 |
| `"32"` | UNREGISTERED IP | 호출 IP가 화이트리스트에 없음 |

### KPubData 예외로의 매핑

| 코드 | KPubData 예외 | 비고 |
|---|---|---|
| `"30"`, `"31"`, `"20"`, `"32"` | `AuthError` | 세부 경우 구분은 `provider_code` 사용 |
| `"22"` | `RateLimitError` | `retryable=False` 설정 — 일일 할당량 소진으로, 일시적 스로틀링이 아님 |
| `"10"` | `InvalidRequestError` | |
| `"12"` | `DatasetNotFoundError` | 서비스/데이터셋을 찾지 못함 |
| `"01"`, `"02"` | `ServiceUnavailableError` | 상위 제공기관 장애, `retryable=True` |
| 잘못된 envelope | `ProviderResponseError` | `resultCode` 누락 또는 계약 위반 |
| 잘못된 JSON/XML | `ParseError` | 전송 계층 디코드 실패 |

## 7. 호출 제한

- 서비스 키별 일일 호출 할당량이 있습니다 (오류 코드 `"22"`).
- 할당량은 **데이터셋 및 계정별**로 다르며, 각 데이터셋의 포털 페이지에 표시됩니다.
  하나의 공통 제한값은 없습니다.
- `Retry-After` 헤더는 제공되지 않습니다. 코드 `"22"`가 오면
  어댑터는 `retryable=False`가 설정된 `RateLimitError`를 발생시킵니다 —
  일일 할당량 소진은 같은 날 안에 재시도해도 해결되지 않습니다.

## 8. 일반적인 쿼리 파라미터

| 파라미터 | 필수 여부 | 설명 |
|---|---|---|
| `serviceKey` | | API 키 |
| `pageNo` | (항상 전송) | 페이지 번호 (기본값 1) |
| `numOfRows` | (항상 전송) | 페이지 크기 (기본값 10) |
| `resultType` | | `json` 또는 `xml` (기본값 XML) |
| *dataset-specific* | varies | 검색 필터, 날짜 범위 등 |

## 9. 어댑터 설계에 주는 시사점

1. **카탈로그 엔드포인트 없음** — 데이터셋 탐색은 외부
   (포털 웹사이트)에서 이뤄집니다. `list_datasets`는 선별된 정적 목록을
   반환하거나 로컬 카탈로그 파일을 읽습니다.
2. **데이터셋별 base URL** — `DatasetRef.endpoint`에 저장합니다.
   오퍼레이션 결정은 데이터셋 메타데이터에서 오며, 경로를 하드코딩해
   구성하지 않습니다.
3. **JSON 우선** — 데이터셋이 지원하면 `resultType=json`을 전송합니다.
   JSON을 지원하지 않으면 전송 계층이 XML을 파싱하도록 둡니다.
4. **본문 내부 오류** — `body`를 처리하기 전에 `resultCode`를 확인합니다.
   HTTP 200이라고 성공을 의미하지는 않습니다.
5. **방어적 페이지 순회** — `query_records`는 §5의 중단 조건과 함께
   `pageNo` / `numOfRows`를 사용해 자동 페이지네이션해야 합니다.
6. **`call_raw`** — 임의의 파라미터를 그대로 전달하고
   **최소한만 가공한** 제공기관 응답 dict를 반환합니다. 평탄화하거나
   canonicalize하지 마세요 — raw 비상구를 보존하기 위함입니다.
7. **미지원 capability** — 데이터셋 메타데이터가 명시적으로 증명하지 않는 한
   `get_schema`는 기본적으로 **지원하지 않습니다**. 지원된다고 표시하지 마세요.
8. **item 정규화** — §4.3 설명대로 항상 `items.item`을 `list[dict]`로
   강제 변환합니다.

## 10. 참고 구현체

- [data-go-mcp-servers](https://github.com/Koomook/data-go-mcp-servers) —
  NPS, NTS, PPS data.go.kr API용 MCP 서버 래퍼입니다.
  인증, 페이지네이션, 오류 처리 패턴을 보여줍니다.
