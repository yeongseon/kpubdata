"""내장 Provider 매니페스트 — Provider 탐색의 단일 기준 문서.

각 엔트리는 provider 이름을 모듈 경로와 어댑터 클래스 이름에 매핑한다.
``Client``는 첫 접근 시 이 모듈들을 지연 import하므로, 사용하지 않는
provider는 import 비용을 전혀 추가하지 않는다.

새 내장 provider를 추가하려면 여기에 엔트리를 덧붙이면 된다. 기본 등록을 위해
다른 파일을 변경할 필요는 없다.
"""

from __future__ import annotations

#: (provider_name, module_path, adapter_class_name)
BUILTIN_PROVIDERS: tuple[tuple[str, str, str], ...] = (
    ("datago", "kpubdata.providers.datago", "DataGoAdapter"),
    ("bok", "kpubdata.providers.bok", "BokAdapter"),
    ("law", "kpubdata.providers.law", "LawAdapter"),
    ("seoul", "kpubdata.providers.seoul", "SeoulAdapter"),
    ("kosis", "kpubdata.providers.kosis", "KosisAdapter"),
    ("lofin", "kpubdata.providers.lofin", "LofinAdapter"),
    ("localdata", "kpubdata.providers.localdata.adapter", "LocaldataAdapter"),
    ("semas", "kpubdata.providers.semas.adapter", "SemasAdapter"),
    ("krx", "kpubdata.providers.krx", "KrxAdapter"),
)
