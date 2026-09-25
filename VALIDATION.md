# 아키텍처 검증

> 이 문서는 **2026년 초기 설계 시점의 검증 기록**이다. 그때 무엇을 근거로 무엇을
> 결정했는지를 남기는 것이 목적이며, 이후 구현에서 달라진 부분은
> [ADR](./docs/adrs/) 이 정본이다.

## 결론

현재 방향은 **한 가지를 다듬으면** 타당하다.

- 제품은 **기관(agency) 중심이 아니라 데이터셋(dataset) 중심**으로 유지한다
- 다만 현실은 **provider + dataset/service + representation + operation** 으로 모델링한다

이 구분이 중요한 이유는, 한국 공공데이터 포털이 메타데이터를 제공기관 단위로만
노출하지 않기 때문이다. 데이터셋/서비스 단위로도, 제공 형태(OpenAPI·파일·시트 등)
단위로도 노출한다.

## 무엇을 검증했나

### 1. dialect 기반 아키텍처가 잘 맞는다

SQLAlchemy 문서는 `Engine` 이 `Dialect` 와 `Pool` 을 함께 쓰고, dialect 구현이 DBAPI
고유 사항을 담당한다고 설명한다. 내부 구조 문서는 **데이터베이스마다 달라지는 것은
모두 dialect 개념에 속한다**고 못박는다. 이 비유가 유용한 이유는 KPubData 도 같은
모양이기 때문이다 — core 는 작게 두고 backend 고유 동작은 provider 어댑터로 민다.

여기에 잘 옮겨지는 이유:

- 공공데이터 provider 는 인증·파라미터 이름·전송 관례·응답 형식·결과 의미가 제각각이다
- 프레임워크는 접근 방식을 통일해야 하지만, **모든 backend 가 의미적으로 같은 척해서는 안 된다**

### 2. 데이터셋/서비스 중심이 기관 중심보다 정확하다

공공데이터포털은 제공기관·데이터명/설명·분류·데이터 타입 같은 메타데이터로 항목을
노출하고, 서비스를 유형(REST·SOAP·다운로드·LOD 등)으로도 분류한다. 서울 열린데이터
광장도 마찬가지이며, **하나의 서비스가 시트와 OpenAPI 두 표현을 함께 갖는 경우**를
명시적으로 보여준다.

따라서 주 추상은 "기관 클라이언트" 가 아니라 다음에 가까워야 한다.

- **provider**: 누가 소유·제공하는가
- **dataset/service**: 사용자가 원하는 것
- **representation**: 어떻게 노출되는가
- **operation**: 무엇을 할 수 있는가

### 3. 표준화할 것은 UX 이지 모든 native API 모양이 아니다

목표는 **일관된 파이썬 진입점**이지, 가짜 만능 파라미터 스키마가 아니다.

표준화 대상:

- `client.dataset(id)`
- `dataset.list(...)`
- `dataset.schema()`
- `dataset.call_raw(...)`

provider 고유 파라미터는 그대로 남아도 된다. 모든 API 를 하나의 완벽한 범용 필터
언어로 밀어 넣으면 새는(leaky) 데다 오해를 부르는 추상이 될 가능성이 높다.

### 4. raw 비상구가 필요하다

Requests 는 원시 바이트가 필요한 경우를 위해 `Response.raw` 를 명시적으로 문서화하고,
**디코딩된 내용은 원래 전송 payload 와 같지 않다**는 점을 함께 알린다. KPubData 도
raw 접근을 일급 기능으로 유지할 근거가 된다.

공공데이터 API 에서는 raw 접근이 더 중요하다.

- 문서가 실제 동작과 어긋나는 일이 잦다
- provider 가 **200 응답 본문 안에** 실패를 담아 보내는 경우가 있다
- 디버깅할 때 XML/JSON 차이가 실제로 문제가 된다

### 5. capability 기반 설계가 정직한 방법이다

모든 데이터셋이 같은 작업을 지원하지는 않는다. 질의 가능한 목록도 있고, 단건 조회만
되는 것도 있고, 파일 다운로드만 노출하는 것도 있고, 도메인 레코드가 아니라 메타데이터를
내보내는 것도 있다.

capability 모델은 그 차이를 **공개 API 를 쪼개지 않고** 명시하는 가장 깔끔한 방법이다.

## 최종 정의

> KPubData 는 한국 공공데이터를 위한 **provider 인식·데이터셋 중심·capability 기반**
> 파이썬 데이터 접근 프레임워크다. 작은 canonical 질의/결과 모델을 쓰고, 파이썬다운
> 편의 API 를 노출하며, **raw 비상구를 항상 남긴다.**

## 여전히 유효한 설계 결정

| 결정 | |
|---|---|
| 데이터셋 중심 공개 API | 예 |
| 작은 canonical `Query`·`RecordBatch` | 예 |
| capability 기반 지원 매트릭스 | 예 |
| raw 접근 경로 | 예 |
| SQLAlchemy 에서 빌려온 철학 | 예 |
| 모든 provider 가 하나의 참된 표준 API 를 공유하는 척하기 | **아니오** |

## 근거 문헌

위 검증은 다음 공식 문서를 대조해 확인했다.

- `Engine`·`Core`·`Dialect` 에 대한 SQLAlchemy 문서
- 공공데이터포털의 메타데이터·서비스 유형 페이지
- 서울 열린데이터광장 데이터셋 메타데이터
- raw 응답 처리에 대한 Requests 문서

### 링크

- SQLAlchemy 개요·dialect: https://docs.sqlalchemy.org/en/20/intro.html
- SQLAlchemy engine 설정: https://docs.sqlalchemy.org/en/latest/core/engines.html
- SQLAlchemy core 내부 구조 / dialect: https://docs.sqlalchemy.org/en/latest/core/internals.html
- 공공데이터포털 목록 API 메타데이터 예시: https://www.data.go.kr/data/15077093/openapi.do
- 공공데이터포털 서비스 유형 필터: https://www.data.go.kr/
- 서울 열린데이터광장 서비스 메타데이터 예시: https://data.seoul.go.kr/dataList/OA-2250/S/1/datasetView.do
- Requests raw 응답 문서: https://requests.readthedocs.io/en/latest/user/quickstart/

---

## 관련 문서

### 이 저장소 내 문서
| 문서 | 설명 |
| :--- | :--- |
| [API_SPEC.md](./API_SPEC.md) | 파이썬 API 명세 |
| [CANONICAL_MODEL.md](./CANONICAL_MODEL.md) | 표준 데이터 모델 정의 |
| [PROVIDER_ADAPTER_CONTRACT.md](./PROVIDER_ADAPTER_CONTRACT.md) | 어댑터 구현 규약 |
