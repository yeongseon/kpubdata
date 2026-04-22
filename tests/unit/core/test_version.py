"""Regression test: kpubdata.__version__ must track package metadata."""

from importlib.metadata import version

import kpubdata


def test_version_matches_metadata() -> None:
    """Ensure __version__ equals importlib.metadata version (issue #127)."""
    assert kpubdata.__version__ == version("kpubdata")
