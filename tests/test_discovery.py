"""
Tests for discovery module.
"""

from datetime import datetime, timedelta

import pytest

from app.discovery.deduplicator import ContentDeduplicator, URLDeduplicator
from app.discovery.filters import ArticleFilter, KeywordMatcher
from app.discovery.search import ArticleDiscovery


class TestURLDeduplicator:
    """Tests for URL deduplication."""

    def test_normalize_url_removes_tracking(self):
        """Test URL normalization removes tracking parameters."""
        dedup = URLDeduplicator()

        url = "https://example.com/article?utm_source=twitter&utm_medium=social"
        normalized = dedup.normalize_url(url)

        assert "utm_source" not in normalized
        assert "utm_medium" not in normalized
        assert "example.com/article" in normalized

    def test_normalize_url_removes_www(self):
        """Test URL normalization removes www."""
        dedup = URLDeduplicator()

        url = "https://www.example.com/article"
        normalized = dedup.normalize_url(url)

        assert "www." not in normalized
        assert "example.com/article" in normalized

    def test_normalize_url_removes_trailing_slash(self):
        """Test URL normalization removes trailing slash."""
        dedup = URLDeduplicator()

        url1 = "https://example.com/article/"
        url2 = "https://example.com/article"

        norm1 = dedup.normalize_url(url1)
        norm2 = dedup.normalize_url(url2)

        assert norm1 == norm2

    def test_deduplicate_removes_exact_duplicates(self):
        """Test deduplication removes exact URL duplicates."""
        dedup = URLDeduplicator()

        articles = [
            {"url": "https://example.com/article1", "title": "Article 1"},
            {"url": "https://example.com/article1", "title": "Article 1 Duplicate"},
            {"url": "https://example.com/article2", "title": "Article 2"},
        ]

        unique = dedup.deduplicate(articles)

        assert len(unique) == 2
        assert unique[0]["url"] == "https://example.com/article1"
        assert unique[1]["url"] == "https://example.com/article2"

    def test_deduplicate_removes_similar_urls(self):
        """Test deduplication handles URL variations."""
        dedup = URLDeduplicator()

        articles = [
            {"url": "https://www.example.com/article?utm_source=fb", "title": "Article"},
            {"url": "https://example.com/article?utm_source=tw", "title": "Article"},
            {"url": "https://example.com/article", "title": "Article"},
        ]

        unique = dedup.deduplicate(articles)

        # All should normalize to the same URL
        assert len(unique) == 1

    def test_hash_title_normalizes(self):
        """Test title hashing normalizes text."""
        dedup = URLDeduplicator()

        title1 = "Apple Reports Strong Earnings!"
        title2 = "apple reports strong earnings"
        title3 = "Apple  Reports  Strong  Earnings"

        hash1 = dedup._hash_title(title1)
        hash2 = dedup._hash_title(title2)
        hash3 = dedup._hash_title(title3)

        assert hash1 == hash2 == hash3


class TestArticleFilter:
    """Tests for article filtering."""

    def test_date_filter_includes_in_range(self):
        """Test date filter includes articles in range."""
        start = datetime.now() - timedelta(days=7)
        end = datetime.now()

        article_filter = ArticleFilter(
            ticker="AAPL", company_name="Apple", start_date=start, end_date=end
        )

        article = {"published": datetime.now() - timedelta(days=3)}

        assert article_filter._is_in_date_range(article)

    def test_date_filter_excludes_out_of_range(self):
        """Test date filter excludes articles outside range."""
        start = datetime.now() - timedelta(days=7)
        end = datetime.now()

        article_filter = ArticleFilter(
            ticker="AAPL", company_name="Apple", start_date=start, end_date=end
        )

        # Article from 30 days ago
        article = {"published": datetime.now() - timedelta(days=30)}

        assert not article_filter._is_in_date_range(article)

    def test_domain_filter_excludes_blocked(self):
        """Test domain filter excludes blocked domains."""
        article_filter = ArticleFilter(
            ticker="AAPL",
            company_name="Apple",
            start_date=datetime.now(),
            end_date=datetime.now(),
            exclude_domains=["twitter.com", "facebook.com"],
        )

        article = {"domain": "twitter.com"}

        assert article_filter._is_excluded_domain(article)

    def test_relevance_score_ticker_match(self):
        """Test relevance scoring rewards ticker mentions."""
        article_filter = ArticleFilter(
            ticker="AAPL",
            company_name="Apple",
            start_date=datetime.now(),
            end_date=datetime.now(),
        )

        article = {
            "title": "AAPL reports strong quarterly earnings",
            "summary": "Apple Inc. exceeded expectations.",
            "quality_score": 0.9,
        }

        score = article_filter._calculate_relevance_score(article)

        # Should have ticker match (+0.5) + earnings keyword + quality
        assert score > 0.8

    def test_relevance_score_company_name(self):
        """Test relevance scoring rewards company name."""
        article_filter = ArticleFilter(
            ticker="AAPL",
            company_name="Apple",
            start_date=datetime.now(),
            end_date=datetime.now(),
        )

        article = {
            "title": "Apple announces new product",
            "summary": "The company revealed details.",
            "quality_score": 0.5,
        }

        score = article_filter._calculate_relevance_score(article)

        # Should have company name match (+0.3)
        assert score >= 0.3

    def test_filter_and_rank_returns_top_k(self):
        """Test filter_and_rank returns top K articles."""
        article_filter = ArticleFilter(
            ticker="AAPL",
            company_name="Apple",
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now(),
        )

        articles = [
            {
                "title": f"Article {i}",
                "summary": "AAPL earnings" if i % 2 == 0 else "Other news",
                "published": datetime.now() - timedelta(days=i),
                "quality_score": 0.5,
                "domain": "example.com",
            }
            for i in range(20)
        ]

        top_articles = article_filter.filter_and_rank(articles, top_k=5)

        assert len(top_articles) <= 5
        # Should be sorted by relevance
        if len(top_articles) > 1:
            assert top_articles[0]["relevance_score"] >= top_articles[-1]["relevance_score"]


