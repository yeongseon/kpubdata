"""새 Provider 어댑터를 위한 스캐폴딩 도구 (#61).

이 모듈은 새 Provider 어댑터를 추가할 때 필요한 최소 파일 묶음을 자동으로
생성한다. 핵심은 PROVIDER_ADAPTER_CONTRACT.md / AGENTS.md의 규칙을 따르는
정직한 skeleton — 동작하는 placeholder 어댑터 + catalogue + fixture +
contract test — 을 한 번에 만들어주어 첫 PR을 작성하기 위한 시작 비용을
없애는 데 있다.

주요 함수:
    - scaffold_provider: 지정된 이름의 Provider skeleton을 디스크에 생성한다.
"""

from __future__ import annotations

import json
import keyword
import re
from dataclasses import dataclass
from pathlib import Path

_PROVIDER_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
_DATASET_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class ScaffoldResult:
    """스캐폴딩이 만든 파일 경로의 결과 객체.

    속성:
        provider_dir: src/kpubdata/providers/<name>/ 디렉터리.
        adapter_path: provider 어댑터 모듈 경로.
        init_path: provider 패키지 __init__.py 경로.
        catalogue_path: catalogue.json 경로.
        fixture_dir: tests/fixtures/<name>/ 디렉터리.
        fixture_path: 샘플 fixture JSON 경로.
        contract_test_path: tests/contract/test_<name>.py 경로.
        created: 새로 만든 파일 경로 목록.
    """

    provider_dir: Path
    adapter_path: Path
    init_path: Path
    catalogue_path: Path
    fixture_dir: Path
    fixture_path: Path
    contract_test_path: Path
    created: tuple[Path, ...]


def _validate_provider_name(name: str) -> None:
    """워크스페이스를 벗어날 수 있거나 파이썬 식별자가 아닌 이름을 거부한다.

    파이썬 예약어(``class``, ``import`` 등)는 import/from 문에서 SyntaxError가
    나므로 정규식 통과 여부와 무관하게 별도로 거부한다.
    """
    if not _PROVIDER_NAME_PATTERN.match(name):
        raise ValueError(
            f"provider name must match {_PROVIDER_NAME_PATTERN.pattern!r}, got {name!r}. "
            "Use lowercase ASCII letters, digits, underscore; start with a letter."
        )
    if keyword.iskeyword(name) or keyword.issoftkeyword(name):
        raise ValueError(
            f"provider name must not be a Python keyword, got {name!r}. "
            "Generated `from kpubdata.providers.<name>` would fail to parse."
        )


def _validate_dataset_key(key: str) -> None:
    """비ASCII나 식별자가 아닌 dataset_key를 거부한다.

    dataset_key는 테스트 함수 이름(``test_<provider>_seed_dataset_*``)의 일부로도
    재사용될 수 있어 파이썬 예약어를 명시적으로 거부한다.
    """
    if not _DATASET_KEY_PATTERN.match(key):
        raise ValueError(
            f"dataset_key must match {_DATASET_KEY_PATTERN.pattern!r}, got {key!r}. "
            "Use lowercase ASCII letters, digits, underscore; start with a letter."
        )
    if keyword.iskeyword(key) or keyword.issoftkeyword(key):
        raise ValueError(f"dataset_key must not be a Python keyword, got {key!r}.")


