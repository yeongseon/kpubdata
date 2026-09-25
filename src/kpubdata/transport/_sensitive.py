"""credential 로 취급할 파라미터·헤더 이름의 단일 정본.

같은 목록이 세 벌로 갈라져 있었다 — ``http.py`` 13개, ``cache.py`` 9개,
``replay.py`` 8개. 이름을 하나 추가할 때 세 곳을 모두 고쳐야 한다는 사실을
아무도 적어두지 않아서 실제로 어긋났고, 그 결과 ``cache.py`` 에는 sgis 의
``consumer_secret`` 이 빠졌다 — 목록에 없는 이름은 지문이 아니라 **원문 그대로**
캐시 키 재료가 된다.

이름은 부분 문자열이 아니라 정확히 일치로 판정한다. ``key`` 를 부분 문자열로
보면 ``district_code`` 같은 평범한 파라미터까지 가려져 로그가 쓸모없어진다.
"""

from __future__ import annotations

#: 소문자로 접은(casefold) 이름만 담는다. 비교하는 쪽도 casefold 한다.
SENSITIVE_PARAM_KEYS: frozenset[str] = frozenset(
    {
        "servicekey",
        "service_key",
        "api_key",
        "apikey",
        "token",
        "authorization",
        "secret",
        "password",
        "key",
        # law(국가법령정보)는 API 키를 "OC" 파라미터로 보낸다 — 이름만 봐서는
        # credential 로 보이지 않아 마스킹 목록에서 빠져 있었고, 예외 메시지에
        # 담긴 URL 에 키가 평문으로 남았다.
        "oc",
        # sgis(통계지리정보)는 OAuth 스타일 이름을 쓴다. 정확한 이름 목록이므로
        # 각각 등재해야 한다.
        "accesstoken",
        "consumer_key",
        "consumer_secret",
    }
)

__all__ = ["SENSITIVE_PARAM_KEYS"]
