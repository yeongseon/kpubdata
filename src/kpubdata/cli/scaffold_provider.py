"""Generate boilerplate files for a new kpubdata provider adapter."""

from __future__ import annotations

import json
from pathlib import Path


def _init_template(class_name: str) -> str:
    return f'''"""{{name}} provider adapter package."""

from __future__ import annotations

from .adapter import {class_name}

__all__ = ["{class_name}"]
'''


def _adapter_template(name: str, class_name: str) -> str:
    return f'''"""{{name}} adapter with curated dataset catalogue."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import cast

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import (
    DatasetRef,
    Query,
    RecordBatch,
    SchemaDescriptor,
)
from kpubdata.core.protocol import ProviderAdapter
from kpubdata.exceptions import (
    DatasetNotFoundError,
)
from kpubdata.providers._common import load_catalogue
from kpubdata.transport.http import HttpTransport

logger = logging.getLogger("kpubdata.provider.{name}")


class {class_name}(ProviderAdapter):
    """Provider adapter for {name}."""

    def __init__(
        self,
        config: KPubDataConfig,
        transport: HttpTransport | None = None,
    ) -> None:
        self._config = config
        self._transport = transport or HttpTransport()
        self._catalogue = load_catalogue(Path(__file__).parent / "catalogue.json")
        self._datasets: dict[str, DatasetRef] = {{}}
        for entry in self._catalogue:
            key = entry["dataset_key"]
            self._datasets[key] = DatasetRef(
                id=f"{name}.{{key}}",
                provider="{name}",
                ops=entry.get("operations", ["list", "raw"]),
            )

    @property
    def name(self) -> str:
        return "{name}"

    def list_datasets(self) -> list[DatasetRef]:
        return list(self._datasets.values())

    def search_datasets(self, keyword: str) -> list[DatasetRef]:
        keyword_lower = keyword.lower()
        return [
            ds
            for ds in self._datasets.values()
            if keyword_lower in ds.id.lower()
        ]

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        if dataset_key not in self._datasets:
            raise DatasetNotFoundError(
                f"Dataset not found: {name}.{{dataset_key}}",
                provider="{name}",
                dataset_id=f"{name}.{{dataset_key}}",
            )
        return self._datasets[dataset_key]

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        # TODO: Implement actual API call logic
        raise NotImplementedError("query_records not yet implemented")

    def get_schema(self, dataset: DatasetRef) -> SchemaDescriptor | None:
        return None

    def call_raw(
        self, dataset: DatasetRef, operation: str, params: dict[str, object]
    ) -> object:
        # TODO: Implement raw API call logic
        raise NotImplementedError("call_raw not yet implemented")
'''


def _catalogue_template(dataset_key: str) -> str:
    catalogue = [
        {
            "dataset_key": dataset_key,
            "name": f"{dataset_key} dataset",
            "base_url": "https://example.com/api",
            "default_operation": "getData",
            "representation": "api_json",
            "description": f"TODO: describe {dataset_key}",
            "operations": ["list", "raw"],
            "query_support": {
                "pagination": "offset",
                "max_page_size": 1000,
            },
        }
    ]
    return json.dumps(catalogue, indent=2, ensure_ascii=False) + "\n"


def _unit_test_template(name: str, class_name: str) -> str:
    return f'''"""Unit tests for {name} adapter."""

from __future__ import annotations

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.exceptions import DatasetNotFoundError
from kpubdata.providers.{name}.adapter import {class_name}


def _build_adapter() -> {class_name}:
    config = KPubDataConfig(provider_keys={{"{name}": "test-key"}})
    return {class_name}(config=config)


class Test{class_name}:
    def test_name(self) -> None:
        adapter = _build_adapter()
        assert adapter.name == "{name}"

    def test_list_datasets_nonempty(self) -> None:
        adapter = _build_adapter()
        datasets = adapter.list_datasets()
        assert len(datasets) > 0
        assert all(isinstance(ds, DatasetRef) for ds in datasets)

    def test_get_dataset_valid(self) -> None:
        adapter = _build_adapter()
        datasets = adapter.list_datasets()
        first_key = datasets[0].dataset_key
        ds = adapter.get_dataset(first_key)
        assert isinstance(ds, DatasetRef)

    def test_get_dataset_invalid_raises(self) -> None:
        adapter = _build_adapter()
        with pytest.raises(DatasetNotFoundError):
            adapter.get_dataset("nonexistent_key_xyz")

    def test_all_datasets_have_provider(self) -> None:
        adapter = _build_adapter()
        for ds in adapter.list_datasets():
            assert ds.provider == "{name}"
'''