def _adapter_module(provider_name: str, dataset_key: str) -> str:
    """provider adapter 모듈 본문을 문자열로 반환한다."""
    class_name = "".join(part.capitalize() for part in provider_name.split("_")) + "Adapter"
    return f'''"""{provider_name} provider 어댑터 (TODO: 한 줄 설명).

PROVIDER_ADAPTER_CONTRACT.md의 책임을 따르는 skeleton — 실제 backend 호출은
구현해야 한다(예: HTTP transport 호출, native 응답을 정규 RecordBatch로 변환).
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from kpubdata.core.models import (
    DatasetRef,
    Query,
    RecordBatch,
    SchemaDescriptor,
)
from kpubdata.exceptions import DatasetNotFoundError, InvalidRequestError
from kpubdata.providers._common import build_dataset_ref, load_catalogue


_CATALOGUE_PATH = Path(__file__).parent / "catalogue.json"


def _load_default_catalogue() -> tuple[DatasetRef, ...]:
    """이 provider 패키지의 catalogue.json을 DatasetRef 튜플로 로드한다.

    설치된 패키지에서는 ``importlib.resources`` 기반의 ``load_catalogue``를
    사용하고(zip wheel 등에서도 동작), 그 경로가 실패하면(예: 스캐폴드 직후
    아직 패키지가 import되기 전, 또는 spec_from_file_location으로 standalone
    로드된 경우) ``__file__`` 기준 파일시스템 읽기로 폴백한다.
    """
    try:
        return load_catalogue("kpubdata.providers.{provider_name}", "{provider_name}")
    except (ModuleNotFoundError, FileNotFoundError):
        raw = json.loads(_CATALOGUE_PATH.read_text(encoding="utf-8"))
        return tuple(build_dataset_ref("{provider_name}", entry) for entry in raw)


class {class_name}:
    """{provider_name} Provider 어댑터.

    이 skeleton은 datasets discovery만 동작한다. query_records/call_raw 등
    실제 fetch 로직은 backend 명세에 맞춰 채워야 한다.
    """

    requires_api_key: bool = True  # TODO: backend가 무인증이면 False로 변경.

    def __init__(self, *, catalogue: Sequence[DatasetRef] | None = None) -> None:
        """provider catalogue를 로드한다(테스트에서는 catalogue를 주입할 수 있다)."""
        self._datasets: tuple[DatasetRef, ...] = (
            tuple(catalogue) if catalogue is not None else _load_default_catalogue()
        )
        self._datasets_by_key: dict[str, DatasetRef] = {{
            d.dataset_key: d for d in self._datasets
        }}

    @property
    def name(self) -> str:
        """정규 Provider 키."""
        return "{provider_name}"

    def list_datasets(self) -> list[DatasetRef]:
        """이 Provider에서 탐색 가능한 데이터셋."""
        return list(self._datasets)

    def search_datasets(self, text: str) -> list[DatasetRef]:
        """텍스트로 데이터셋을 검색한다(이름/id casefold 매치)."""
        needle = text.casefold()
        return [
            d for d in self._datasets
            if needle in d.id.casefold() or needle in d.name.casefold()
        ]

    def get_dataset(self, dataset_key: str) -> DatasetRef:
        """Provider 로컬 dataset_key를 DatasetRef로 해석한다."""
        dataset = self._datasets_by_key.get(dataset_key)
        if dataset is not None:
            return dataset
        raise DatasetNotFoundError(
            f"Dataset not found: {provider_name}.{{dataset_key}}",
            provider="{provider_name}",
            dataset_id=f"{provider_name}.{{dataset_key}}",
        )

    def query_records(self, dataset: DatasetRef, query: Query) -> RecordBatch:
        """정규 list/query 호출. TODO: 실제 backend 호출 구현."""
        raise InvalidRequestError(
            "query_records is not implemented yet — fill in backend logic.",
            provider="{provider_name}",
            dataset_id=dataset.id,
        )

    def get_schema(self, dataset: DatasetRef) -> SchemaDescriptor | None:
        """선택적 스키마 메타데이터(미지원이면 None)."""
        return None

    def call_raw(
        self, dataset: DatasetRef, operation: str, params: dict[str, object]
    ) -> object:
        """raw 비상구. TODO: backend의 원본 응답을 그대로 반환하도록 구현."""
        raise InvalidRequestError(
            "call_raw is not implemented yet — fill in backend logic.",
            provider="{provider_name}",
            dataset_id=dataset.id,
        )


__all__ = ["{class_name}"]
'''


def _init_module(provider_name: str) -> str:
    """provider 패키지 __init__.py 본문."""
    class_name = "".join(part.capitalize() for part in provider_name.split("_")) + "Adapter"
    return (
        f'"""{provider_name} Provider 어댑터 패키지."""\n\n'
        f"from __future__ import annotations\n\n"
        f"from .adapter import {class_name}\n\n"
        f'__all__ = ["{class_name}"]\n'
    )


