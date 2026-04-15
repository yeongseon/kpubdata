# 빠른 시작 가이드: 처음부터 끝까지

이 문서를 따라하면 KPubData를 설치하고, API 키를 설정하고, 실제 공공데이터를 조회하는 것까지 한 번에 완료할 수 있습니다.

## 필요한 것
- Python 3.10 이상 (확인: `python --version`)
- 인터넷 연결
- 공공데이터 API 키 (아래에서 발급 방법 안내)

## Step 1: Python 설치 확인
```bash
python --version
# Python 3.10.x 이상이면 OK
# 설치 안 되어 있다면: https://www.python.org/downloads/
```

## Step 2: KPubData 설치
```bash
pip install kpubdata
```
설치 확인:
```bash
python -c "import kpubdata; print('설치 성공!')"
# 설치 성공!
```

## Step 3: API 키 발급
가장 쉬운 한국은행(BOK) API부터 시작합니다.
1. https://ecos.bok.or.kr/api/ 접속
2. "인증키 신청" 클릭
3. 본인인증 후 회원가입
4. 마이페이지에서 발급된 키 확인 (예: `ABCD1234EFGH5678`)

## Step 4: API 키 설정
### macOS / Linux
```bash
export KPUBDATA_BOK_API_KEY="여기에-발급받은-키-붙여넣기"
```

### Windows (PowerShell)
```powershell
$env:KPUBDATA_BOK_API_KEY="여기에-발급받은-키-붙여넣기"
```

### Windows (명령 프롬프트)
```cmd
set KPUBDATA_BOK_API_KEY=여기에-발급받은-키-붙여넣기
```

설정 확인:
```bash
python -c "import os; print(os.environ.get('KPUBDATA_BOK_API_KEY', '설정 안됨'))"
# ABCD1234EFGH5678  ← 이런 식으로 키가 출력되면 OK
```

## Step 5: 첫 번째 데이터 조회
Python 파일을 하나 만들겠습니다.

```bash
# 작업 폴더 만들기
mkdir my-first-kpubdata
cd my-first-kpubdata
```

`first_query.py` 파일을 만들고 아래 내용을 붙여넣으세요:

```python
from kpubdata import Client

# 1. 클라이언트 생성 (환경변수에서 API 키 자동 로드)
client = Client.from_env()

# 2. 한국은행 기준금리 데이터셋 선택
ds = client.dataset("bok.base_rate")

# 3. 2024년 월별 기준금리 조회
result = ds.list(start_date="202401", end_date="202412")

# 4. 결과 출력
print(f"총 {len(result.items)}건의 데이터를 가져왔습니다.\n")

print("| 기간   | 기준금리 |")
print("|--------|----------|")
for item in result.items:
    print(f"| {item['TIME']} | {item['DATA_VALUE']}%   |")
```

실행:
```bash
python first_query.py
```

예상 출력:
```
총 12건의 데이터를 가져왔습니다.

| 기간   | 기준금리 |
|--------|----------|
| 202401 | 3.5%   |
| 202402 | 3.5%   |
| 202403 | 3.5%   |
| ...    |        |
| 202412 | 3.0%   |
```

## Step 6: 에러가 났을 때

### "API 키가 설정되지 않았습니다"
```
kpubdata.exceptions.AuthError: Provider key not configured for 'bok'
```
→ Step 4의 환경변수 설정을 다시 확인하세요. 터미널을 새로 열었다면 export 명령을 다시 실행해야 합니다.

### "날짜 형식 오류"
```
ProviderResponseError: BOK ECOS returned error
```
→ 날짜를 `"20240101"` 대신 `"202401"` (YYYYMM) 형식으로 입력했는지 확인하세요.

## Step 7: 다른 데이터도 조회해보기

### 사용 가능한 전체 데이터셋 목록 보기

```python
from kpubdata import Client

client = Client.from_env()

for ds in client.datasets.list():
    print(f"{ds.id} — {ds.name}")
```

출력 예시:
```
datago.village_fcst — 동네예보 조회서비스 (Village Forecast)
datago.ultra_srt_ncst — 초단기실황 조회서비스 (Ultra Short-term Nowcast)
datago.air_quality — 대기오염정보 조회서비스 (Air Quality)
datago.bus_arrival — 경기도 버스도착정보 조회서비스 (Bus Arrival)
datago.hospital_info — 병원정보서비스 (Hospital Information)
datago.apt_trade — 아파트매매 실거래자료 (Apartment Trade)
bok.base_rate — 한국은행 기준금리 (BOK Base Rate)
kosis.population_migration — 시도별 이동자수 (Population Migration)
```

### 다른 Provider 사용하려면
- 공공데이터포털(datago): [datago API 키 발급 가이드](./providers/datago.md)
- 통계청 KOSIS: [KOSIS API 키 발급 가이드](./providers/kosis.md)

## 다음 단계
- 각 Provider별 상세 사용법: [docs/providers/](./providers/) 폴더
- 프로젝트에 기여하기: [CONTRIBUTING.md](../CONTRIBUTING.md)
- 전체 API 명세: [API_SPEC.md](../API_SPEC.md)
