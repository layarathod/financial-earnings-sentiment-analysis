"""
Tests for fetcher module.
"""

import pytest

from app.fetcher.downloader import ArticleDownloader
from app.fetcher.robots import RobotsChecker


class TestRobotsChecker:
    """Tests for robots.txt checking."""

    def test_initialization(self):
        """Test RobotsChecker initialization."""
        checker = RobotsChecker(user_agent="TestBot", respect_robots=True)

        assert checker.user_agent == "TestBot"
        assert checker.respect_robots is True

    def test_can_fetch_when_disabled(self):
        """Test that can_fetch returns True when robots checking is disabled."""
        checker = RobotsChecker(user_agent="TestBot", respect_robots=False)

        assert checker.can_fetch("https://example.com/article")

    def test_can_fetch_allows_unknown_domain(self):
        """Test that unknown domains are allowed by default."""
        checker = RobotsChecker(user_agent="TestBot", respect_robots=True)

        # For a domain we can't fetch robots.txt from, should allow
        result = checker.can_fetch("https://nonexistent-domain-12345.com/article")

        # Should allow since we can't fetch robots.txt
        assert result is True

    def test_clear_cache(self):
        """Test cache clearing."""
        checker = RobotsChecker(user_agent="TestBot")

        checker.clear_cache()

        assert len(checker._parsers) == 0
        assert len(checker._last_access) == 0


class TestArticleDownloader:
    """Tests for article downloader."""

    def test_initialization(self, test_settings):
        """Test ArticleDownloader initialization."""
        downloader = ArticleDownloader(
            user_agent="TestBot",
            timeout=10,
            max_retries=2,
        )

        assert downloader.user_agent == "TestBot"
        assert downloader.timeout == 10
        assert downloader.max_retries == 2

    def test_session_creation(self, test_settings):
        """Test session is created with proper configuration."""
        downloader = ArticleDownloader()

        assert downloader.session is not None
        assert "User-Agent" in downloader.session.headers

    def test_context_manager(self, test_settings):
        """Test downloader can be used as context manager."""
        with ArticleDownloader() as downloader:
            assert downloader.session is not None

        # Session should be closed after context exit
        # (requests.Session doesn't have an is_closed property, but this shouldn't error)

    def test_download_invalid_url(self, test_settings):
        """Test downloading from invalid URL returns None."""
        downloader = ArticleDownloader(respect_robots=False)

        result = downloader.download("https://nonexistent-domain-12345.com/article")

        assert result is None

    def test_download_many_empty_list(self, test_settings):
        """Test download_many with empty list."""
        downloader = ArticleDownloader()

        results = downloader.download_many([])

        assert results == []
