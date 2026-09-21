"""모든 provider 어댑터에 공통으로 거는 계약 테스트 (#455).

`PROVIDER_ADAPTER_CONTRACT.md` §2 가 규정한 책임 중 **어댑터마다 달라지지 않는 것**을
한 곳에서 파라미터라이즈로 건다. 어댑터별 테스트 파일에는 방언 차이(envelope 형상,
파라미터 이름 매핑, provider 고유 오류 코드)만 남는다.

왜 이렇게 묶나: 어댑터가 14개인데 같은 계약을 각자 다시 쓰면, 어댑터가 하나 늘 때마다
같은 테스트가 한 벌씩 복제된다(이슈 시점 테스트 코드가 소스의 2.8배). 여기 한 줄을 추가하면
14개 전부에 즉시 적용되고, 새 어댑터는 ``_ADAPTERS`` 에 한 줄만 더하면 계약 전체를 상속한다.

**커버리지가 아니라 회귀 방지선이다** — 새 provider 를 붙일 때 "이건 당연히 되겠지" 하고
넘어가는 지점을 기계가 대신 확인한다.
"""

from __future__ import annotations

import importlib
from typing import Any

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.core.capability import Operation
from kpubdata.core.models import DatasetRef
from kpubdata.exceptions import DatasetNotFoundError

# (모듈 이름, 클래스 이름). 새 어댑터를 추가하면 이 줄만 늘리면 된다.
_ADAPTER_SPECS: list[tuple[str, str]] = [
    ("bok", "BokAdapter"),
    ("datago", "DataGoAdapter"),
    ("fds", "FdsAdapter"),
    ("kipris", "KiprisAdapter"),
    ("korean", "KoreanAdapter"),
    ("kosis", "KosisAdapter"),
    ("krx", "KrxAdapter"),
    ("law", "LawAdapter"),
    ("localdata", "LocaldataAdapter"),
    ("lofin", "LofinAdapter"),
    ("neis", "NeisAdapter"),
    ("semas", "SemasAdapter"),
    ("seoul", "SeoulAdapter"),
    ("sgis", "SgisAdapter"),
]


def _load(module_name: str, class_name: str) -> Any:
    module = importlib.import_module(f"kpubdata.providers.{module_name}.adapter")
    return getattr(module, class_name)


def _adapter(module_name: str, class_name: str) -> Any:
    """키 없이 어댑터를 만든다 — 카탈로그 조회는 credential 을 요구하면 안 된다."""
    return _load(module_name, class_name)(config=KPubDataConfig(provider_keys={}))


_PARAMS = [pytest.param(m, c, id=m) for m, c in _ADAPTER_SPECS]


def _adapter_params(func: Any) -> Any:
    return pytest.mark.parametrize(("module_name", "class_name"), _PARAMS)(func)


# --- 기본 표면 -------------------------------------------------------------


@_adapter_params
def test_adapter_exposes_the_required_surface(module_name: str, class_name: str) -> None:
    """Client 가 호출하는 메서드가 전부 있어야 한다 (계약 §2)."""
    cls = _load(module_name, class_name)
    for attribute in (
        "name",
        "list_datasets",
        "search_datasets",
        "get_dataset",
        "get_schema",
        "query_records",
        "call_raw",
    ):
        assert hasattr(cls, attribute), f"{class_name} is missing {attribute}"


@_adapter_params
def test_adapter_declares_whether_it_needs_a_key(module_name: str, class_name: str) -> None:
    """``requires_api_key`` 는 bool 이어야 한다 — Client 가 이 값으로 분기한다."""
    cls = _load(module_name, class_name)
    assert isinstance(cls.requires_api_key, bool)


@_adapter_params
def test_provider_name_matches_the_module(module_name: str, class_name: str) -> None:
    assert _adapter(module_name, class_name).name == module_name


@_adapter_params
def test_catalogue_loads_without_any_credential(module_name: str, class_name: str) -> None:
    """탐색은 키 없이 가능해야 한다 — 키가 있어야 목록도 못 보면 발견성이 죽는다."""
    datasets = _adapter(module_name, class_name).list_datasets()
    assert datasets, f"{module_name} has an empty catalogue"
    assert all(isinstance(d, DatasetRef) for d in datasets)


# --- 카탈로그 무결성 -------------------------------------------------------


