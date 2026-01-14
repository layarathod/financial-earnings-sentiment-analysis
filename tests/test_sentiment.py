"""
Tests for sentiment analysis module.
"""

import pytest

from app.analysis.aggregator import SentimentAggregator


class TestVADERSentimentAnalyzer:
    """Tests for VADER sentiment analyzer."""

    def test_initialization(self):
        """Test VADER initialization."""
        try:
            from app.analysis.sentiment import VADERSentimentAnalyzer

            analyzer = VADERSentimentAnalyzer()
            assert analyzer is not None
        except ImportError:
            pytest.skip("vaderSentiment not installed")

    def test_analyze_positive_text(self):
        """Test analyzing positive text."""
        try:
            from app.analysis.sentiment import VADERSentimentAnalyzer

            analyzer = VADERSentimentAnalyzer()
            text = "This is excellent news! The company exceeded expectations with strong earnings growth."

            result = analyzer.analyze(text)

            assert result["model"] == "vader"
            assert "compound" in result
            assert "label" in result
            assert result["compound"] > 0  # Should be positive
            assert result["label"] == "positive"
        except ImportError:
            pytest.skip("vaderSentiment not installed")

    def test_analyze_negative_text(self):
        """Test analyzing negative text."""
        try:
            from app.analysis.sentiment import VADERSentimentAnalyzer

            analyzer = VADERSentimentAnalyzer()
            text = "This is terrible news. The company missed expectations badly and outlook is dire."

            result = analyzer.analyze(text)

            assert result["compound"] < 0  # Should be negative
            assert result["label"] == "negative"
        except ImportError:
            pytest.skip("vaderSentiment not installed")

    def test_analyze_empty_text(self):
        """Test analyzing empty text."""
        try:
            from app.analysis.sentiment import VADERSentimentAnalyzer

            analyzer = VADERSentimentAnalyzer()
            result = analyzer.analyze("")

            assert result["label"] == "neutral"
            assert result["compound"] == 0.0
        except ImportError:
            pytest.skip("vaderSentiment not installed")


class TestSentimentAggregator:
    """Tests for sentiment aggregator."""

    def test_initialization(self):
        """Test aggregator initialization."""
        aggregator = SentimentAggregator()
        assert aggregator is not None

    def test_aggregate_empty_list(self):
        """Test aggregating empty list."""
        aggregator = SentimentAggregator()
        result = aggregator.aggregate([])

        assert "statistics" in result
        assert result["statistics"]["total_articles"] == 0

    def test_aggregate_vader_scores(self):
        """Test aggregating VADER scores."""
        aggregator = SentimentAggregator()

        articles = [
            {
                "title": "Article 1",
                "sentiment": {
                    "model": "vader",
                    "compound": 0.8,
                    "positive": 0.7,
                    "negative": 0.1,
                    "neutral": 0.2,
                    "label": "positive",
                },
            },
            {
                "title": "Article 2",
                "sentiment": {
                    "model": "vader",
                    "compound": 0.6,
                    "positive": 0.6,
                    "negative": 0.2,
                    "neutral": 0.2,
                    "label": "positive",
                },
            },
            {
                "title": "Article 3",
                "sentiment": {
                    "model": "vader",
                    "compound": -0.3,
                    "positive": 0.2,
                    "negative": 0.5,
                    "neutral": 0.3,
                    "label": "negative",
                },
            },
        ]

        result = aggregator.aggregate(articles)

        assert "statistics" in result
        assert result["statistics"]["total_articles"] == 3
        assert result["statistics"]["positive_count"] == 2
        assert result["statistics"]["negative_count"] == 1

        assert "overall" in result
        # Average compound should be positive (0.8 + 0.6 - 0.3) / 3
        assert result["overall"]["compound"] > 0

    def test_aggregate_weighted(self):
        """Test weighted aggregation."""
        aggregator = SentimentAggregator()

        articles = [
            {
                "sentiment": {
                    "model": "vader",
                    "compound": 0.8,
                    "label": "positive",
                    "confidence": 0.8,
                }
            },
            {
                "sentiment": {
                    "model": "vader",
                    "compound": -0.2,
                    "label": "negative",
                    "confidence": 0.2,
                }
            },
        ]

        # Weight first article heavily
        weights = [0.9, 0.1]

        result = aggregator.aggregate_weighted(articles, weights)

        assert "statistics" in result
        # Weighted compound should be close to first article
        # 0.8 * 0.9 + (-0.2) * 0.1 = 0.72 - 0.02 = 0.70

    def test_compute_statistics(self):
        """Test statistics computation."""
        aggregator = SentimentAggregator()

        sentiments = [
            {"label": "positive"},
            {"label": "positive"},
            {"label": "negative"},
            {"label": "neutral"},
        ]

        stats = aggregator._compute_statistics(sentiments)

        assert stats["total_articles"] == 4
        assert stats["positive_count"] == 2
        assert stats["negative_count"] == 1
        assert stats["neutral_count"] == 1
        assert stats["positive_ratio"] == 0.5
        assert stats["negative_ratio"] == 0.25


class TestGetSentimentAnalyzer:
    """Tests for sentiment analyzer factory."""

    def test_get_vader_analyzer(self):
        """Test getting VADER analyzer."""
        try:
            from app.analysis.sentiment import VADERSentimentAnalyzer, get_sentiment_analyzer

            analyzer = get_sentiment_analyzer("vader")
            assert isinstance(analyzer, VADERSentimentAnalyzer)
        except ImportError:
            pytest.skip("vaderSentiment not installed")

    def test_get_unknown_analyzer(self):
        """Test getting unknown analyzer defaults to VADER."""
        try:
            from app.analysis.sentiment import VADERSentimentAnalyzer, get_sentiment_analyzer

            analyzer = get_sentiment_analyzer("unknown_model")
            assert isinstance(analyzer, VADERSentimentAnalyzer)
        except ImportError:
            pytest.skip("vaderSentiment not installed")