def _catalogue_seed(provider_name: str, dataset_key: str) -> str:
    """초기 catalogue.json 본문(샘플 데이터셋 1개)."""
    entry = {
        "dataset_key": dataset_key,
        "name": f"{provider_name} {dataset_key} sample (TODO: 실명으로 교체)",
        "base_url": "https://example.invalid/api",
        "default_operation": "list",
        "representation": "api_json",
        "service_key_param": "serviceKey",
        "format_param": "type",
        "description": "TODO: backend 데이터셋 설명을 채워주세요.",
        "tags": [provider_name],
        "source_url": "https://example.invalid/dataset",
        "operations": ["list", "raw"],
        "query_support": {"pagination": "offset", "max_page_size": 100},
    }
    return json.dumps([entry], indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def _fixture_seed(dataset_key: str) -> str:
    """샘플 success fixture(합성 placeholder)."""
    payload = {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
            "body": {
                "items": {
                    "item": [
                        {"id": "1", "name": f"sample {dataset_key} record"},
                    ],
                },
                "numOfRows": 1,
                "pageNo": 1,
                "totalCount": 1,
            },
        },
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def _contract_test(provider_name: str, dataset_key: str) -> str:
    """tests/contract/test_<name>.py skeleton — discovery까지 동작."""
    class_name = "".join(part.capitalize() for part in provider_name.split("_")) + "Adapter"
    return f'''"""{provider_name} provider contract test (skeleton).

query_records 등 backend 호출이 구현되면 해당 시나리오 테스트를 채워야 한다.
"""

from __future__ import annotations

from kpubdata.core.capability import Operation
from kpubdata.providers.{provider_name} import {class_name}


def _adapter() -> {class_name}:
    """테스트용 어댑터 인스턴스를 생성한다."""
    return {class_name}()


def test_{provider_name}_adapter_name() -> None:
    """Provider 이름이 정규 키와 일치한다."""
    assert _adapter().name == "{provider_name}"


def test_{provider_name}_lists_seed_dataset() -> None:
    """catalogue.json의 시드 데이터셋이 list_datasets에 노출된다."""
    datasets = _adapter().list_datasets()
    assert any(d.dataset_key == "{dataset_key}" for d in datasets)


def test_{provider_name}_seed_dataset_metadata() -> None:
    """시드 데이터셋이 list/raw 작업을 선언하는지 확인한다."""
    dataset = _adapter().get_dataset("{dataset_key}")
    assert dataset.id == "{provider_name}.{dataset_key}"
    assert Operation.LIST in dataset.operations
    assert Operation.RAW in dataset.operations
'''


def scaffold_provider(
    name: str,
    *,
    repo_root: Path,
    dataset_key: str = "sample",
    overwrite: bool = False,
) -> ScaffoldResult:
    """새 Provider 어댑터의 최소 파일 묶음을 생성한다.

    매개변수:
        name: Provider 이름(파이썬 패키지 명, 예: ``my_provider``).
        repo_root: kpubdata 저장소 루트 경로(``src/`` 와 ``tests/`` 의 부모).
        dataset_key: 시드 catalogue 엔트리의 dataset_key.
        overwrite: 기존 파일이 있을 때 덮어쓸지 여부. 기본 False — 기존 파일이
            있으면 ``FileExistsError``를 발생시킨다.

    반환값:
        ScaffoldResult: 생성된 경로 묶음.

    예외:
        ValueError: 이름 또는 dataset_key가 규칙에 맞지 않을 때.
        FileExistsError: ``overwrite=False`` 일 때 기존 파일이 존재하면 발생.
    """
    _validate_provider_name(name)
    _validate_dataset_key(dataset_key)

    provider_dir = repo_root / "src" / "kpubdata" / "providers" / name
    adapter_path = provider_dir / "adapter.py"
    init_path = provider_dir / "__init__.py"
    catalogue_path = provider_dir / "catalogue.json"
    fixture_dir = repo_root / "tests" / "fixtures" / name
    fixture_path = fixture_dir / "success_sample.json"
    contract_test_path = repo_root / "tests" / "contract" / f"test_{name}.py"

    files: dict[Path, str] = {
        init_path: _init_module(name),
        adapter_path: _adapter_module(name, dataset_key),
        catalogue_path: _catalogue_seed(name, dataset_key),
        fixture_path: _fixture_seed(dataset_key),
        contract_test_path: _contract_test(name, dataset_key),
    }

    if not overwrite:
        existing = [p for p in files if p.exists()]
        if existing:
            paths = ", ".join(str(p) for p in existing)
            raise FileExistsError(
                f"refusing to overwrite existing scaffold files: {paths}. "
                "Pass overwrite=True (or --force) to replace."
            )

    provider_dir.mkdir(parents=True, exist_ok=True)
    fixture_dir.mkdir(parents=True, exist_ok=True)
    contract_test_path.parent.mkdir(parents=True, exist_ok=True)

    created: list[Path] = []
    for path, content in files.items():
        path.write_text(content, encoding="utf-8")
        created.append(path)

    return ScaffoldResult(
        provider_dir=provider_dir,
        adapter_path=adapter_path,
        init_path=init_path,
        catalogue_path=catalogue_path,
        fixture_dir=fixture_dir,
        fixture_path=fixture_path,
        contract_test_path=contract_test_path,
        created=tuple(created),
    )


__all__ = ["ScaffoldResult", "scaffold_provider"]
