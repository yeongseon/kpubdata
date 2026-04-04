# KPubData 기여 가이드 (CONTRIBUTING.md)

KPubData 프로젝트에 관심을 가져주셔서 감사합니다! 이 프로젝트는 대학생을 포함한 모든 초보 개발자의 첫 기여를 환영합니다. 오픈소스 기여가 처음이라도 괜찮습니다. 이 가이드를 따라 차근차근 시작해 보세요.

## 1. 환영 인사 및 프로젝트 소개

KPubData는 공공데이터를 더 쉽고 표준화된 방식으로 다루기 위한 프로젝트 패밀리입니다.
- **kpubdata**: 핵심 라이브러리 (공공데이터 어댑터 엔진)
- **kpubdata-builder**: 데이터를 가공하고 내보내는 도구
- **kpubdata-studio**: 데이터를 시각화하고 관리하는 웹 대시보드

이 레포지토리(`kpubdata`)는 다양한 공공데이터 API를 하나의 표준 인터페이스로 연결하는 역할을 합니다.

## 2. 개발 환경 설정

Python 코드를 수정하고 테스트하기 위한 환경을 만들어 봅시다.

### Step 1: Python 설치
Python 3.10 버전 이상이 필요합니다. [Python 공식 홈페이지](https://www.python.org/downloads/)에서 설치하거나, `pyenv` 같은 도구를 사용하세요.

### Step 2: uv 설치
`uv`는 Python 패키지를 아주 빠르게 관리해 주는 도구입니다. 터미널(Terminal)을 열고 아래 명령어를 입력하세요.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Step 3: 프로젝트 가져오기 (Clone)
본인의 GitHub 계정으로 이 레포지토리를 **Fork**한 뒤, 내 컴퓨터로 가져옵니다.

```bash
git clone https://github.com/YOUR_USERNAME/kpubdata.git
cd kpubdata
```

### Step 4: 의존성 설치 및 확인
`uv`를 사용해 개발에 필요한 모든 라이브러리를 설치합니다.

```bash
# 필요한 패키지 설치
uv sync --extra dev

# 테스트 실행 (모든 기능이 잘 작동하는지 확인)
uv run pytest

# 코드 스타일 확인 (린트)
uv run ruff check .

# 타입 체크
uv run mypy src
```

## 3. Git 기초 워크플로

처음이라도 당황하지 마세요. 아래 순서대로 진행하면 됩니다.

1. **이슈 선택**: GitHub Issues 탭에서 `good first issue` 라벨이 붙은 이슈를 골라보세요.
2. **브랜치 만들기**: 작업할 주제에 맞춰 이름을 정합니다.
   - 예: `feat/issue-12-add-seoul-bus-adapter`
   - 예: `fix/issue-5-fix-typo`
3. **코드 수정 및 커밋**: 변경 사항을 기록합니다. 커밋 메시지는 간단하게 적으세요.
   - `feat: 서울시 버스 API 어댑터 추가`
   - `fix: 오타 수정`
4. **Push**: 내 GitHub 레포지토리로 올립니다.
   - `git push origin feat/issue-12-add-seoul-bus-adapter`
5. **Pull Request (PR) 보내기**: GitHub 웹사이트에서 "Compare & pull request" 버튼을 누릅니다.

## 4. 코딩 규칙 (Coding Convention)

우리는 깨끗한 코드를 유지하기 위해 몇 가지 규칙을 지킵니다.

- **타입 힌트**: 모든 함수에는 타입을 명시해야 합니다. `Any` 타입은 사용하지 않습니다.
- **문서화 (Docstring)**: 함수나 클래스가 무엇을 하는지 간단한 설명을 적어주세요.
- **포맷팅**: `uv run ruff format .` 명령어로 코드 스타일을 자동으로 맞출 수 있습니다.
- **Import**: 파일 맨 위에 `from __future__ import annotations`를 추가해 주세요.

## 5. 첫 번째 어댑터(Adapter) 추가하기

KPubData의 핵심은 새로운 데이터 소스를 연결하는 것입니다.

1. `src/kpubdata/adapters/` 폴더 아래에 새로운 파일을 만듭니다.
2. `PROVIDER_ADAPTER_CONTRACT.md` 문서를 읽고 표준 규격을 확인하세요.
3. `BaseAdapter` 클래스를 상속받아 `fetch()`와 `parse()` 메서드를 구현합니다.
4. `tests/` 폴더에 테스트 코드를 추가해 작동을 증명하세요.

## 6. PR 가이드 및 체크리스트

PR을 보낼 때 제목은 `[#이슈번호] 간단한 설명` 형식을 지켜주세요.

**보내기 전 체크리스트:**
- [ ] `uv run pytest` 결과가 모두 통과(Pass)인가요?
- [ ] `uv run ruff check .`에서 경고가 없나요?
- [ ] `uv run mypy src`에서 타입 오류가 없나요?

## 7. 도움 요청하기

모르는 것이 있다면 언제든 GitHub Issues에 질문을 남기세요. "이게 뭐죠?", "설치가 안 돼요" 같은 질문도 환영합니다. 누구나 처음은 어렵습니다. 함께 해결해 나가요!
