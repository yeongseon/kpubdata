---
description: 기존 카탈로그 데이터셋을 spec으로 전환한다
subagent: dataset-builder
---
데이터셋 $ARGUMENTS 를 카탈로그에서 spec으로 전환한다.

1. `src/kpubdata/providers/{provider}/catalogue.json`의 해당 항목을 spec YAML로 이식
   (raw_metadata의 base_url/operation/service_key_param/format_param 등을 스키마 필드로)
2. `make record DATASET=<id>` — 기존 fixture 호환 여부 확인
3. 예제 스크립트 작성, `make verify` 통과
4. 카탈로그 항목 제거는 별도 PR에서 (컷오버는 관련 contract 테스트와 합의 후)