@_adapter_params
def test_dataset_keys_are_unique(module_name: str, class_name: str) -> None:
    """키가 겹치면 ``get_dataset`` 이 어느 쪽을 주는지 정의되지 않는다."""
    keys = [d.dataset_key for d in _adapter(module_name, class_name).list_datasets()]
    duplicates = {k for k in keys if keys.count(k) > 1}
    assert not duplicates, f"{module_name} has duplicate dataset keys: {sorted(duplicates)}"


@_adapter_params
def test_dataset_ids_are_provider_qualified(module_name: str, class_name: str) -> None:
    """``id`` 는 provider 로 한정돼야 cross-provider 로 섞이지 않는다."""
    for dataset in _adapter(module_name, class_name).list_datasets():
        assert dataset.provider == module_name
        assert dataset.id.startswith(f"{module_name}."), dataset.id


@_adapter_params
def test_every_dataset_declares_at_least_one_operation(module_name: str, class_name: str) -> None:
    """빈 operations 는 "아무것도 못 한다"는 뜻이다 — 정직한 선언을 강제한다(계약 §2)."""
    for dataset in _adapter(module_name, class_name).list_datasets():
        assert dataset.operations, f"{dataset.id} declares no operations"
        assert all(isinstance(op, Operation) for op in dataset.operations)


@_adapter_params
def test_declared_operations_match_supports(module_name: str, class_name: str) -> None:
    for dataset in _adapter(module_name, class_name).list_datasets():
        for operation in dataset.operations:
            assert dataset.supports(operation)


@_adapter_params
def test_datasets_have_human_readable_names(module_name: str, class_name: str) -> None:
    for dataset in _adapter(module_name, class_name).list_datasets():
        assert dataset.name.strip(), f"{dataset.id} has a blank name"


# --- 조회 ------------------------------------------------------------------


@_adapter_params
def test_get_dataset_returns_the_catalogue_entry(module_name: str, class_name: str) -> None:
    adapter = _adapter(module_name, class_name)
    for dataset in adapter.list_datasets():
        assert adapter.get_dataset(dataset.dataset_key) is dataset


@_adapter_params
def test_unknown_dataset_key_raises_not_found(module_name: str, class_name: str) -> None:
    """조용히 None 을 돌려주면 호출부가 빈 결과와 오타를 구분하지 못한다."""
    adapter = _adapter(module_name, class_name)
    with pytest.raises(DatasetNotFoundError) as exc:
        adapter.get_dataset("no-such-dataset-key-xyz")
    assert exc.value.provider == module_name
    # 오류에 provider 로 한정된 id 가 실려야 사용자가 어디를 고칠지 안다.
    assert "no-such-dataset-key-xyz" in str(exc.value)


@_adapter_params
def test_search_finds_a_known_dataset(module_name: str, class_name: str) -> None:
    adapter = _adapter(module_name, class_name)
    sample = adapter.list_datasets()[0]
    assert sample in adapter.search_datasets(sample.dataset_key)


@_adapter_params
def test_search_is_case_insensitive(module_name: str, class_name: str) -> None:
    adapter = _adapter(module_name, class_name)
    sample = adapter.list_datasets()[0]
    assert sample in adapter.search_datasets(sample.dataset_key.upper())


@_adapter_params
def test_search_with_no_match_returns_empty(module_name: str, class_name: str) -> None:
    assert _adapter(module_name, class_name).search_datasets("존재하지-않는-키워드-zzz") == []


@_adapter_params
def test_list_datasets_returns_a_fresh_list(module_name: str, class_name: str) -> None:
    """호출자가 받은 목록을 바꿔도 어댑터 내부 카탈로그가 오염되면 안 된다."""
    adapter = _adapter(module_name, class_name)
    first = adapter.list_datasets()
    first.clear()
    assert adapter.list_datasets(), f"{module_name} leaked its internal catalogue list"


# --- 스키마 선언 -----------------------------------------------------------


@_adapter_params
def test_get_schema_is_honest_about_what_it_knows(module_name: str, class_name: str) -> None:
    """스키마를 모르면 ``None`` 이어야 한다 — 빈 스키마를 지어내면 안 된다(계약 §2)."""
    adapter = _adapter(module_name, class_name)
    for dataset in adapter.list_datasets():
        schema = adapter.get_schema(dataset)
        if schema is None:
            continue
        assert schema.fields, f"{dataset.id} returned an empty schema instead of None"
