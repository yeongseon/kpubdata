"""KPubData Python 모듈.

이 파일은 ``src/kpubdata/providers/law/__init__.py`` 경로의 구현을 담는다.
주요 클래스와 함수는 공개 API, 전송 계층, Provider 어댑터 중 하나의 역할을 담당한다.
"""

from __future__ import annotations

from .adapter import LawAdapter

__all__ = ["LawAdapter"]
