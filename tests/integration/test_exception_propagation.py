from __future__ import annotations

import pytest

from kpubdata.client import Client
from kpubdata.core.capability import Operation
from kpubdata.core.models import DatasetRef, Query, RecordBatch
from kpubdata.core.representation import Representation
from kpubdata.exceptions import (
    AuthError,
    DatasetNotFoundError,
    ProviderNotRegisteredError,
    PublicDataError,
    RateLimitError,
    ServiceUnavailableError,
)


class ErrorAdapter:
    def __init__(self) -> None:
        self._datasets: dict[str, DatasetRef] = {
            "failing": DatasetRef(
                id="errorprov.failing",
                provider="errorprov",
                dataset_key="failing",
                name="Failing Dataset",
                representation=Representation.API_JSON,
                operations=frozenset({Operation.LIST, Operation.RAW}),
            ),
            "limited": DatasetRef(
                id="errorprov.limited",
                provider="errorprov",
                dataset_key="limited",
                name="Limited Dataset",
                representation=Representation.API_JSON,
                operations=frozenset({Operation.LIST, Operation.RAW}),
            ),
        }

    @property
    def name(self) -> str:
        return "errorprov"

    def list_datasets(self) -> list[DatasetRef]:
        return [self._datasets["failing"], self._datasets["limited"]]

    def search_datasets(self, text: str) -> list[DatasetRef]:
        _ = text
        return []

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        try:
            return self._datasets[dataset_key]
        except KeyError as exc:
            raise DatasetNotFoundError(
                f"Dataset not found: {self.name}.{dataset_key}",
                provider=self.name,
                dataset_id=f"{self.name}.{dataset_key}",
            ) from exc

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        _ = query
        raise AuthError(
            message="Invalid API key",
            provider="errorprov",
            dataset_id=dataset.id,
            operation="list",
            provider_code="30",
            retryable=False,
        )

    def get_schema(self, dataset: DatasetRef) -> None:
        raise ServiceUnavailableError(
            message="Service down",
            provider="errorprov",
            dataset_id=dataset.id,
            operation="schema",
            retryable=True,
        )

    def call_raw(self, dataset: DatasetRef, operation: str, params: dict[str, object]) -> object:
        _ = params
        raise RateLimitError(
            message="Too many requests",
            provider="errorprov",
            dataset_id=dataset.id,
            operation=operation,
            status_code=429,
            retryable=False,
        )


def _build_client() -> tuple[Client, ErrorAdapter]:
    client = Client(provider_keys={"errorprov": "bad-key"})
    adapter = ErrorAdapter()
    client.register_provider(adapter)
    return client, adapter


def test_auth_error_from_dataset_list() -> None:
    client, _adapter = _build_client()

    with pytest.raises(AuthError) as exc_info:
        _ = client.dataset("errorprov.failing").list()

    exc = exc_info.value
    assert exc.provider == "errorprov"
    assert exc.dataset_id == "errorprov.failing"
    assert exc.operation == "list"
    assert exc.provider_code == "30"
    assert exc.retryable is False


def test_auth_error_caught_as_base() -> None:
    client, _adapter = _build_client()

    try:
        _ = client.dataset("errorprov.failing").list()
        pytest.fail("Expected PublicDataError")
    except PublicDataError as exc:
        assert isinstance(exc, AuthError)


def test_rate_limit_from_call_raw() -> None:
    client, _adapter = _build_client()

    with pytest.raises(RateLimitError) as exc_info:
        _ = client.dataset("errorprov.failing").call_raw("getData")

    exc = exc_info.value
    assert exc.status_code == 429
    assert exc.retryable is False
    assert exc.operation == "getData"


def test_service_unavailable_from_schema() -> None:
    client, _adapter = _build_client()

    with pytest.raises(ServiceUnavailableError) as exc_info:
        _ = client.dataset("errorprov.failing").schema()

    exc = exc_info.value
    assert exc.retryable is True
    assert exc.operation == "schema"


def test_dataset_not_found() -> None:
    client, _adapter = _build_client()

    with pytest.raises(DatasetNotFoundError) as exc_info:
        _ = client.dataset("errorprov.nonexistent")

    assert exc_info.value.dataset_id == "errorprov.nonexistent"


def test_provider_not_registered() -> None:
    client = Client(provider_keys={"errorprov": "bad-key"})

    with pytest.raises(ProviderNotRegisteredError):
        _ = client.dataset("unknown.ds")


def test_auth_error_repr_includes_context() -> None:
    client, _adapter = _build_client()

    with pytest.raises(AuthError) as exc_info:
        _ = client.dataset("errorprov.failing").list()

    rendered = repr(exc_info.value)
    assert "errorprov" in rendered
    assert "30" in f"{rendered} {exc_info.value.provider_code}"


def test_rate_limit_repr_includes_status() -> None:
    client, _adapter = _build_client()

    with pytest.raises(RateLimitError) as exc_info:
        _ = client.dataset("errorprov.failing").call_raw("getData")

    assert "429" in repr(exc_info.value)


def test_dataset_not_found_has_cause_chain() -> None:
    client, _adapter = _build_client()

    with pytest.raises(DatasetNotFoundError) as exc_info:
        _ = client.dataset("errorprov.nonexistent")

    assert isinstance(exc_info.value.__cause__, KeyError)
