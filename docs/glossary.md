# KPubData 용어집

> 이 용어집은 KPubData 프로젝트의 문서를 읽기 전에 먼저 훑어보면 좋습니다.
> 대학교 2학년 수준의 파이썬 기초 지식을 전제로 작성되었습니다.

## 이 문서 읽는 법

KPubData 프로젝트 전체에서 반복적으로 등장하는 **비유 체계**가 있습니다. 이 비유를 먼저 기억해 두면 문서 읽기가 훨씬 수월합니다.

| 비유 | 실제 의미 |
|---|---|
| 🏛️ 도서관 | KPubData 시스템 전체 |
| 👤 사서 | `Client` — 사용자가 처음 만나는 입구 |
| 🗂️ 카탈로그 | `Catalog` — 사용 가능한 데이터셋 목록 |
| 📖 책 | `Dataset` — 실제 데이터의 집합 |
| 🗣️ 통역사 | `Adapter` — 기관마다 다른 API를 KPubData 표준으로 변환하는 코드 |
| 📬 우편 봉투 | `RecordBatch` — 데이터를 담아 돌려주는 표준 그릇 |
| 🗣️ 사투리 → 표준어 | `Dialect Architecture` — 기관 고유 방식을 표준으로 변환 |

각 용어에는 **한 줄 설명**, **비유**, 그리고 코드에서 찾을 수 있는 **위치**를 함께 적어 두었습니다.

---

## 핵심 개념

### Provider (제공 기관)

