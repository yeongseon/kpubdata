---
description: 데이터셋 하나를 spec 기반으로 추가한다 (완료 = make verify exit 0)
subagent: dataset-builder
---
dataset-request 이슈 #$ARGUMENTS 를 처리한다.

절차는 `.opencode/agent/dataset-builder.md` 와 AGENTS.md "데이터셋 추가 절차"를 따른다.
완료 조건은 `make verify DATASET=<id>` exit 0 이며, 그 전에 멈추지 않는다.
3회 실패 시 needs-human 라벨 + 요약 후 중단한다.
