# KPubData 기여 가이드 (CONTRIBUTING.md)

KPubData 프로젝트에 관심을 가져주셔서 감사합니다! 이 프로젝트는 대학생을 포함한 모든 초보 개발자의 첫 기여를 환영합니다. 오픈소스 기여가 처음이라도 괜찮습니다. 이 가이드를 따라 차근차근 시작해 보세요.

## 1. 환영 인사 및 프로젝트 소개

KPubData는 공공데이터를 더 쉽고 표준화된 방식으로 다루기 위한 프로젝트 패밀리입니다.
- **kpubdata**: 핵심 라이브러리 (공공데이터 어댑터 엔진)
- **kpubdata-builder**: 데이터를 가공하고 내보내는 도구
- **kpubdata-studio**: 데이터를 시각화하고 관리하는 웹 대시보드

이 레포지토리(`kpubdata`)는 다양한 공공데이터 API를 하나의 표준 인터페이스로 연결하는 역할을 합니다.

## 2. 개발 환경 설정 (처음부터 끝까지)

Python 코드를 수정하고 테스트하기 위한 환경을 만들어 봅시다.

**Step 1: 필수 도구 설치**
*   **Git 설치**: [git-scm.com](https://git-scm.com)에서 설치하세요. — 설치 확인: `git --version`
*   **Python 3.10+ 설치**: [Python 공식 홈페이지](https://www.python.org/downloads/)에서 설치하세요. — 설치 확인: `python --version`
*   **uv 설치**: `uv`는 Python 패키지를 아주 빠르게 관리해 주는 도구입니다. — 설치 확인: `uv --version`
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
*   **GitHub 계정 및 SSH 설정**: GitHub 계정이 필요합니다. [GitHub SSH 설정 가이드](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)를 참고해 내 컴퓨터와 연결하세요.

**Step 2: 프로젝트 Fork & Clone**
```bash
# 1. GitHub 웹에서 오른쪽 상단의 'Fork' 버튼을 클릭해 내 계정으로 복사합니다.

# 2. 내 컴퓨터로 가져오기 (YOUR_USERNAME 부분을 본인 아이디로 바꾸세요)
git clone https://github.com/YOUR_USERNAME/kpubdata.git
cd kpubdata

# 3. 원본 저장소를 upstream으로 등록 (나중에 최신 코드를 받기 위해)
git remote add upstream https://github.com/yeongseon/kpubdata.git
```

**Step 3: 개발 환경 구축**
터미널에서 아래 명령어를 순서대로 입력하세요.
```bash
uv sync --extra dev    # 필요한 패키지 모두 설치
uv run pytest          # 모든 테스트 통과 확인
uv run ruff check .    # 코드 스타일 확인
uv run mypy src        # 타입 체크
```
> 이 4개 명령어가 모두 성공하면 개발 준비 끝!

## 3. 브랜치 전략과 협업 규칙

규칙은 적지만, 반드시 지킵니다. 모르는 것이 있다면 언제든 물어보세요.

### 3-1. 브랜치(Branch)란?
브랜치는 원본 코드의 안전한 복사본에서 작업하는 것입니다. 내가 마음껏 코드를 수정해도 다른 사람의 작업이나 원본 코드에는 아무런 영향을 주지 않습니다. 작업이 완료되면 '합쳐달라'고 요청(Pull Request)하면 됩니다.

### 3-2. 브랜치 전략 (Git Graph)

```mermaid
gitgraph
    commit id: "initial"
    branch feat/issue-1-add-adapter
    checkout feat/issue-1-add-adapter
    commit id: "feat: add skeleton"
    commit id: "feat: implement parser"
    checkout main
    merge feat/issue-1-add-adapter id: "PR #1 merged"
    branch fix/issue-2-typo
    checkout fix/issue-2-typo
    commit id: "fix: typo in docs"
    checkout main
    merge fix/issue-2-typo id: "PR #2 merged"
```

### 3-3. 브랜치 이름 규칙
항상 목적에 맞는 접두사를 사용하세요.

| 접두사 | 용도 | 예시 |
| :--- | :--- | :--- |
| `feat/issue-<번호>-<설명>` | 새로운 기능 추가 | `feat/issue-12-add-bus-adapter` |
| `fix/issue-<번호>-<설명>` | 버그 수정 | `fix/issue-5-fix-xml-parse` |
| `docs/<설명>` | 문서 수정 (이슈 번호 생략 가능) | `docs/update-readme` |

### 3-4. 전체 작업 흐름 (Workflow)

```mermaid
flowchart TD
    A[1. GitHub에서 Fork] --> B[2. git clone]
    B --> C[3. git checkout -b feat/issue-번호-설명]
    C --> D[4. 코드 수정]
    D --> E[5. git add + git commit]
    E --> F{더 수정할 것?}
    F -->|Yes| D
    F -->|No| G[6. git push origin 브랜치이름]
    G --> H[7. GitHub에서 PR 생성]
    H --> I[8. 리뷰 & 머지]
```

**실제 터미널 명령어 순서:**

```bash
# 1. 원본 저장소에서 최신 코드를 받아옵니다
git checkout main
git pull upstream main

# 2. 새로운 작업 브랜치를 만듭니다
git checkout -b feat/issue-12-add-bus-adapter

# 3. 코드를 수정하고 변경 사항을 기록(커밋)합니다
git add .
git commit -m "feat: add bus arrival adapter skeleton"

# 4. 내 GitHub 저장소로 올립니다
git push origin feat/issue-12-add-bus-adapter

# 5. GitHub 웹사이트에서 'Compare & pull request' 버튼을 눌러 PR을 생성합니다.
```

### 3-5. 커밋 메시지 규칙
커밋 메시지는 '무엇을 왜 바꿨는지' 설명합니다.

| 접두사 | 의미 | 예시 |
| :--- | :--- | :--- |
| `feat:` | 새 기능 추가 | `feat: add air quality adapter` |
| `fix:` | 버그 수정 | `fix: handle empty XML response` |
| `docs:` | 문서 수정 | `docs: update API spec` |
| `test:` | 테스트 추가/수정 | `test: add parser unit tests` |
| `refactor:` | 리팩토링 (코드 구조 개선) | `refactor: simplify transport layer` |

### 3-6. 절대 금지 사항
- **`main` 브랜치에 직접 push 금지**: 모든 작업은 브랜치에서 진행하세요.
- **`git push --force` 금지**: 특히 `main` 브랜치나 공유 브랜치에는 절대 사용하지 마세요.
- **타인의 브랜치 건드리지 않기**: 내가 만들지 않은 브랜치를 삭제하거나 이름을 바꾸지 마세요.
- **모르면 물어보기**: 추측해서 실행하지 말고, 이슈나 채팅방에 질문하세요.

### 3-7. PR 올리기 전 최종 체크리스트
이 4가지 명령어가 모두 성공해야 PR이 승인될 수 있습니다.

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
```


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

---

## 관련 문서

### 이 저장소 내 문서
| 문서 | 설명 |
| :--- | :--- |
| [AGENTS.md](./AGENTS.md) | 에이전트 및 개발 규칙 가이드 |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 시스템 아키텍처 설계 |
| [ROADMAP.md](./ROADMAP.md) | 프로젝트 로드맵 및 단계별 계획 |
| [API_SPEC.md](./API_SPEC.md) | 파이썬 API 명세 |

### KPubData Product Family
| 저장소 | 문서 | 설명 |
| :--- | :--- | :--- |
| [kpubdata-builder](https://github.com/yeongseon/kpubdata-builder) | [CONTRIBUTING.md](https://github.com/yeongseon/kpubdata-builder/blob/main/CONTRIBUTING.md) | Builder 기여 가이드 |
| [kpubdata-studio](https://github.com/yeongseon/kpubdata-studio) | [CONTRIBUTING.md](https://github.com/yeongseon/kpubdata-studio/blob/main/CONTRIBUTING.md) | Studio 기여 가이드 |
