from __future__ import annotations

import pytest

from kpubdata.transport.retry import with_retry


def test_with_retry_rejects_negative_backoff_factor() -> None:
    with pytest.raises(ValueError, match="backoff_factor"):
        _ = with_retry(lambda: 1, backoff_factor=-0.1)


def test_with_retry_unreachable_state_raises_runtime_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import kpubdata.transport.retry as retry_module

    monkeypatch.setattr(retry_module, "range", lambda *_args: [], raising=False)

    with pytest.raises(RuntimeError, match="unreachable retry state"):
        _ = with_retry(lambda: 1)