데이터를 제공하는 기관입니다. 예를 들어 [공공데이터포털(data.go.kr)](https://www.data.go.kr), 기상청, 서울열린데이터광장 등이 Provider입니다.

> 🏛️ 비유: 도서관에 책을 납품하는 **출판사**입니다. 각 출판사마다 책 표지 디자인이나 목차 형식이 다르듯, 각 기관마다 API 규격이 다릅니다.

- 📍 코드: `src/kpubdata/providers/` 디렉터리 안에 기관별 폴더가 있습니다.

### Client (클라이언트)

사용자가 KPubData를 사용할 때 가장 먼저 만드는 객체입니다. 모든 작업의 출발점이 됩니다.

> 🏛️ 비유: 도서관에 들어서면 처음 만나는 **안내 데스크의 사서**입니다. "어떤 데이터 찾으세요?" 하고 물어봐 주는 역할입니다.

```python
from kpubdata import Client
client = Client.from_env()  # 환경 변수에서 API 키를 읽어 클라이언트 생성
```

- 📍 코드: `src/kpubdata/client.py`
- 📖 참고: [API_SPEC.md](../API_SPEC.md)

### Catalog (카탈로그)

사용 가능한 데이터셋 목록을 관리하는 객체입니다. 어떤 데이터셋이 있는지 검색하고 찾을 수 있습니다.

> 🏛️ 비유: 도서관의 **도서 검색 시스템**입니다. 책 제목이나 키워드를 입력하면 어떤 책이 있는지 알려줍니다.

- 📍 코드: `src/kpubdata/catalog.py`

### Dataset (데이터셋)

실제 데이터의 집합입니다. 예를 들어 "동네예보", "대기오염정보", "버스도착정보" 등이 각각 하나의 Dataset입니다.

> 🏛️ 비유: 도서관에 있는 **개별 책** 한 권입니다. 책마다 주제와 내용이 다르듯, 데이터셋마다 담고 있는 데이터가 다릅니다.

- 📍 코드: `src/kpubdata/core/dataset.py`
- 📖 참고: [CANONICAL_MODEL.md](../CANONICAL_MODEL.md)

### Adapter (어댑터)

각 기관의 서로 다른 API 규칙을 KPubData 표준에 맞게 변환해주는 코드입니다.

> 🏛️ 비유: 외국어 책을 한국어로 바꿔주는 **통역사**입니다. 출판사(Provider)마다 다른 언어(API 규격)로 책을 쓰지만, 통역사가 모든 책을 같은 한국어(KPubData 표준)로 번역해 줍니다.

- 📍 코드: `src/kpubdata/providers/datago/adapter.py` (공공데이터포털 통역사)
- 📖 참고: [PROVIDER_ADAPTER_CONTRACT.md](../PROVIDER_ADAPTER_CONTRACT.md)

### call_raw (원본 호출)

어댑터의 표준 변환을 거치지 않고, 기관의 원본 API를 그대로 호출하는 기능입니다.

> 🏛️ 비유: 번역본을 읽다가 원문이 궁금할 때 열어보는 **원서 비상구**입니다. 평소에는 번역본(표준 결과)을 쓰지만, 원문 그대로 봐야 할 때가 있습니다.

```python
raw = ds.call_raw("getCtprvnRltmMesureDnsty", sidoName="서울")
```

- 📖 참고: [API_SPEC.md](../API_SPEC.md)

---

## 데이터 모델

### DatasetRef (데이터셋 참조)

특정 데이터셋을 **가리키는 주소 정보**입니다. "어떤 기관의 어떤 데이터셋인지"를 식별하는 이름표와 같습니다.

> 🏛️ 비유: 책의 **ISBN 번호** (고유 식별 코드)입니다. `"datago.village_fcst"`처럼 `기관.데이터셋이름` 형태입니다.

- 📍 코드: `src/kpubdata/core/models.py`

### Query (쿼리)

데이터를 찾기 위해 던지는 **검색 조건**입니다. "언제", "어디서", "몇 건" 같은 필터 조건을 담습니다.

> 🏛️ 비유: 도서관 검색창에 입력하는 **검색어와 필터**입니다. "2025년 4월 1일, 서울 강남구, 5건만" 같은 조건입니다.

- 📍 코드: `src/kpubdata/core/models.py`

### RecordBatch (레코드 배치)

검색 결과로 돌아온 **데이터 뭉치**입니다. 여러 개의 Record(개별 데이터 항목)를 담고 있습니다.

> 🏛️ 비유: 사서가 찾아다 준 **책 묶음** (검색 결과 목록)입니다. "총 10건 중 1~5번째 결과입니다"처럼 페이지 정보도 함께 가지고 있습니다.

```python
result = ds.list(base_date="20250401", nx="55", ny="127")
for item in result.items:  # items가 개별 Record들
    print(item)
```

- 📍 코드: `src/kpubdata/core/models.py`
- 📖 참고: [CANONICAL_MODEL.md](../CANONICAL_MODEL.md)

### Record (레코드)

RecordBatch 안에 들어있는 **개별 데이터 항목 하나**입니다.

> 🏛️ 비유: 책 묶음(RecordBatch) 안에 들어있는 **책 한 권**입니다.

### SchemaDescriptor (스키마 설명자)

데이터셋이 어떤 항목(필드)을 가지고 있는지 설명하는 **구조 정보**입니다.

> 🏛️ 비유: 책의 **목차**입니다. "이 데이터셋에는 온도, 습도, 풍속 항목이 있다"는 정보를 알려줍니다.

- 📍 코드: `src/kpubdata/core/models.py`

### FieldDescriptor (필드 설명자)

SchemaDescriptor 안에 들어가는 **개별 항목 하나의 설명**입니다. 항목 이름, 데이터 타입 등을 담습니다.

> 🏛️ 비유: 목차(Schema)에 적힌 **각 챕터의 제목과 설명**입니다. "온도 — 숫자, 섭씨 기준" 같은 정보입니다.

### Capability (기능 선언)

어댑터가 "나는 이런 기능을 할 수 있다/없다"고 **정직하게 선언**하는 정보입니다.

> 🏛️ 비유: 통역사의 **자격증 목록**입니다. "나는 목록 조회는 되지만 단건 조회는 못해요"처럼, 할 수 있는 것과 없는 것을 명확히 알려줍니다.

- 📍 코드: `src/kpubdata/core/capability.py`

### QuerySupport (쿼리 지원 정보)

어댑터가 어떤 검색 조건을 지원하는지 알려주는 정보입니다. Capability의 하위 개념입니다.

> 🏛️ 비유: "이 통역사는 **날짜별 검색은 되지만 지역별 검색은 안 됩니다**"라는 세부 능력 안내입니다.

- 📍 코드: `src/kpubdata/core/capability.py`

### Representation (표현 형식)

API 응답의 데이터 형식을 나타내는 [열거형(Enum)](https://docs.python.org/ko/3/library/enum.html)입니다. JSON 또는 XML 등이 있습니다.

> 🏛️ 비유: 책이 **한글판인지 영문판인지** (포맷)를 나타내는 구분입니다.

- 📍 코드: `src/kpubdata/core/representation.py`

### Envelope (봉투/래퍼)

API 응답에서 실제 데이터를 감싸고 있는 **바깥 구조**입니다. 보통 상태 코드, 에러 메시지, 페이지 정보 등이 들어있고, 그 안에 진짜 데이터가 담겨 있습니다.

> 🏛️ 비유: 편지(데이터)를 담고 있는 **우편 봉투**입니다. 봉투에는 보낸 사람, 우편번호(메타정보)가 적혀 있고, 안에 편지(데이터)가 들어있습니다.

### Pagination (페이지네이션)

데이터가 많을 때 한꺼번에 전부 보내지 않고 **나눠서 보내는 방식**입니다. 기관마다 `pageNo`, `numOfRows`, `startIndex` 등 방식이 제각각입니다.

> 🏛️ 비유: 검색 결과가 100건인데 한 화면에 10건씩 보여주는 **"1페이지, 2페이지, 3페이지…"** 기능입니다.

---

## 아키텍처 패턴

### Canonical Model (표준 모델)

기관마다 다른 데이터 형식을 **하나의 통일된 형태**로 정리한 모델입니다. DatasetRef, Query, RecordBatch 등이 여기에 해당합니다.

> 🏛️ 비유: 전 세계 어디서 보내든 규격이 같은 **국제 우편 봉투**입니다. 봉투 규격(Canonical Model)은 통일하되, 안에 들어가는 편지(데이터)는 자유입니다.

- 📖 참고: [CANONICAL_MODEL.md](../CANONICAL_MODEL.md)

### Dialect (방언) 아키텍처

핵심 기능(표준어)은 작고 안정적으로 유지하면서, 각 기관의 고유한 방식(사투리)은 전용 어댑터가 처리하는 설계 방식입니다.

> 🏛️ 비유: **표준어 ↔ 사투리 통역 시스템**입니다. 서울말(KPubData 표준)은 하나이지만, 부산 사투리(data.go.kr), 제주 사투리(서울시 API) 등을 각각의 통역사(Adapter)가 번역해 줍니다.

- 📖 참고: [ARCHITECTURE.md](../ARCHITECTURE.md), [ADR-0001](adrs/0001-dialect-inspired-architecture.md)

### Transport (전송 계층)

실제 HTTP 통신을 담당하는 계층입니다. 어댑터가 "이 주소로 이 데이터를 요청해줘"라고 하면, Transport가 실제로 인터넷을 통해 기관 서버와 통신합니다.

> 🏛️ 비유: 통역사가 외국 출판사에 전화를 거는 **전화기(통신 장비)**입니다. 통역사는 무슨 말을 할지 정하고, 전화기가 실제 통화를 담당합니다.

- 📍 코드: `src/kpubdata/transport/http.py`

### ProviderAdapter Protocol (제공기관 어댑터 프로토콜)

모든 어댑터가 반드시 구현해야 하는 **공통 규칙(인터페이스)**입니다. Python의 `typing.Protocol`을 사용합니다.

> 🏛️ 비유: 통역사 **자격 시험 기준**입니다. "목록 조회, 단건 조회, 원본 호출을 할 줄 알아야 통역사 자격이 있다"는 규칙입니다.

- 📍 코드: `src/kpubdata/core/protocol.py`
- 📖 참고: [PROVIDER_ADAPTER_CONTRACT.md](../PROVIDER_ADAPTER_CONTRACT.md)

---

## 테스트

### Fixture (픽스처)

테스트할 때 실제 API를 호출하는 대신 사용하는 **미리 저장해 둔 가짜 응답 데이터**입니다.

> 🏛️ 비유: 요리 수업에서 실제 장을 보러 가는 대신 미리 준비해 둔 **샘플 재료 세트**입니다. 테스트할 때마다 실제 API를 호출하면 느리고 불안정하므로, 한 번 저장해 둔 응답을 재사용합니다.

- 📍 코드: `tests/fixtures/` 디렉터리

### Contract Test (계약 테스트)

모든 어댑터가 KPubData의 **공통 규약(Contract)**을 잘 지키고 있는지 확인하는 테스트입니다.

> 🏛️ 비유: 모든 통역사가 같은 **자격 시험 문제**를 풀어보는 것입니다. 어떤 통역사든 "목록 조회를 하면 RecordBatch가 나와야 한다"는 동일한 기준으로 검증합니다.

- 📍 코드: `tests/contract/`
- 📖 참고: [PROVIDER_ADAPTER_CONTRACT.md](../PROVIDER_ADAPTER_CONTRACT.md)

---

## 개발 도구

### dataclass (데이터클래스)

파이썬에서 **데이터를 담는 클래스**를 간편하게 만들어주는 기능입니다. `@dataclass` 데코레이터를 붙이면 `__init__`, `__repr__` 등을 자동으로 만들어 줍니다.

```python
from dataclasses import dataclass

@dataclass
class Student:
    name: str     # 이름
    grade: int    # 학년

s = Student("김철수", 2)
print(s)  # Student(name='김철수', grade=2)
```

> 쉽게 말해: 매번 `__init__`을 손으로 쓰는 대신, "이 클래스는 이런 변수들을 가진다"고만 선언하면 나머지를 자동으로 채워주는 **편의 기능**입니다.

- 📖 참고: [Python 공식 문서 — dataclasses](https://docs.python.org/ko/3/library/dataclasses.html)

### typing.Protocol (타이핑 프로토콜)

"이 클래스는 이런 메서드를 가져야 한다"는 **규칙만 정의**하는 파이썬 기능입니다. Java의 Interface와 비슷하지만, 클래스가 명시적으로 상속하지 않아도 규칙만 맞으면 인정됩니다.

```python
from typing import Protocol

class Printable(Protocol):
    def print_info(self) -> str: ...  # 이 메서드만 있으면 OK

class Dog:
    def print_info(self) -> str:
        return "멍멍이"

# Dog은 Printable을 상속하지 않았지만, print_info가 있으므로 Printable로 인정됨
```

> 쉽게 말해: **"이 기능만 할 줄 알면 통과"**라는 느슨한 자격 기준입니다.

### MappingProxyType

파이썬의 딕셔너리(`dict`)를 **읽기 전용으로 감싸는** 래퍼입니다. 외부에서 값을 바꾸지 못하게 보호할 때 사용합니다.

> 쉽게 말해: 유리 케이스 안에 넣은 메뉴판입니다. 볼 수는 있지만 **수정은 못합니다**.

### httpx

KPubData가 HTTP 통신에 사용하는 파이썬 라이브러리입니다. `requests` 라이브러리와 비슷하지만 더 현대적입니다.

> 쉽게 말해: 인터넷으로 데이터를 주고받을 때 쓰는 **택배 회사**입니다.

- 📖 참고: [httpx 공식 문서](https://www.python-httpx.org/)

### uv

매우 빠른 파이썬 패키지 관리 도구입니다. `pip`과 같은 역할이지만 10~100배 빠릅니다.

> 쉽게 말해: `pip`의 **터보 버전**입니다. 이 프로젝트는 개발 환경을 `uv`로 관리합니다.

```bash
uv sync --extra dev    # 개발 의존성 포함하여 설치
uv run pytest          # uv 환경에서 테스트 실행
```

- 📖 참고: [uv 공식 문서](https://docs.astral.sh/uv/)

### ruff

파이썬 코드의 **스타일 검사(lint)와 자동 정리(format)**를 해주는 도구입니다.

> 쉽게 말해: 맞춤법 검사기입니다. 코드에서 일관되지 않은 스타일이나 잠재적 문제를 찾아줍니다.

```bash
uv run ruff check .        # 코드 스타일 검사
uv run ruff format --check .  # 포맷 검사
```

### mypy

파이썬 코드의 **타입(자료형)을 검사**하는 도구입니다. `str` 변수에 `int` 값을 넣으려 하면 에러를 알려줍니다.

> 쉽게 말해: "여기에 숫자를 넣겠다고 약속했는데 문자를 넣으려 한다"고 **미리 경고해 주는 감시자**입니다.

```bash
uv run mypy src  # src 폴더의 타입 검사
```

### pytest

파이썬에서 가장 널리 쓰이는 **테스트 실행 도구**입니다.

> 쉽게 말해: "내 코드가 제대로 작동하는지" 자동으로 확인해 주는 **시험 감독관**입니다.

```bash
uv run pytest  # 모든 테스트 실행
```

---

## 더 읽어보기

- [README.md](../README.md) — 프로젝트 전체 소개와 빠른 시작
- [ARCHITECTURE.md](../ARCHITECTURE.md) — 시스템 구조 상세 설명
- [CANONICAL_MODEL.md](../CANONICAL_MODEL.md) — 표준 데이터 모델 정의
- [PROVIDER_ADAPTER_CONTRACT.md](../PROVIDER_ADAPTER_CONTRACT.md) — 어댑터 구현 가이드
- [API_SPEC.md](../API_SPEC.md) — 파이썬 API 사용법
- [CONTRIBUTING.md](../CONTRIBUTING.md) — 프로젝트 기여 방법
- [초보자 튜토리얼](tutorials/quickstart-tutorial.md) — 처음 시작하는 분을 위한 단계별 안내
