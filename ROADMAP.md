# Roadmap — KPubData

```mermaid
timeline
    title KPubData 개발 로드맵
    v0.1 : 핵심 계약 확정 : 전송 계층 골격 : 3개 어댑터 구현 : XML/JSON 지원 : 탐색/조회/원본 호출
    v0.2 : 데이터셋 메타데이터 보강 : 플러그인 로딩 : 스키마 개선 : Pandas 어댑터 추가
    v0.3 : 경량 MCP 어댑터 : 어댑터 생성 도구 : 제공 기관 확대 : 탐색 기능 강화
    v1.0 : API 안정화 : 어댑터 계약 검증 완료 : 풍부한 문서 및 예제 : 버전 관리 체계 확립
```

## v0.1

Foundation release.

- finalize core contracts
- implement transport skeleton
- implement 3 distinct adapters
- support XML + JSON
- support discovery + list + raw
- ship docs and contract tests

## v0.2

Stabilization and ergonomics.

- dataset metadata enrichment
- plugin loading
- schema improvements
- pandas adapter
- more examples

## v0.3

Extensibility.

- thin MCP adapter
- provider scaffolding tools
- more provider coverage
- more robust discovery

## v1.0 criteria

- public API feels stable
- adapter contract proven across multiple provider families
- docs/examples sufficient for external users
- breakage policy and versioning discipline established

---

## 관련 문서

### 이 저장소 내 문서
| 문서 | 설명 |
| :--- | :--- |
| [PRD.md](./PRD.md) | 제품 요구사항 정의 |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 시스템 아키텍처 설계 |
| [API_SPEC.md](./API_SPEC.md) | 파이썬 API 명세 |

### KPubData Product Family
| 저장소 | 문서 | 설명 |
| :--- | :--- | :--- |
| [kpubdata-builder](https://github.com/yeongseon/kpubdata-builder) | [ROADMAP.md](https://github.com/yeongseon/kpubdata-builder/blob/main/ROADMAP.md) | Builder 로드맵 |
| [kpubdata-studio](https://github.com/yeongseon/kpubdata-studio) | [ROADMAP.md](https://github.com/yeongseon/kpubdata-studio/blob/main/ROADMAP.md) | Studio 로드맵 |
