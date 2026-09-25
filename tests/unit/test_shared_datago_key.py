"""README 가 안내하는 provider 키 이름이 실제로 동작해야 한다.

localdata·semas 는 data.go.kr 서비스라 datago 와 같은 서비스 키를 쓴다. 두
어댑터가 곧바로 ``require_provider_key("datago")`` 를 부르는 바람에, README 의
``provider_keys={"localdata": ...}`` 와 ``KPUBDATA_LOCALDATA_API_KEY`` 가 조용히
무시됐다 — 문서를 그대로 따라 한 사용자는 ConfigError 를 봤다.
"""

from __future__ import annotations

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.exceptions import ConfigError

_SHARED_KEY_PROVIDERS = ("localdata", "semas")


@pytest.fixture(autouse=True)
def _no_ambient_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    """실행 환경의 실제 키가 결과를 가리지 않게 한다."""
    for name in ("DATAGO", "LOCALDATA", "SEMAS"):
        monkeypatch.delenv(f"KPUBDATA_{name}_API_KEY", raising=False)
        monkeypatch.delenv(f"{name}_API_KEY", raising=False)


class TestTheDocumentedNameWorks:
    @pytest.mark.parametrize("provider", _SHARED_KEY_PROVIDERS)
    def test_its_own_name_resolves(self, provider: str) -> None:
        config = KPubDataConfig(provider_keys={provider: "own-key"})

        assert config.require_provider_key(provider, fallback_to="datago") == "own-key"

    @pytest.mark.parametrize("provider", _SHARED_KEY_PROVIDERS)
    def test_its_own_env_var_resolves(self, provider: str, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(f"KPUBDATA_{provider.upper()}_API_KEY", "env-key")
        config = KPubDataConfig()

        assert config.require_provider_key(provider, fallback_to="datago") == "env-key"


class TestTheSharedKeyStillWorks:
    @pytest.mark.parametrize("provider", _SHARED_KEY_PROVIDERS)
    def test_the_datago_key_is_used_when_no_own_key_exists(self, provider: str) -> None:
        """기존 사용자는 datago 키 하나만 설정해 두었다 — 그 구성을 깨지 않는다."""
        config = KPubDataConfig(provider_keys={"datago": "shared-key"})

        assert config.require_provider_key(provider, fallback_to="datago") == "shared-key"

    @pytest.mark.parametrize("provider", _SHARED_KEY_PROVIDERS)
    def test_its_own_key_wins_over_the_shared_one(self, provider: str) -> None:
        config = KPubDataConfig(provider_keys={provider: "own-key", "datago": "shared-key"})

        assert config.require_provider_key(provider, fallback_to="datago") == "own-key"


class TestTheErrorExplainsTheRelationship:
    @pytest.mark.parametrize("provider", _SHARED_KEY_PROVIDERS)
    def test_it_names_both_variables(self, provider: str) -> None:
        config = KPubDataConfig()

        with pytest.raises(ConfigError) as excinfo:
            config.require_provider_key(provider, fallback_to="datago")

        message = str(excinfo.value)
        assert f"KPUBDATA_{provider.upper()}_API_KEY" in message
        assert "KPUBDATA_DATAGO_API_KEY" in message

    def test_a_provider_with_no_fallback_is_unchanged(self) -> None:
        config = KPubDataConfig()

        with pytest.raises(ConfigError, match="Missing provider API key for 'bok'"):
            config.require_provider_key("bok")
