from __future__ import annotations

from types import MappingProxyType

import pytest

from kpubdata.core.models import DatasetRef
from kpubdata.core.representation import Representation
from kpubdata.exceptions import DatasetNotFoundError
from kpubdata.providers.datago.adapter import DataGoAdapter


class TestDataGoAdapter:
    def test_default_catalogue_loads(self) -> None:
        adapter = DataGoAdapter()

        datasets = adapter.list_datasets()
        assert datasets
        assert all(isinstance(dataset, DatasetRef) for dataset in datasets)

    def test_list_datasets_returns_copy(self) -> None:
        adapter = DataGoAdapter()

        first = adapter.list_datasets()
        second = adapter.list_datasets()

        assert first == second
        assert first is not second

    def test_list_datasets_all_datago_provider(self) -> None:
        adapter = DataGoAdapter()

        datasets = adapter.list_datasets()
        assert all(dataset.provider == "datago" for dataset in datasets)

    def test_list_datasets_ids_prefixed(self) -> None:
        adapter = DataGoAdapter()

        datasets = adapter.list_datasets()
        assert all(dataset.id.startswith("datago.") for dataset in datasets)

    def test_get_dataset_found(self) -> None:
        adapter = DataGoAdapter()

        dataset = adapter.get_dataset("village_fcst")
        assert dataset.id == "datago.village_fcst"
        assert dataset.dataset_key == "village_fcst"

    def test_get_dataset_not_found(self) -> None:
        adapter = DataGoAdapter()

        with pytest.raises(DatasetNotFoundError):
            _ = adapter.get_dataset("does_not_exist")

    def test_constructor_override_catalogue(self) -> None:
        custom_dataset = DatasetRef(
            id="datago.custom",
            provider="datago",
            dataset_key="custom",
            name="Custom Dataset",
            representation=Representation.API_JSON,
            operations=frozenset(),
            raw_metadata=MappingProxyType({"base_url": "https://example.test"}),
        )
        adapter = DataGoAdapter(catalogue=[custom_dataset])

        assert adapter.list_datasets() == [custom_dataset]

    def test_search_datasets_match(self) -> None:
        adapter = DataGoAdapter()

        results = adapter.search_datasets("forecast")
        assert results
        assert any(dataset.dataset_key == "village_fcst" for dataset in results)

    def test_search_datasets_no_match(self) -> None:
        adapter = DataGoAdapter()

        assert adapter.search_datasets("zzzzzz-not-a-dataset") == []

    def test_no_api_key_required_for_discovery(self) -> None:
        adapter = DataGoAdapter()

        datasets = adapter.list_datasets()
        assert datasets

        dataset = adapter.get_dataset("village_fcst")
        assert dataset.id == "datago.village_fcst"
