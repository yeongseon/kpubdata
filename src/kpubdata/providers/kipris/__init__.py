"""KIPRIS(특허청) 특허정보 어댑터."""

from kpubdata.providers.kipris.adapter import KiprisAdapter

__all__ = ["KiprisAdapter"]

KIPRIS_CATALOGUE = [
    {
        "id": "patent_search",
        "name": "특허/실용신안 서지정보 검색",
        "description": "특허 및 실용신안의 서지정보 검색 (출원번호, 출원일자, 발명의 명칭 등)",
        "metadata": {
            "base_url": "http://plus.kipris.or.kr/openapi/service/patentBibliographyInfoService/getBibliographyInfo",
        },
    },
    {
        "id": "trademark_search",
        "name": "상표 출원/등록 정보 검색",
        "description": "상표 출원 및 등록 정보 검색 (상표번호, 출원일자, 등록일자 등)",
        "metadata": {
            "base_url": "http://plus.kipris.or.kr/openapi/service/trademarkInfoService/getTrademarkInfo",
        },
    },
    {
        "id": "design_search",
        "name": "디자인 출원/등록 정보 검색",
        "description": "디자인 출원 및 등록 정보 검색 (디자인번호, 출원일자, 등록일자 등)",
        "metadata": {
            "base_url": "http://plus.kipris.or.kr/openapi/service/designInfoService/getDesignInfo",
        },
    },
]