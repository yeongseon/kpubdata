---
description: 드리프트 이슈/스모크 실패를 수리한다
subagent: drift-fixer
---
드리프트 $ARGUMENTS 를 수리한다.

절차는 `.opencode/agent/drift-fixer.md` 를 따른다. fixture는 반드시 `make record`로만 재생성하고,
spec-schema-gap으로 판명되면 needs-human 후 중단한다.
