"""국립국어원 언어 데이터 어댑터."""

from kpubdata.providers.korean.adapter import KoreanAdapter

__all__ = ["KoreanAdapter"]

KOREAN_CATALOGUE = [
    {
        "id": "dictionary_search",
        "name": "표준국어대사전 검색",
        "description": "표준국어대사전에서 단어, 용어, 문장 등을 검색하고 어휘 정보를 제공",
        "metadata": {
            "base_url": "https://stdict.korean.go.kr/api/search.do",
        },
    },
    {
        "id": "spell_check",
        "name": "한국어 맞춤법/문법 검사",
        "description": "한국어 맞춤법 및 문법 오류를 검사하고 교정 제안 제공",
        "metadata": {
            "base_url": "https://speller.cs.pusan.ac.kr/results",
        },
    },
    {
        "id": "opendict_search",
        "name": "우리말샘 오픈사전 검색",
        "description": "우리말샘 오픈사전에서 신조어, 유행어, 지역어 등을 검색",
        "metadata": {
            "base_url": "https://opendict.korean.go.kr/api/search.do",
        },
    },
]