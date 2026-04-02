"""Dataset representation types for source/shape modeling."""

from __future__ import annotations

from enum import Enum


class Representation(str, Enum):
    """How a dataset is provisioned: source shape rather than access mode."""

    API_JSON = "api_json"
    API_XML = "api_xml"
    FILE_CSV = "file_csv"
    FILE_EXCEL = "file_excel"
    SHEET = "sheet"
    OTHER = "other"


__all__ = ["Representation"]
