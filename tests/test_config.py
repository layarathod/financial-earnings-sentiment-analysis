"""
Tests for configuration module.
"""

import pytest

from app.config.settings import Settings, get_settings, reset_settings


def test_settings_defaults():
    """Test default settings values."""
    settings = Settings()

    assert settings.log_level == "INFO"
    assert settings.sentiment_model == "vader"
    assert settings.default_top_k == 20
    assert settings.respect_robots_txt is True
    assert settings.enable_rss is True


def test_settings_validation_log_level():
    """Test log level validation."""
    with pytest.raises(ValueError, match="log_level must be one of"):
        Settings(log_level="INVALID")


def test_settings_validation_sentiment_model():
    """Test sentiment model validation."""
    with pytest.raises(ValueError, match="sentiment_model must be one of"):
        Settings(sentiment_model="invalid_model")


def test_settings_valid_values():
    """Test settings with valid values."""
    settings = Settings(
        log_level="DEBUG",
        sentiment_model="finbert",
        default_top_k=50,
    )

    assert settings.log_level == "DEBUG"
    assert settings.sentiment_model == "finbert"
    assert settings.default_top_k == 50


def test_get_settings_singleton():
    """Test that get_settings returns singleton instance."""
    reset_settings()

    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2


def test_settings_ensure_directories(test_settings, temp_dir):
    """Test directory creation."""
    test_settings.ensure_directories()

    assert test_settings.data_dir.exists()
    assert test_settings.raw_data_dir.exists()
    assert test_settings.parsed_data_dir.exists()
    assert test_settings.results_data_dir.exists()
    assert test_settings.output_dir.exists()


def test_sources_config_path(test_settings):
    """Test sources config path property."""
    path = test_settings.sources_config_path
    assert path.name == "sources.yaml"
    assert "configs" in str(path)