class TestKeywordMatcher:
    """Tests for keyword matching."""

    def test_contains_earnings_keywords_positive(self):
        """Test earnings keyword detection - positive case."""
        text = "Apple reported strong Q4 2023 earnings yesterday."

        assert KeywordMatcher.contains_earnings_keywords(text)

    def test_contains_earnings_keywords_negative(self):
        """Test earnings keyword detection - negative case."""
        text = "Apple launches new iPhone model."

        assert not KeywordMatcher.contains_earnings_keywords(text)

    def test_extract_quarter_mentions(self):
        """Test quarter mention extraction."""
        text = "The company reported Q1 2024 and Q2 2024 results."

        quarters = KeywordMatcher.extract_quarter_mentions(text)

        assert "Q1 2024" in quarters
        assert "Q2 2024" in quarters
        assert len(quarters) == 2


class TestArticleDiscovery:
    """Tests for article discovery."""

    def test_initialization(self, test_settings):
        """Test discovery initialization."""
        discovery = ArticleDiscovery(
            ticker="AAPL",
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now(),
            top_k=10,
        )

        assert discovery.ticker == "AAPL"
        assert discovery.top_k == 10

    def test_get_company_name(self, test_settings):
        """Test company name lookup."""
        discovery = ArticleDiscovery(
            ticker="AAPL",
            start_date=datetime.now(),
            end_date=datetime.now(),
        )

        assert discovery.company_name == "Apple"

    def test_get_company_name_fallback(self, test_settings):
        """Test company name fallback for unknown ticker."""
        discovery = ArticleDiscovery(
            ticker="UNKNOWN",
            start_date=datetime.now(),
            end_date=datetime.now(),
        )

        assert discovery.company_name == "UNKNOWN"

    def test_get_search_keywords(self, test_settings):
        """Test search keyword generation."""
        discovery = ArticleDiscovery(
            ticker="AAPL",
            start_date=datetime.now(),
            end_date=datetime.now(),
        )

        keywords = discovery.get_search_keywords()

        # Should contain ticker and company name
        assert any("AAPL" in kw for kw in keywords)
        assert any("Apple" in kw for kw in keywords)

    def test_parse_rss_entry(self, test_settings):
        """Test RSS entry parsing."""
        discovery = ArticleDiscovery(
            ticker="AAPL",
            start_date=datetime.now(),
            end_date=datetime.now(),
        )

        # Mock RSS entry
        class MockEntry:
            def get(self, key, default=None):
                data = {
                    "link": "https://example.com/article",
                    "title": "Apple Earnings Beat",
                    "summary": "Apple reported strong results.",
                    "published_parsed": datetime.now().timetuple()[:6],
                }
                return data.get(key, default)

        entry = MockEntry()
        article = discovery._parse_rss_entry(entry, "Example Source", 0.9)

        assert article is not None
        assert article["url"] == "https://example.com/article"
        assert article["title"] == "Apple Earnings Beat"
        assert article["quality_score"] == 0.9


class TestContentDeduplicator:
    """Tests for content deduplication."""

    def test_is_duplicate_exact(self):
        """Test exact duplicate detection."""
        dedup = ContentDeduplicator()

        text = "This is an article about earnings."

        assert not dedup.is_duplicate(text)
        assert dedup.is_duplicate(text)  # Second time should be duplicate

    def test_is_duplicate_normalized(self):
        """Test normalized duplicate detection."""
        dedup = ContentDeduplicator()

        text1 = "This is an article."
        text2 = "This  is  an  article."  # Extra spaces
        text3 = "THIS IS AN ARTICLE."  # Different case

        assert not dedup.is_duplicate(text1)
        assert dedup.is_duplicate(text2)
        assert dedup.is_duplicate(text3)
