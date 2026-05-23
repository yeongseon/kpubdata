"""테스트 모듈.

이 파일은 ``tests/unit/test_config_coverage.py`` 경로의 테스트 시나리오와 보조 객체를 정의한다.
회귀 방지와 공개 계약 검증을 위해 핵심 흐름, 예외, 가장자리 조건을 확인한다.
"""

from __future__ import annotations

import os
from unittest.mock import patch

from kpubdata.config import KPubDataConfig


# test from env skips empty values 테스트가 검증하는 시나리오를 설명한다.
def test_from_env_skips_empty_values() -> None:
    """
    test from env skips empty values 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    env = {
        "KPUBDATA_DATAGO_API_KEY": "datago-key",
        "KPUBDATA_EMPTY_API_KEY": "",
    }
    with patch.dict(os.environ, env, clear=False):
        config = KPubDataConfig.from_env()

    assert config.provider_keys["datago"] == "datago-key"
    assert "empty" not in config.provider_keys


# test from env provider overrides require string pairs and non empty values 테스트가 검증하는 시나리오를 설명한다.
def test_from_env_provider_overrides_require_string_pairs_and_non_empty_values() -> None:
    """
    test from env provider overrides require string pairs and non empty values 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    env = {"KPUBDATA_DATAGO_API_KEY": "scanned-key"}
    overrides: dict[object, object] = {
        "Data-Go": "override-key",
        "blank": "",
        "nonstr": 123,
        999: "value",
    }
    with patch.dict(os.environ, env, clear=False):
        config = KPubDataConfig.from_env(provider_keys=overrides)

    assert config.provider_keys["data-go"] == "override-key"
    assert "blank" not in config.provider_keys
    assert "nonstr" not in config.provider_keys
    assert "999" not in config.provider_keys


# test get provider key uses case insensitive explicit fallback 테스트가 검증하는 시나리오를 설명한다.
def test_get_provider_key_uses_case_insensitive_explicit_fallback() -> None:
    """
    test get provider key uses case insensitive explicit fallback 시나리오를 검증한다.

    반환값:
        None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

    예외:
        구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

    예시:
        테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
    """
    config = KPubDataConfig(provider_keys={"DaTaGo": "explicit-key"})

    assert config.get_provider_key("datago") == "explicit-key"
