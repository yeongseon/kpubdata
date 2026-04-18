from __future__ import annotations

import json
from typing import cast

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.providers.lofin.adapter import LofinAdapter
from kpubdata.transport.http import HttpTransport


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.headers: dict[str, str] = {"content-type": "application/json"}
        self.text: str = json.dumps(payload)
        self.content: bytes = self.text.encode()


class FakeTransport:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self._responses: list[FakeResponse] = list(responses)
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        return self._responses.pop(0)


def _success_payload(*, items: object, total_count: object) -> dict[str, object]:
    return {
        "AJGCF": [
            {
                "head": [
                    {"list_total_count": total_count},
                    {"RESULT": {"CODE": "INFO-000", "MESSAGE": "OK"}},
                ]
            },
            {"row": items},
        ]
    }


def _build_adapter_with_transport(
    responses: list[FakeResponse],
) -> tuple[LofinAdapter, DatasetRef, FakeTransport]:
    transport = FakeTransport(responses)
    adapter = LofinAdapter(
        config=KPubDataConfig(provider_keys={"lofin": "test-key"}),
        transport=cast(HttpTransport, cast(object, transport)),
    )
    dataset = adapter.get_dataset("expenditure_budget")
    return adapter, dataset, transport


def test_query_records_returns_single_page_and_sets_next_page() -> None:
    payload = _success_payload(items=[{"id": 1}, {"id": 2}], total_count=5)
    adapter, dataset, transport = _build_adapter_with_transport([FakeResponse(payload)])

    batch = adapter.query_records(dataset, Query(page=1, page_size=2))

    assert batch.items == [{"id": 1}, {"id": 2}]
    assert batch.total_count == 5
    assert batch.next_page == 2
    assert batch.raw == payload
    assert len(transport.calls) == 1


def test_query_records_uses_default_page_size_100() -> None:
    payload = _success_payload(items=[{"id": 1}], total_count=1)
    adapter, dataset, transport = _build_adapter_with_transport([FakeResponse(payload)])

    _ = adapter.query_records(dataset, Query())

    request_url = cast(str, transport.calls[0]["url"])
    assert "pSize=100" in request_url


def test_query_records_uses_heuristic_next_page_without_total_count() -> None:
    payload = _success_payload(items=[{"id": 1}, {"id": 2}], total_count=None)
    adapter, dataset, _ = _build_adapter_with_transport([FakeResponse(payload)])

    batch = adapter.query_records(dataset, Query(page=1, page_size=2))

    assert batch.total_count is None
    assert batch.next_page == 2


def test_transport_requirements_includes_ssl_context_factory() -> None:
    """LofinAdapter exposes transport_requirements with an SSL context factory."""
    reqs = LofinAdapter.transport_requirements
    assert reqs is not None
    assert reqs.ssl_context_factory is not None

    ctx = reqs.ssl_context_factory()
    import ssl

    assert isinstance(ctx, ssl.SSLContext)


def test_client_applies_lofin_ssl_context() -> None:
    """Client detects LofinAdapter.transport_requirements and builds custom transport."""
    from unittest.mock import patch

    from kpubdata.client import Client
    from kpubdata.transport.http import HttpTransport

    with patch.object(
        HttpTransport, "with_requirements", wraps=HttpTransport.with_requirements
    ) as spy:
        client = Client()
        _ = client.datasets.list()

    assert spy.call_count >= 1
    for call in spy.call_args_list:
        reqs = call[0][1] if len(call[0]) > 1 else call.kwargs.get("requirements")
        if reqs and reqs.ssl_context_factory is not None:
            return
    raise AssertionError(
        "HttpTransport.with_requirements was never called with ssl_context_factory"
    )
