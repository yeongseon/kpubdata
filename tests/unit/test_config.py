"""Tests for config management."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from kpubdata.config import KPubDataConfig
from kpubdata.exceptions import ConfigError


class TestKPubDataConfig:
    """
    TestKPubDataConfig 관련 역할을 캡슐화하는 클래스.

    이 클래스는 ``tests/unit/test_config.py`` 모듈 안에서 TestKPubDataConfig의 상태와 동작을 함께 관리한다.
    주요 메서드: test_explicit_key, test_missing_key_returns_none, test_require_key_raises, test_env_kpubdata_prefix, test_env_fallback_prefix.

    속성 설명:
        생성자와 클래스 본문에서 정의한 속성은 하위 메서드가 공통 문맥으로 재사용한다.
    """
    # test explicit key 테스트가 검증하는 시나리오를 설명한다.
    def test_explicit_key(self) -> None:
        """
        test explicit key 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        cfg = KPubDataConfig(provider_keys={"datago": "mykey"})
        assert cfg.get_provider_key("datago") == "mykey"

    # test missing key returns none 테스트가 검증하는 시나리오를 설명한다.
    def test_missing_key_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        test missing key returns none 시나리오를 검증한다.

        매개변수:
            monkeypatch (pytest.MonkeyPatch): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        monkeypatch.delenv("KPUBDATA_DATAGO_API_KEY", raising=False)
        monkeypatch.delenv("DATAGO_API_KEY", raising=False)
        cfg = KPubDataConfig()
        assert cfg.get_provider_key("datago") is None

    # test require key raises 테스트가 검증하는 시나리오를 설명한다.
    def test_require_key_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        test require key raises 시나리오를 검증한다.

        매개변수:
            monkeypatch (pytest.MonkeyPatch): 호출자가 제공하는 입력 값이다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        monkeypatch.delenv("KPUBDATA_DATAGO_API_KEY", raising=False)
        monkeypatch.delenv("DATAGO_API_KEY", raising=False)
        cfg = KPubDataConfig()
        with pytest.raises(ConfigError, match="Missing provider API key"):
            cfg.require_provider_key("datago")

    # test env kpubdata prefix 테스트가 검증하는 시나리오를 설명한다.
    def test_env_kpubdata_prefix(self) -> None:
        """
        test env kpubdata prefix 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        cfg = KPubDataConfig()
        with patch.dict(os.environ, {"KPUBDATA_SEOUL_API_KEY": "envkey"}):
            assert cfg.get_provider_key("seoul") == "envkey"

    # test env fallback prefix 테스트가 검증하는 시나리오를 설명한다.
    def test_env_fallback_prefix(self) -> None:
        """
        test env fallback prefix 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        cfg = KPubDataConfig()
        with patch.dict(os.environ, {"SEOUL_API_KEY": "fallback"}, clear=False):
            # Only if KPUBDATA_ not set
            result = cfg.get_provider_key("seoul")
            assert result is not None

    # test explicit takes precedence 테스트가 검증하는 시나리오를 설명한다.
    def test_explicit_takes_precedence(self) -> None:
        """
        test explicit takes precedence 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        cfg = KPubDataConfig(provider_keys={"seoul": "explicit"})
        with patch.dict(os.environ, {"KPUBDATA_SEOUL_API_KEY": "envkey"}):
            assert cfg.get_provider_key("seoul") == "explicit"

    # test from env 테스트가 검증하는 시나리오를 설명한다.
    def test_from_env(self) -> None:
        """
        test from env 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        env = {"KPUBDATA_DATAGO_API_KEY": "k1", "KPUBDATA_SEOUL_API_KEY": "k2"}
        with patch.dict(os.environ, env, clear=False):
            cfg = KPubDataConfig.from_env()
            assert "datago" in cfg.provider_keys
            assert "seoul" in cfg.provider_keys

    # test repr no secrets 테스트가 검증하는 시나리오를 설명한다.
    def test_repr_no_secrets(self) -> None:
        """
        test repr no secrets 시나리오를 검증한다.

        반환값:
            None: 계산 결과 또는 하위 호출의 반환값을 돌려준다.

        예외:
            구현체 내부 또는 하위 의존성에서 발생한 예외를 그대로 전파할 수 있다.

        예시:
            테스트 이름이 설명하는 기대 동작이 회귀 없이 유지되는지 확인한다.
        """
        cfg = KPubDataConfig(provider_keys={"datago": "secret123"})
        r = repr(cfg)
        assert "secret123" not in r
        assert "datago" in r
