"""
Pytest configuration and shared fixtures.
"""

import tempfile
from pathlib import Path

import pytest

from app.config.settings import Settings, reset_settings


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_settings(temp_dir):
    """Create test settings with temporary directories."""
    reset_settings()

    settings = Settings(
        project_root=temp_dir,
        data_dir=temp_dir / "data",
        output_dir=temp_dir / "outputs",
        raw_data_dir=temp_dir / "data" / "raw",
        parsed_data_dir=temp_dir / "data" / "parsed",
        results_data_dir=temp_dir / "data" / "results",
        cache_dir=temp_dir / "data" / "cache",
        reports_dir=temp_dir / "outputs" / "reports",
        plots_dir=temp_dir / "outputs" / "plots",
        log_to_file=False,  # Don't create log files in tests
    )

    settings.ensure_directories()
    return settings


@pytest.fixture
def mock_article_data():
    """Mock article data for testing."""
    return {
        "url": "https://example.com/article-1",
        "title": "AAPL Reports Strong Q4 Earnings",
        "text": "Apple Inc. reported strong quarterly earnings, beating analyst expectations.",
        "author": "John Doe",
        "published": "2024-01-15T10:00:00",
        "word_count": 500,
    }


@pytest.fixture
def mock_urls():
    """Mock URL data for testing."""
    return [
        {
            "url": "https://example.com/article-1",
            "title": "AAPL Earnings Beat",
            "source": "example.com",
            "published": "2024-01-15T10:00:00",
            "relevance_score": 0.95,
        },
        {
            "url": "https://example.com/article-2",
            "title": "Apple Revenue Growth",
            "source": "example.com",
            "published": "2024-01-14T15:00:00",
            "relevance_score": 0.88,
        },
    ]


@pytest.fixture(autouse=True)
def reset_settings_after_test():
    """Reset settings after each test."""
    yield
    reset_settings()
