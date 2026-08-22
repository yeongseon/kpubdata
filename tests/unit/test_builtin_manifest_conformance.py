"""builtin provider manifest와 Client resolve·지원 문서의 정합 검증 (#332).

SUPPORTED_DATA.md가 지원으로 표시한 provider는 builtin manifest에 등록되어
일반 ``Client()``에서 네트워크 호출 없이 dataset이 resolve되어야 한다 —
문서/Studio UI가 말하는 것과 runtime이 하는 것이 같은지를 잠근다.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from kpubdata.client import Client
from kpubdata.providers.manifest import BUILTIN_PROVIDERS

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SUPPORTED = _REPO_ROOT / "SUPPORTED_DATA.md"


def _supported_providers() -> set[str]:
    # 표 형식: | 지원 | 검증수준 | ... | 제공기관 (`provider`) | ...
    text = _SUPPORTED.read_text(encoding="utf-8")
    rows = [
        line
        for line in text.splitlines()
        if line.startswith("| 지원 |") or line.startswith("| 부분 지원 |")
    ]
    providers = set()
    for row in rows:
        match = re.search(r"\(`([a-z_]+)`\)", row)
        if match:
            providers.add(match.group(1))
    return providers


def test_every_supported_doc_provider_is_builtin() -> None:
    """지원 문서의 provider는 전부 builtin manifest에 등록되어 있다."""
    documented = _supported_providers()
    builtin = {name for name, _module, _cls in BUILTIN_PROVIDERS}
    missing = documented - builtin
    assert not missing, (
        f"SUPPORTED_DATA.md가 지원으로 표시했지만 builtin manifest에 없음: {sorted(missing)}"
    )


@pytest.mark.parametrize("provider", sorted(_supported_providers()))
def test_supported_provider_resolves_without_network(provider: str) -> None:
    """지원 표시 provider는 Client()에서 네트워크 없이 dataset resolve가 된다."""
    client = Client()
    entries = client.datasets.list(provider=provider)
    assert entries, f"provider {provider!r}에 dataset이 하나도 없다"

    dataset = client.dataset(f"{provider}.{entries[0].dataset_key}")
    assert dataset._ref.dataset_key == entries[0].dataset_key

    # 이슈 #332의 복제 시나리오: SGIS가 네트워크 없이 resolve되는지 직접 확인한다.
    if provider == "sgis":
        sgis = client.dataset("sgis.boundary.sido")
        assert sgis._ref.dataset_key == "boundary.sido"
