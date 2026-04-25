from __future__ import annotations

import pytest

from kpubdata.client import Client
from kpubdata.core.models import RecordBatch


@pytest.mark.integration
@pytest.mark.usefixtures("require_sgis_key")
def test_boundary_sido_returns_record_batch(live_client: Client) -> None:
    ds = live_client.dataset("sgis.boundary.sido")

    result = ds.list()

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0


@pytest.mark.integration
@pytest.mark.usefixtures("require_sgis_key")
def test_boundary_sido_has_geometry(live_client: Client) -> None:
    ds = live_client.dataset("sgis.boundary.sido")
    result = ds.list()

    item = result.items[0]
    assert "geometry" in item or "adm_cd" in item


@pytest.mark.integration
@pytest.mark.usefixtures("require_sgis_key")
def test_boundary_sido_raw_returns_geojson(live_client: Client) -> None:
    ds = live_client.dataset("sgis.boundary.sido")

    raw = ds.call_raw("list")

    assert isinstance(raw, dict)
    assert "features" in raw


@pytest.mark.integration
@pytest.mark.usefixtures("require_sgis_key")
def test_boundary_sigungu_returns_record_batch(live_client: Client) -> None:
    ds = live_client.dataset("sgis.boundary.sigungu")

    result = ds.list()

    assert isinstance(result, RecordBatch)
    assert len(result.items) > 0


@pytest.mark.integration
@pytest.mark.usefixtures("require_sgis_key")
def test_boundary_sido_count_is_reasonable(live_client: Client) -> None:
    ds = live_client.dataset("sgis.boundary.sido")
    result = ds.list()

    assert 15 <= len(result.items) <= 20