def _contract_test_template(name: str, class_name: str) -> str:
    return f'''"""Contract tests for {name} adapter."""

from __future__ import annotations

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.models import DatasetRef, Query
from kpubdata.providers.{name}.adapter import {class_name}
from tests.contract.provider_adapter import ProviderAdapterContract


def _build_adapter() -> {class_name}:
    config = KPubDataConfig(provider_keys={{"{name}": "test-key"}})
    return {class_name}(config=config)


class Test{class_name}Contract(ProviderAdapterContract):
    @pytest.fixture()
    def adapter(self) -> {class_name}:
        return _build_adapter()

    @pytest.fixture()
    def valid_dataset_key(self) -> str:
        # TODO: replace with actual dataset key from catalogue.json
        return "example_dataset"

    @pytest.fixture()
    def invalid_dataset_key(self) -> str:
        return "nonexistent_dataset_key_xyz"

    @pytest.fixture()
    def sample_dataset(self, adapter: {class_name}) -> DatasetRef:
        # TODO: replace with actual dataset key from catalogue.json
        return adapter.get_dataset("example_dataset")

    @pytest.fixture()
    def sample_query(self) -> Query:
        return Query()

    @pytest.fixture()
    def raw_operation(self) -> tuple[str, dict[str, object]]:
        # TODO: replace with actual operation name
        return ("getData", {{}})
'''


def _to_class_name(provider_name: str) -> str:
    """Convert provider name to PascalCase class name.

    Examples:
        "datago" -> "DatagoAdapter"
        "my_provider" -> "MyProviderAdapter"
        "seoul-open" -> "SeoulOpenAdapter"
    """
    parts = provider_name.replace("-", "_").split("_")
    pascal = "".join(part.capitalize() for part in parts)
    return f"{pascal}Adapter"


def scaffold_provider(
    provider_name: str,
    dataset_key: str = "example_dataset",
    project_root: Path | None = None,
) -> list[Path]:
    """Generate boilerplate files for a new provider adapter.

    Args:
        provider_name: Short identifier for the provider (e.g. "kosis", "ecos").
        dataset_key: Initial dataset key to include in catalogue.json.
        project_root: Root directory of the kpubdata project. Defaults to cwd.

    Returns:
        List of created file paths.
    """
    root = project_root or Path.cwd()
    class_name = _to_class_name(provider_name)

    provider_dir = root / "src" / "kpubdata" / "providers" / provider_name
    unit_test_dir = root / "tests" / "unit" / "providers" / provider_name
    contract_test_dir = root / "tests" / "contract"

    files: list[tuple[Path, str]] = [
        (provider_dir / "__init__.py", _init_template(class_name)),
        (provider_dir / "adapter.py", _adapter_template(provider_name, class_name)),
        (provider_dir / "catalogue.json", _catalogue_template(dataset_key)),
        (unit_test_dir / "__init__.py", ""),
        (unit_test_dir / "test_adapter.py", _unit_test_template(provider_name, class_name)),
        (
            contract_test_dir / f"test_{provider_name}.py",
            _contract_test_template(provider_name, class_name),
        ),
    ]

    created: list[Path] = []
    for path, content in files:
        if path.exists():
            print(f"  SKIP (exists): {path.relative_to(root)}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"  CREATED: {path.relative_to(root)}")
        created.append(path)

    return created


def main() -> None:
    """CLI entry point for provider scaffolding."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Scaffold a new kpubdata provider adapter",
    )
    parser.add_argument(
        "provider_name",
        help="Short identifier for the provider (e.g. kosis, ecos, seoul)",
    )
    parser.add_argument(
        "--dataset-key",
        default="example_dataset",
        help="Initial dataset key for catalogue.json (default: example_dataset)",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Project root directory (default: current directory)",
    )

    args = parser.parse_args()

    print(f"Scaffolding provider: {args.provider_name}")
    print()

    created = scaffold_provider(
        provider_name=args.provider_name,
        dataset_key=args.dataset_key,
        project_root=args.project_root,
    )

    print()
    if created:
        print(f"Done! {len(created)} file(s) created.")
        print()
        print("Next steps:")
        print(f"  1. Edit src/kpubdata/providers/{args.provider_name}/catalogue.json")
        print("     - Update dataset_key, name, base_url, default_operation")
        print("  2. Implement query_records() and call_raw() in adapter.py")
        print("  3. Update contract test fixtures (valid_dataset_key, sample_dataset, etc.)")
        print(f"  4. Run: uv run pytest tests/unit/providers/{args.provider_name} -q")
    else:
        print("No files created (all already exist).")


if __name__ == "__main__":
    main()
