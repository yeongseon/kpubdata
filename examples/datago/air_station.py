"""datago.air_station 예제 — 측정소별 실시간 대기측정정보.

실행 모드:
- ``KPUBDATA_MODE=replay`` — 기록된 fixture로 결정적 실행(API 키 불필요)
- 미지정 — 실호출(``KPUBDATA_DATAGO_API_KEY`` 필요)

파라미터는 spec의 예제 ``baengnyeong_daily``와 동일하다.
계열 특이사항: items가 네이스트 배열로 온다(items_path = response.body.items).
"""

from __future__ import annotations

import os

from kpubdata import Client


def main() -> None:
    """백령도 측정소 일평균 측정정보 예제 조회를 실행한다."""
    api_key = os.environ.get("KPUBDATA_DATAGO_API_KEY", "replay-mode")
    client = Client(provider_keys={"datago": api_key}, cache=False)

    dataset = client.dataset("datago.air_station")
    batch = dataset.list(station="백령도", term="daily", page=1, page_size=10)

    # 의미 있는 검증: 측정 항목 구조 + 측정 시각 존재
    # pm25는 행에 따라 키 자체가 없는 선택 필드 — 필수 단언에서 제외(실측 함정)
    assert batch.items, "측정값이 최소 1건은 있어야 한다"
    first = batch.items[0]
    missing = {"dataTime", "pm10Value", "khaiValue"} - set(first)
    assert not missing, f"필수 측정 필드 누락: {sorted(missing)}"
    assert batch.total_count and batch.total_count > 0, "총건수가 보고되어야 한다"

    print(f"air_station 백령도(daily): {len(batch.items)}건 / 전체 {batch.total_count}건")
    pm25 = first.get("pm25Value", "N/A")  # 선택 필드
    print(
        f"최근 측정({first['dataTime']}): PM10={first['pm10Value']}, "
        f"PM2.5={pm25}, 통합대기={first['khaiValue']}"
    )


if __name__ == "__main__":
    main()
