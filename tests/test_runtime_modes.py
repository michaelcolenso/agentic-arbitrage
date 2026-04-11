"""
Tests for FACTORY_MODE runtime guardrails.
"""
import importlib
import os

import pytest

import config.settings as settings_module
import factory as factory_module
from core.models import OpportunityStatus


def reload_settings(monkeypatch):
    """Reload settings module to pick up env changes."""
    return importlib.reload(settings_module)


def reload_factory(monkeypatch):
    """Reload factory module to pick up settings changes."""
    importlib.reload(settings_module)
    return importlib.reload(factory_module)


class TestFactoryModeConfig:
    """Tests for FactoryConfig mode parsing."""

    def test_default_mode_is_demo(self, monkeypatch):
        monkeypatch.delenv("FACTORY_MODE", raising=False)
        settings = reload_settings(monkeypatch)
        assert settings.config.factory_mode == "demo"
        assert settings.config.is_demo is True
        assert settings.config.is_staging is False
        assert settings.config.is_production is False

    def test_staging_mode(self, monkeypatch):
        monkeypatch.setenv("FACTORY_MODE", "staging")
        settings = reload_settings(monkeypatch)
        assert settings.config.factory_mode == "staging"
        assert settings.config.is_demo is False
        assert settings.config.is_staging is True
        assert settings.config.is_production is False

    def test_production_mode(self, monkeypatch):
        monkeypatch.setenv("FACTORY_MODE", "production")
        settings = reload_settings(monkeypatch)
        assert settings.config.factory_mode == "production"
        assert settings.config.is_demo is False
        assert settings.config.is_staging is False
        assert settings.config.is_production is True

    def test_invalid_mode_defaults_to_demo(self, monkeypatch):
        monkeypatch.setenv("FACTORY_MODE", "invalid")
        settings = reload_settings(monkeypatch)
        assert settings.config.factory_mode == "demo"


class TestFactoryModeCLI:
    """Tests for CLI mode argument."""

    def test_cli_accepts_mode_argument(self, monkeypatch):
        monkeypatch.setenv("FACTORY_MODE", "demo")
        factory = reload_factory(monkeypatch)
        parser = factory.create_cli()
        args = parser.parse_args(["--mode", "production", "run"])
        assert args.mode == "production"

    def test_cli_defaults_mode_from_env(self, monkeypatch):
        monkeypatch.setenv("FACTORY_MODE", "staging")
        factory = reload_factory(monkeypatch)
        parser = factory.create_cli()
        args = parser.parse_args(["run"])
        assert args.mode == "staging"

    def test_cli_invalid_mode_rejected(self, monkeypatch):
        monkeypatch.setenv("FACTORY_MODE", "demo")
        factory = reload_factory(monkeypatch)
        parser = factory.create_cli()
        with pytest.raises(SystemExit):
            parser.parse_args(["--mode", "invalid", "run"])


class TestProductionRequirements:
    """Tests for production mode fail-closed behavior."""

    def test_production_requires_cloudflare_token(self, monkeypatch):
        monkeypatch.setenv("FACTORY_MODE", "production")
        monkeypatch.delenv("CLOUDFLARE_API_TOKEN", raising=False)
        monkeypatch.setenv("GITHUB_TOKEN", "valid_token")
        settings = reload_settings(monkeypatch)
        factory = reload_factory(monkeypatch)
        arb = factory.ArbitrageFactory()
        with pytest.raises(RuntimeError, match="production"):
            arb.assert_production_ready()

    def test_production_requires_github_token(self, monkeypatch):
        monkeypatch.setenv("FACTORY_MODE", "production")
        monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "valid_token")
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        settings = reload_settings(monkeypatch)
        factory = reload_factory(monkeypatch)
        arb = factory.ArbitrageFactory()
        with pytest.raises(RuntimeError, match="production"):
            arb.assert_production_ready()

    def test_production_passes_with_all_credentials(self, monkeypatch):
        monkeypatch.setenv("FACTORY_MODE", "production")
        monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "valid_token")
        monkeypatch.setenv("GITHUB_TOKEN", "valid_token")
        settings = reload_settings(monkeypatch)
        factory = reload_factory(monkeypatch)
        arb = factory.ArbitrageFactory()
        # Should not raise
        arb.assert_production_ready()

    def test_demo_does_not_require_credentials(self, monkeypatch):
        monkeypatch.setenv("FACTORY_MODE", "demo")
        monkeypatch.delenv("CLOUDFLARE_API_TOKEN", raising=False)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        settings = reload_settings(monkeypatch)
        factory = reload_factory(monkeypatch)
        arb = factory.ArbitrageFactory()
        # Should not raise
        arb.assert_production_ready()

    def test_staging_does_not_require_credentials(self, monkeypatch):
        monkeypatch.setenv("FACTORY_MODE", "staging")
        monkeypatch.delenv("CLOUDFLARE_API_TOKEN", raising=False)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        settings = reload_settings(monkeypatch)
        factory = reload_factory(monkeypatch)
        arb = factory.ArbitrageFactory()
        # Should not raise
        arb.assert_production_ready()


class TestStatusIncludesMode:
    """Tests that status output includes mode."""

    def test_status_includes_mode(self, monkeypatch):
        monkeypatch.setenv("FACTORY_MODE", "staging")
        factory = reload_factory(monkeypatch)
        arb = factory.ArbitrageFactory()
        status = arb.get_status()
        assert status["mode"] == "staging"
