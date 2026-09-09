"""datago.hospital_info 예제 — 병원정보서비스 조회 (골든 예제: 단순).

실행 모드:
- ``KPUBDATA_MODE=replay`` — 기록된 fixture로 결정적 실행(API 키 불필요)
- 미지정 — 실호출(``KPUBDATA_DATAGO_API_KEY`` 필요)

파라미터는 spec의 예제 ``default``(필수 필터 없음, 10건)와 동일하다.
"""

from __future__ import annotations

import os

from kpubdata import Client


def main() -> None:
    """병원 기본정보 예제 조회를 실행한다."""
    api_key = os.environ.get("KPUBDATA_DATAGO_API_KEY", "replay-mode")
    client = Client(provider_keys={"datago": api_key}, cache=False)

    dataset = client.dataset("datago.hospital_info")
    batch = dataset.list(page=1, page_size=10)

    # 의미 있는 검증: 필수 필터가 없어도 구조는 온전해야 한다
    assert batch.items, "병원 데이터가 최소 1건은 있어야 한다"
    assert batch.total_count and batch.total_count > 0, "전국 병원 총건수가 보고되어야 한다"
    first = batch.items[0]
    assert "병원명" in first or "yadmNm" in first, f"병원명 필드 누락: {sorted(first)[:8]}"

    print(f"hospital_info: {len(batch.items)}건 / 전체 {batch.total_count:,}건")
    이름후보 = first.get("병원명") or first.get("yadmNm")
    print(f"첫 병원: {이름후보} ({first.get('시도명', first.get('sidoCdNm', '?'))})")


if __name__ == "__main__":
    main()
