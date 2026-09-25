"""semas provider 어댑터.

data.go.kr 계열 공용 구현(:mod:`kpubdata.providers._datago_family`)을 그대로 쓴다 —
인증·envelope·페이지네이션 규약이 datago 와 같기 때문이다. 예전에는 localdata 와
semas 가 각각 375줄짜리 사본을 들고 있었고, 이름을 맞춰 비교하면 코드 차이가
0줄이었다. 그 중복 때문에 "03"(NODATA) 처리가 한쪽에만 들어가 #470 회귀가 났다.
"""

from __future__ import annotations

from kpubdata.providers._datago_family import DataGoFamilyAdapter


class SemasAdapter(DataGoFamilyAdapter):
    """semas 데이터셋 어댑터."""

    provider_name = "semas"
    catalogue_package = "kpubdata.providers.semas"


__all__ = ["SemasAdapter"]
