"""Built-in provider manifest — single source of truth for provider discovery.

Each entry maps a provider name to its module path and adapter class name.
The ``Client`` lazily imports these modules on first access so that unused
providers impose zero import cost.

To add a new built-in provider, append an entry here.  No other file needs
to change for basic registration.
"""

from __future__ import annotations

#: (provider_name, module_path, adapter_class_name)
BUILTIN_PROVIDERS: tuple[tuple[str, str, str], ...] = (
    ("datago", "kpubdata.providers.datago", "DataGoAdapter"),
    ("bok", "kpubdata.providers.bok", "BokAdapter"),
    ("seoul", "kpubdata.providers.seoul", "SeoulAdapter"),
    ("kosis", "kpubdata.providers.kosis", "KosisAdapter"),
    ("lofin", "kpubdata.providers.lofin", "LofinAdapter"),
    ("localdata", "kpubdata.providers.localdata.adapter", "LocaldataAdapter"),
    ("semas", "kpubdata.providers.semas.adapter", "SemasAdapter"),
)
