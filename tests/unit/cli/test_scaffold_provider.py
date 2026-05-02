"""Unit tests for provider scaffolding tool."""

from __future__ import annotations

import json
from pathlib import Path

from kpubdata.cli.scaffold_provider import (
    _to_class_name,
    scaffold_provider,
)


class TestToClassName:
    def test_simple_name(self) -> None:
        assert _to_class_name("kosis") == "KosisAdapter"

    def test_underscore_name(self) -> None:
        assert _to_class_name("my_provider") == "MyProviderAdapter"

    def test_hyphen_name(self) -> None:
        assert _to_class_name("seoul-open") == "SeoulOpenAdapter"

    def test_single_char(self) -> None:
        assert _to_class_name("x") == "XAdapter"


class TestScaffoldProvider:
    def test_creates_all_files(self, tmp_path: Path) -> None:
        # Set up minimal project structure
        (tmp_path / "src" / "kpubdata" / "providers").mkdir(parents=True)
        (tmp_path / "tests" / "unit" / "providers").mkdir(parents=True)
        (tmp_path / "tests" / "contract").mkdir(parents=True)

        created = scaffold_provider(
            provider_name="testprov",
            dataset_key="my_dataset",
            project_root=tmp_path,
        )

        assert len(created) == 6

        # Verify provider source files
        provider_dir = tmp_path / "src" / "kpubdata" / "providers" / "testprov"
        assert (provider_dir / "__init__.py").exists()
        assert (provider_dir / "adapter.py").exists()
        assert (provider_dir / "catalogue.json").exists()

        # Verify test files
        unit_dir = tmp_path / "tests" / "unit" / "providers" / "testprov"
        assert (unit_dir / "__init__.py").exists()
        assert (unit_dir / "test_adapter.py").exists()

        contract_file = tmp_path / "tests" / "contract" / "test_testprov.py"
        assert contract_file.exists()

    def test_adapter_contains_class(self, tmp_path: Path) -> None:
        (tmp_path / "src" / "kpubdata" / "providers").mkdir(parents=True)
        (tmp_path / "tests" / "unit" / "providers").mkdir(parents=True)
        (tmp_path / "tests" / "contract").mkdir(parents=True)

        scaffold_provider("myprov", project_root=tmp_path)

        adapter_code = (
            tmp_path / "src" / "kpubdata" / "providers" / "myprov" / "adapter.py"
        ).read_text()
        assert "class MyprovAdapter" in adapter_code
        assert "ProviderAdapter" in adapter_code
        assert "def name(self)" in adapter_code

    def test_init_exports_adapter(self, tmp_path: Path) -> None:
        (tmp_path / "src" / "kpubdata" / "providers").mkdir(parents=True)
        (tmp_path / "tests" / "unit" / "providers").mkdir(parents=True)
        (tmp_path / "tests" / "contract").mkdir(parents=True)

        scaffold_provider("myprov", project_root=tmp_path)

        init_code = (
            tmp_path / "src" / "kpubdata" / "providers" / "myprov" / "__init__.py"
        ).read_text()
        assert "MyprovAdapter" in init_code

    def test_catalogue_valid_json(self, tmp_path: Path) -> None:
        (tmp_path / "src" / "kpubdata" / "providers").mkdir(parents=True)
        (tmp_path / "tests" / "unit" / "providers").mkdir(parents=True)
        (tmp_path / "tests" / "contract").mkdir(parents=True)

        scaffold_provider("myprov", dataset_key="weather", project_root=tmp_path)

        cat_path = tmp_path / "src" / "kpubdata" / "providers" / "myprov" / "catalogue.json"
        data = json.loads(cat_path.read_text())
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["dataset_key"] == "weather"

    def test_skip_existing_files(self, tmp_path: Path) -> None:
        (tmp_path / "src" / "kpubdata" / "providers").mkdir(parents=True)
        (tmp_path / "tests" / "unit" / "providers").mkdir(parents=True)
        (tmp_path / "tests" / "contract").mkdir(parents=True)

        first = scaffold_provider("myprov", project_root=tmp_path)
        second = scaffold_provider("myprov", project_root=tmp_path)

        assert len(first) == 6
        assert len(second) == 0

    def test_contract_test_inherits_base(self, tmp_path: Path) -> None:
        (tmp_path / "src" / "kpubdata" / "providers").mkdir(parents=True)
        (tmp_path / "tests" / "unit" / "providers").mkdir(parents=True)
        (tmp_path / "tests" / "contract").mkdir(parents=True)

        scaffold_provider("myprov", project_root=tmp_path)

        contract_code = (tmp_path / "tests" / "contract" / "test_myprov.py").read_text()
        assert "ProviderAdapterContract" in contract_code
        assert "TestMyprovAdapterContract" in contract_code
