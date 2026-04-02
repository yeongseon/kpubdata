from __future__ import annotations

from kpubdata.exceptions import PublicDataError


def test_public_data_error_repr_includes_retryable_flag() -> None:
    error = PublicDataError("retry me", retryable=True)

    assert "retryable=True" in repr(error)
