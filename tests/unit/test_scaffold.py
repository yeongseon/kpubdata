"""Provider scaffolding 도구 (#61)에 대한 단위 테스트.

scaffold_provider가 다음 파일 세트를 만들고, 만들어진 결과물이 실제로
adapter contract와 호환되는지(시드 데이터셋이 등록되고 list_datasets에
나타나는지)까지 확인한다.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from kpubdata.scaffold import scaffold_provider


def _shared_repo_root(tmp_path: Path) -> Path:
    """src/__init__.py 골격이 들어간 임시 repo root를 만들어 반환한다."""
    (tmp_path / "src" / "kpubdata" / "providers").mkdir(parents=True)
    (tmp_path / "tests" / "contract").mkdir(parents=True)
    (tmp_path / "tests" / "fixtures").mkdir(parents=True)
    return tmp_path


class TestScaffoldProvider:
    def test_creates_expected_file_set(self, tmp_path: Path) -> None:
        # scaffold가 적어도 adapter / __init__ / catalogue / fixture / contract test를 만든다.
        repo = _shared_repo_root(tmp_path)

        result = scaffold_provider("my_prov", repo_root=repo, dataset_key="sample")

        assert result.adapter_path.exists()
        assert result.init_path.exists()
        assert result.catalogue_path.exists()
        assert result.fixture_path.exists()
        assert result.contract_test_path.exists()
        assert set(result.created) >= {
            result.adapter_path,
            result.init_path,
            result.catalogue_path,
            result.fixture_path,
            result.contract_test_path,
        }

    def test_catalogue_seed_is_valid_json_with_dataset_key(self, tmp_path: Path) -> None:
        # 시드 catalogue는 파싱 가능하고 요청한 dataset_key를 가진다.
        repo = _shared_repo_root(tmp_path)

        result = scaffold_provider("my_prov", repo_root=repo, dataset_key="weather")

        entries = json.loads(result.catalogue_path.read_text(encoding="utf-8"))
        assert isinstance(entries, list) and entries
        assert entries[0]["dataset_key"] == "weather"
        assert "list" in entries[0]["operations"]
        assert "raw" in entries[0]["operations"]

    def test_init_exports_adapter_class_with_camel_case(self, tmp_path: Path) -> None:
        # __init__.py가 "MyProvAdapter" 형태의 클래스를 export한다.
        repo = _shared_repo_root(tmp_path)

        result = scaffold_provider("my_prov", repo_root=repo)

        init_text = result.init_path.read_text(encoding="utf-8")
        assert "MyProvAdapter" in init_text

    def test_generated_adapter_loads_and_lists_seed_dataset(self, tmp_path: Path) -> None:
        # 생성된 adapter.py를 spec_from_file_location으로 직접 로드해서,
        # list_datasets가 시드 dataset_key를 노출하는지 확인한다 — 스캐폴드
        # 결과가 adapter contract 일부(discovery)를 즉시 만족함을 보장한다.
        import importlib.util

        repo = _shared_repo_root(tmp_path)
        result = scaffold_provider("scaffolded_demo", repo_root=repo, dataset_key="demo_ds")

        spec = importlib.util.spec_from_file_location("_scaffold_demo_adapter", result.adapter_path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            adapter = module.ScaffoldedDemoAdapter()
            assert adapter.name == "scaffolded_demo"
            datasets = adapter.list_datasets()
            assert any(d.dataset_key == "demo_ds" for d in datasets)
            dataset = adapter.get_dataset("demo_ds")
            assert dataset.id == "scaffolded_demo.demo_ds"
        finally:
            sys.modules.pop("_scaffold_demo_adapter", None)

    def test_refuses_to_overwrite_existing_files_without_force(self, tmp_path: Path) -> None:
        repo = _shared_repo_root(tmp_path)
        scaffold_provider("dup_prov", repo_root=repo)

        with pytest.raises(FileExistsError, match="refusing to overwrite"):
            scaffold_provider("dup_prov", repo_root=repo)

    def test_force_replaces_existing_files(self, tmp_path: Path) -> None:
        repo = _shared_repo_root(tmp_path)
        first = scaffold_provider("dup_prov", repo_root=repo, dataset_key="first")
        # catalogue를 수정해 두고, force로 재생성하면 원래 시드로 돌아간다.
        first.catalogue_path.write_text("[]\n", encoding="utf-8")

        second = scaffold_provider("dup_prov", repo_root=repo, dataset_key="second", overwrite=True)

        entries = json.loads(second.catalogue_path.read_text(encoding="utf-8"))
        assert entries[0]["dataset_key"] == "second"

    def test_rejects_invalid_provider_name(self, tmp_path: Path) -> None:
        # 워크스페이스를 벗어나거나 파이썬 식별자가 아닌 이름은 거부.
        repo = _shared_repo_root(tmp_path)

        with pytest.raises(ValueError, match="provider name must match"):
            scaffold_provider("../escape", repo_root=repo)

    def test_rejects_invalid_dataset_key(self, tmp_path: Path) -> None:
        repo = _shared_repo_root(tmp_path)

        with pytest.raises(ValueError, match="dataset_key must match"):
            scaffold_provider("ok_name", repo_root=repo, dataset_key="Bad-Key")


class TestScaffoldCli:
    def test_cli_subcommand_creates_files(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # `kpubdata scaffold provider <name>` 가 동작하고 exit 0를 반환한다.
        from kpubdata.cli import main

        repo = _shared_repo_root(tmp_path)
        exit_code = main(
            [
                "scaffold",
                "provider",
                "cli_prov",
                "--dataset-key",
                "demo",
                "--repo-root",
                str(repo),
            ]
        )
        captured = capsys.readouterr()

        assert exit_code == 0
        assert "Scaffolded provider 'cli_prov'" in captured.out
        assert (repo / "src" / "kpubdata" / "providers" / "cli_prov" / "adapter.py").exists()

    def test_cli_reports_invalid_name_with_exit_one(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from kpubdata.cli import main

        repo = _shared_repo_root(tmp_path)
        exit_code = main(["scaffold", "provider", "Bad-Name", "--repo-root", str(repo)])
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "scaffold failed" in captured.err
