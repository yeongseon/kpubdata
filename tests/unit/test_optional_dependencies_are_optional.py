"""optional extra 없이도 기본 경로가 동작하는지 검증한다.

CI 는 늘 ``--extra dev`` 로 돌기 때문에 "optional 이라고 선언했지만 실제로는
필수" 인 의존성을 잡지 못한다. krx 어댑터가 pandas 를 최상단에서 import 하는
바람에, krx 를 쓸 생각이 없는 사용자의 ``client.datasets.list()`` 가 통째로
죽었다 — krx 는 인증이 필요 없어서 provider manifest 에 항상 실려 있고,
provider 를 지정하지 않은 목록 조회는 등록된 어댑터를 전부 만들기 때문이다.
"""

from __future__ import annotations

import builtins
import importlib
import sys
from collections.abc import Iterator
from types import ModuleType
from typing import Any

import pytest

# typing_extensions 도 optional 이다 — 의존성 marker 가 python_version < '3.12'
# 라서 3.12 이상에서 새로 설치하면 없다. 네 모듈이 이걸 조건 없이 import 하던
# 시절에는 ``import kpubdata`` 자체가 ImportError 로 죽었다.
_OPTIONAL_MODULES = ("pandas", "pykrx", "typing_extensions")


@pytest.fixture()
def without_optional_extras() -> Iterator[None]:
    """optional extra 가 설치되지 않은 환경을 흉내낸다."""
    real_import = builtins.__import__

    def _blocked(name: str, *args: Any, **kwargs: Any) -> ModuleType:
        root = name.split(".", 1)[0]
        if root in _OPTIONAL_MODULES:
            raise ImportError(f"No module named {root!r}")
        return real_import(name, *args, **kwargs)

    saved = {
        key: value
        for key, value in sys.modules.items()
        if key.split(".", 1)[0] in {*_OPTIONAL_MODULES, "kpubdata"}
    }
    for key in list(saved):
        del sys.modules[key]
    builtins.__import__ = _blocked
    try:
        yield
    finally:
        builtins.__import__ = real_import
        for key in [k for k in sys.modules if k.split(".", 1)[0] == "kpubdata"]:
            del sys.modules[key]
        sys.modules.update(saved)


class TestPandasIsReallyOptional:
    def test_the_krx_adapter_module_imports(self, without_optional_extras: None) -> None:
        module = importlib.import_module("kpubdata.providers.krx.adapter")

        assert module.KrxAdapter is not None

    def test_listing_every_dataset_works(self, without_optional_extras: None) -> None:
        """이게 실제로 죽던 호출이다 — ``kpubdata datasets list`` 와 같은 경로."""
        client_module = importlib.import_module("kpubdata.client")

        datasets = client_module.Client().datasets.list()

        assert datasets, "카탈로그가 비면 안 된다"

    def test_krx_still_lists_its_own_datasets(self, without_optional_extras: None) -> None:
        module = importlib.import_module("kpubdata.providers.krx.adapter")

        assert module.KrxAdapter().list_datasets()

    def test_actually_using_krx_explains_what_to_install(
        self, without_optional_extras: None
    ) -> None:
        """조용히 실패하지 않는다 — 무엇을 설치해야 하는지 말해 준다."""
        module = importlib.import_module("kpubdata.providers.krx.adapter")
        exceptions = importlib.import_module("kpubdata.exceptions")

        with pytest.raises(exceptions.ConfigError, match=r"kpubdata\[krx\]"):
            module._pandas()


class TestTypingExtensionsIsReallyOptional:
    """3.12 이상 새 설치에는 typing_extensions 가 없다.

    ``override`` 는 3.12, ``dataclass_transform`` 은 3.11 부터 stdlib 이라
    marker 하나로는 맞출 수 없다. ``kpubdata._typing`` 이 버전별로 갈라 준다.
    """

    def test_importing_the_package_works(self, without_optional_extras: None) -> None:
        client_module = importlib.import_module("kpubdata.client")

        assert client_module.Client is not None

    def test_every_module_that_needed_it_imports(self, without_optional_extras: None) -> None:
        for name in (
            "kpubdata.client",
            "kpubdata.transport.http",
            "kpubdata.core.dataset",
            "kpubdata.core.capability",
        ):
            assert importlib.import_module(name) is not None
