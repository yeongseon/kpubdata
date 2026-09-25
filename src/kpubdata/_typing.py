"""표준 라이브러리에 들어오기 전까지만 ``typing_extensions`` 를 쓰는 창구.

네 모듈이 ``typing_extensions`` 를 조건 없이 import 하는데, 의존성 marker 는
``python_version < '3.11'`` 이었다. 그래서 3.11 이상에서 새로 설치하면
``typing_extensions`` 가 없는 채로 import 문만 남아 ``import kpubdata`` 자체가
ImportError 로 죽는다. CI 는 늘 dev extra 를 깔아서(그쪽이 typing_extensions 를
끌어온다) 드러나지 않았다.

각 이름이 stdlib 에 들어온 버전이 다르므로 한 marker 로는 맞출 수 없다 —
``dataclass_transform`` 은 3.11, ``override`` 는 3.12 다. 여기서 버전별로 갈라
두고, marker 는 둘 다 필요한 3.12 미만으로 맞춘다.
"""

from __future__ import annotations

import sys

if sys.version_info >= (3, 12):
    from typing import override
else:  # pragma: no cover - 3.11 이하에서만 실행된다
    from typing_extensions import override

if sys.version_info >= (3, 11):
    from typing import dataclass_transform
else:  # pragma: no cover - 3.10 에서만 실행된다
    from typing_extensions import dataclass_transform

__all__ = ["dataclass_transform", "override"]
