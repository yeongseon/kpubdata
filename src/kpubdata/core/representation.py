"""소스/형태 모델링을 위한 데이터셋 표현 유형."""

from __future__ import annotations

from enum import Enum


class Representation(str, Enum):
    """접근 방식이 아니라 소스 형태 기준으로 데이터셋이 제공되는 방식을 설명한다."""

    API_JSON = "api_json"
    API_XML = "api_xml"
    FILE_CSV = "file_csv"
    FILE_EXCEL = "file_excel"
    SHEET = "sheet"
    OTHER = "other"


__all__ = ["Representation"]
