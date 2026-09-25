"""도달성 프로브 — 키 하나로 전 데이터셋을 분류하고 활용신청 목록을 만든다 (#499).

데이터셋 추가에서 **사람만 할 수 있는 단계는 data.go.kr 활용신청** 하나다. 그런데
어느 데이터셋이 신청을 기다리는지가 ``SUPPORTED_DATA.md`` 비고란 텍스트에만 있어서,
에이전트는 spec 작업을 시작한 **뒤에야** 403 으로 알게 된다. 되돌릴 작업을 먼저 하는
셈이다.

이 모듈은 그 판정을 앞으로 당긴다 — 데이터셋마다 1회 호출해 네 가지로 나눈다.

``ok``           호출된다
``auth-403``     활용신청 필요
``params-400``   필수 파라미터 미확인
``gone``         폐기·DNS·5xx

``batch_record.py`` 와 같은 fast-fail 전송 설정을 쓴다(timeout 15s·재시도 0) —
실패 데이터셋이 전체를 늦추지 않아야 하고, 여기서는 실패가 정상 결과다.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import Query
from kpubdata.core.spec import SpecDefinition, discover_specs, find_spec
from kpubdata.exceptions import (
    AuthError,
    DatasetNotFoundError,
    InvalidRequestError,
    PublicDataError,
    RateLimitError,
    ServiceUnavailableError,
    TransportError,
)
from kpubdata.transport.http import HttpTransport, TransportConfig

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT_PATH = REPO_ROOT / "docs" / "status" / "key-scope.json"

#: 프로브 전송 설정. 실패가 정상 결과이므로 빠르게 포기한다.
PROBE_TIMEOUT_SECONDS = 15
PROBE_RETRIES = 0

ProbeStatus = str  # "ok" | "auth-403" | "params-400" | "gone"


@dataclass(frozen=True)
class ProbeResult:
    """데이터셋 하나의 도달성 판정."""

    dataset_id: str
    service_id: str
    status: ProbeStatus
    probed_at: str
    detail: str = ""


def service_id_of(spec: SpecDefinition) -> str:
    """이 데이터셋이 속한 data.go.kr 서비스 식별자.

    ``base_url`` 의 마지막 경로 세그먼트다 — 활용신청은 **데이터셋이 아니라 서비스
    단위**로 한다. 예컨대 ``ArpltnInforInqireSvc`` 하나를 신청하면 대기질 관련
    데이터셋 셋이 함께 풀린다. 데이터셋 단위로 나열하면 세 번 신청해야 하는 것처럼
    보인다.
    """
    base_url = getattr(spec.endpoint, "base_url", "") or ""
    path = urlsplit(base_url).path.rstrip("/")
    return path.rsplit("/", 1)[-1] if path else ""


def classify(error: BaseException | None) -> tuple[ProbeStatus, str]:
    """호출 결과를 네 분류 중 하나로 옮긴다.

    상태 코드가 아니라 **예외 타입**으로 판정한다 — executor 가 provider envelope 을
    이미 표준 예외로 매핑해 두었으므로, 여기서 코드 표를 한 벌 더 들고 있을 이유가
    없다(그런 표는 갈라진다).
    """
    if error is None:
        return "ok", ""
    detail = f"{type(error).__name__}: {str(error)[:120]}"
    if isinstance(error, AuthError):
        return "auth-403", detail
    if isinstance(error, InvalidRequestError):
        return "params-400", detail
    # RateLimitError 를 TransportError 보다 **먼저** 본다. 전자가 후자의 하위라서
    # 순서를 뒤집으면 한도 초과가 gone 으로 분류된다 — 한도 초과는 "도달은 된다" 는
    # 뜻이므로 활용신청 대상이 아니다.
    if isinstance(error, RateLimitError):
        return "ok", detail
    if isinstance(error, (DatasetNotFoundError, ServiceUnavailableError)):
        return "gone", detail
    if isinstance(error, TransportError):
        # 403 이 AuthError 로 올라오지 않는 경로가 있으면 여기서 잡는다.
        if getattr(error, "status_code", None) == 403:
            return "auth-403", detail
        return "gone", detail
    return "gone", detail


def probe_dataset(
    dataset_id: str,
    *,
    config: KPubDataConfig | None = None,
    transport: HttpTransport | None = None,
) -> ProbeResult | None:
    """데이터셋 하나를 1회 호출해 분류한다. spec 이 없으면 None."""
    spec = find_spec(dataset_id)
    if spec is None:
        return None

    resolved_config = config or KPubDataConfig.from_env()
    resolved_transport = transport or HttpTransport(
        config=TransportConfig(timeout=PROBE_TIMEOUT_SECONDS, max_retries=PROBE_RETRIES, cache=None)
    )
    from kpubdata.core.executor import SpecExecutor

    executor = SpecExecutor(config=resolved_config, transport=resolved_transport)
    example = spec.examples[0] if spec.examples else None
    query = (
        Query(filters=dict(example.params), page=example.page, page_size=example.page_size)
        if example
        else Query()
    )

    error: BaseException | None = None
    try:
        _ = executor.query(spec, _ref_for(spec), query)
    except PublicDataError as exc:
        error = exc
    except Exception as exc:  # noqa: BLE001 — 프로브는 모든 실패를 분류해야 한다
        error = exc

    status, detail = classify(error)
    return ProbeResult(
        dataset_id=spec.id,
        service_id=service_id_of(spec),
        status=status,
        probed_at=datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        detail=detail,
    )


def _ref_for(spec: SpecDefinition) -> object:
    """executor 가 요구하는 최소 DatasetRef."""
    from kpubdata.core.models import DatasetRef, Representation

    return DatasetRef(
        id=spec.id,
        provider=spec.provider,
        dataset_key=spec.dataset_key,
        name=getattr(spec, "title", None) or spec.id,
        representation=Representation.API_JSON,
    )


def probe_all(
    *,
    provider: str | None = None,
    dataset_id: str | None = None,
    config: KPubDataConfig | None = None,
    transport: HttpTransport | None = None,
) -> list[ProbeResult]:
    """대상 데이터셋 전체를 프로브한다."""
    if dataset_id:
        one = probe_dataset(dataset_id, config=config, transport=transport)
        return [one] if one else []

    results: list[ProbeResult] = []
    for spec in discover_specs():
        if provider and spec.provider != provider:
            continue
        one = probe_dataset(spec.id, config=config, transport=transport)
        if one is not None:
            results.append(one)
    return results


def render_apply_report(results: list[ProbeResult]) -> str:
    """활용신청 체크리스트. **서비스 단위로 묶는다.**

    묶는 것이 이 보고서의 요점이다 — 데이터셋 단위로 나열하면 같은 서비스를 여러 번
    신청해야 하는 것처럼 보인다.
    """
    pending = [r for r in results if r.status == "auth-403"]
    if not pending:
        return "# 활용신청 대기\n\n없습니다.\n"

    groups: dict[str, list[ProbeResult]] = {}
    for result in pending:
        groups.setdefault(result.service_id, []).append(result)

    lines = [
        "# 활용신청 대기",
        "",
        f"서비스 {len(groups)}건을 신청하면 데이터셋 {len(pending)}종이 풀립니다.",
        "",
    ]
    for service, items in sorted(groups.items()):
        lines.append(f"## {service or '(서비스 식별 불가)'}")
        lines.append("")
        lines.append(
            f"- 데이터셋 {len(items)}종: " + ", ".join(sorted(i.dataset_id for i in items))
        )
        lines.append("- 신청: https://www.data.go.kr/ 에서 위 서비스명을 검색해 활용신청")
        lines.append("")
    return "\n".join(lines)


def write_report(results: list[ProbeResult], path: Path = DEFAULT_REPORT_PATH) -> Path:
    """프로브 결과를 JSON 으로 저장한다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "probed_at": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        "results": [asdict(r) for r in sorted(results, key=lambda r: r.dataset_id)],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def summarize(results: list[ProbeResult]) -> dict[str, int]:
    """분류별 개수."""
    counts: dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    return counts
