"""Tests for configuration system."""

import pytest

from src.config import Settings, get_settings


class TestSettings:
    """Test suite for application settings."""

    def test_default_settings_load(self):
        """Settings should load with all defaults without any env vars."""
        settings = Settings(openai_api_key="test-key")
        assert settings.app_name == "MedGuard RAG"
        assert settings.app_env == "development"
        assert settings.api_port == 8000

    def test_settings_validation_rejects_invalid_env(self):
        """app_env must be one of development, staging, production."""
        with pytest.raises(ValueError):
            Settings(app_env="invalid", openai_api_key="test-key")

    def test_settings_validation_rejects_invalid_log_level(self):
        """log_level must be a valid Python logging level."""
        with pytest.raises(ValueError):
            Settings(log_level="VERBOSE", openai_api_key="test-key")

    def test_chunk_size_boundaries(self):
        """Chunk size must be between 100 and 2048."""
        with pytest.raises(ValueError):
            Settings(chunk_size=50, openai_api_key="test-key")
        with pytest.raises(ValueError):
            Settings(chunk_size=5000, openai_api_key="test-key")

    def test_temperature_boundaries(self):
        """Temperature must be between 0.0 and 1.0."""
        with pytest.raises(ValueError):
            Settings(openai_temperature=1.5, openai_api_key="test-key")

    def test_is_production_property(self):
        """is_production should return True only for production env."""
        settings = Settings(app_env="production", openai_api_key="test-key")
        assert settings.is_production is True
        assert settings.is_development is False

    def test_is_development_property(self):
        """is_development should return True only for development env."""
        settings = Settings(app_env="development", openai_api_key="test-key")
        assert settings.is_development is True
        assert settings.is_production is False

    def test_get_settings_returns_cached_instance(self):
        """get_settings should return the same instance on repeated calls."""
        get_settings.cache_clear()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
        get_settings.cache_clear()