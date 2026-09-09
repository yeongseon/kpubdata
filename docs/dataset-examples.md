# 데이터셋 예제

> 이 문서는 `examples/` 스크립트에서 자동 생성했다 (`scripts/gen_docs_examples.py`).
> 직접 편집하지 않는다 — 스크립트를 고치고 다시 생성한다.

각 예제는 `KPUBDATA_MODE=replay` 환경에서 API 키 없이 결정적으로 실행된다
(`make verify` 4단계). 실호출은 해당 Provider API 키 설정 후 그대로 실행하면 된다.


## datago


### `datago.apt_trade`

[소스](https://github.com/yeongseon/kpubdata/blob/main/examples/datago/apt_trade.py)

```python
"""datago.apt_trade 예제 — 아파트매매 실거래가 조회 (골든 예제: 페이지네이션).

실행 모드:
- ``KPUBDATA_MODE=replay`` — 기록된 fixture로 결정적 실행(API 키 불필요, CI/에이전트용)
- 미지정 — 실호출(``KPUBDATA_DATAGO_API_KEY`` 필요)

파라미터는 spec(``src/kpubdata/specs/datago/apt_trade.yaml``)의 예제
``seoul_gangnam_2024_01`` 와 동일하다 — replay가 fixture를 찾는 조건이다.
예제 파라미터를 바꾸려면 spec과 ``make record DATASET=datago.apt_trade`` 를 함께.
"""

from __future__ import annotations

import os

from kpubdata import Client


def main() -> None:
    """아파트매매 실거래가 예제 조회를 실행한다."""
    # replay 모드에서는 키 값이 매칭에 쓰이지 않으므로 더미로 대체할 수 있다.
    api_key = os.environ.get("KPUBDATA_DATAGO_API_KEY", "replay-mode")
    client = Client(provider_keys={"datago": api_key}, cache=False)

    dataset = client.dataset("datago.apt_trade")
    batch = dataset.list(LAWD_CD="11110", DEAL_YMD="202401", page=1, page_size=100)

    # 의미 있는 검증: 필수 필드 + 필터 준수(LAWD_CD=11110 강남) + 페이지네이션
    assert batch.items, "거래 데이터가 최소 1건은 있어야 한다"
    assert batch.total_count and batch.total_count > 0, "전체 건수(totalCount)가 보고되어야 한다"
    first = batch.items[0]
    missing = {"aptNm", "dealAmount", "dealYear", "sggCd"} - set(first)
    assert not missing, f"필수 필드 누락: {sorted(missing)}"
    구역외 = [
        item["sggCd"] for item in batch.items if not str(item.get("sggCd", "")).startswith("11110")
    ]
    assert not 구역외, f"LAWD_CD 필터 위반 항목: {구역외[:3]}"

    print(f"apt_trade 강남 2024-01: {len(batch.items)}건 / 전체 {batch.total_count}건")
    print(f"첫 거래: {first['umdNm']} {first['aptNm']} {first['dealAmount']}만원")


if __name__ == "__main__":
    main()
```


### `datago.hospital_info`

[소스](https://github.com/yeongseon/kpubdata/blob/main/examples/datago/hospital_info.py)

```python
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
```


### `datago.village_fcst`

[소스](https://github.com/yeongseon/kpubdata/blob/main/examples/datago/village_fcst.py)

```python
"""datago.village_fcst 예제 — 동네예보 조회 (골든 예제: XML 응답).

실행 모드:
- ``KPUBDATA_MODE=replay`` — 기록된 fixture로 결정적 실행(API 키 불필요)
- 미지정 — 실호출(``KPUBDATA_DATAGO_API_KEY`` 필요)

파라미터는 spec의 예제 ``seoul_default``(전일 23시 발표, 서울 격자)와 동일하다.
날짜가 오래되면 ``make record DATASET=datago.village_fcst`` 로 예제와 fixture를
갱신한다(기상청은 최근 발표만 응답).
"""

from __future__ import annotations

import os

from kpubdata import Client


def main() -> None:
    """동네예보 예제 조회를 실행한다."""
    api_key = os.environ.get("KPUBDATA_DATAGO_API_KEY", "replay-mode")
    client = Client(provider_keys={"datago": api_key}, cache=False)

    dataset = client.dataset("datago.village_fcst")
    batch = dataset.list(
        base_date="20260908", base_time="2300", nx=55, ny=127, page=1, page_size=100
    )

    # 의미 있는 검증: 예보 카테고리 구조
    assert batch.items, "예보 항목이 최소 1개는 있어야 한다"
    categories = {item.get("category") for item in batch.items}
    assert "TMP" in categories or "PCP" in categories, (
        f"기온/강수 카테고리 누락: {sorted(categories)}"
    )
    assert batch.total_count and batch.total_count > 0, "총 예보 항목수가 보고되어야 한다"

    온도 = next(
        (item.get("fcstValue") for item in batch.items if item.get("category") == "TMP"), None
    )
    print(f"village_fcst 서울(55,127): {len(batch.items)}항목 / 전체 {batch.total_count}항목")
    print(f"기온(TMP): {온도}℃")


if __name__ == "__main__":
    main()
```

