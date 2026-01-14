"""
Sentiment aggregation across multiple articles.
"""

from typing import Any, Dict, List

import numpy as np

from app.utils.logger import get_logger

logger = get_logger(__name__)


class SentimentAggregator:
    """
    Aggregates sentiment scores from multiple articles.
    """

    def __init__(self):
        """Initialize aggregator."""
        pass

    def aggregate(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate sentiment from multiple articles.

        Args:
            articles: List of articles with sentiment scores

        Returns:
            Aggregated sentiment summary
        """
        if not articles:
            logger.warning("No articles to aggregate")
            return self._empty_result()

        logger.info(f"Aggregating sentiment from {len(articles)} articles")

        # Extract sentiments
        sentiments = [a.get("sentiment", {}) for a in articles if "sentiment" in a]

        if not sentiments:
            logger.warning("No sentiment scores found in articles")
            return self._empty_result()

        # Aggregate by model
        results = {}

        # Check if we have VADER scores
        vader_scores = [s.get("vader") for s in sentiments if "vader" in s]
        if vader_scores:
            results["vader"] = self._aggregate_vader(vader_scores)

        # Check if we have FinBERT scores
        finbert_scores = [s.get("finbert") for s in sentiments if "finbert" in s]
        if finbert_scores:
            results["finbert"] = self._aggregate_finbert(finbert_scores)

        # If single model results, use directly
        if len(sentiments) > 0 and "model" in sentiments[0]:
            model_name = sentiments[0]["model"]
            if model_name == "vader":
                results["overall"] = self._aggregate_vader(sentiments)
            elif model_name == "finbert":
                results["overall"] = self._aggregate_finbert(sentiments)

        # Compute overall statistics
        results["statistics"] = self._compute_statistics(sentiments)

        # Add article-level details
        results["articles"] = self._article_summaries(articles)

        logger.info(
            f"Aggregation complete: {results['statistics']['total_articles']} articles, "
            f"overall sentiment: {results.get('overall', {}).get('label', 'N/A')}"
        )

        return results

    def aggregate_weighted(
        self, articles: List[Dict[str, Any]], weights: List[float] = None
    ) -> Dict[str, Any]:
        """
        Aggregate sentiment with article-specific weights.

        Args:
            articles: List of articles with sentiment
            weights: Optional weights for each article (e.g., by quality, relevance)

        Returns:
            Weighted aggregated sentiment
        """
        if not articles:
            return self._empty_result()

        # Use uniform weights if not provided
        if weights is None:
            weights = [1.0] * len(articles)

        if len(weights) != len(articles):
            logger.warning("Weights length mismatch, using uniform weights")
            weights = [1.0] * len(articles)

        # Normalize weights
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]

        # Get sentiments
        sentiments = []
        for article, weight in zip(articles, weights):
            if "sentiment" in article:
                sent = article["sentiment"].copy()
                sent["weight"] = weight
                sentiments.append(sent)

        if not sentiments:
            return self._empty_result()

        # Aggregate with weights
        results = {}

        # VADER weighted aggregation
        vader_scores = [(s, s["weight"]) for s in sentiments if "compound" in s]
        if vader_scores:
            results["vader"] = self._aggregate_vader_weighted(vader_scores)

        # FinBERT weighted aggregation
        finbert_scores = [(s, s["weight"]) for s in sentiments if "positive" in s and "model" in s and s["model"] == "finbert"]
        if finbert_scores:
            results["finbert"] = self._aggregate_finbert_weighted(finbert_scores)

        # Statistics
        results["statistics"] = self._compute_statistics(sentiments)

        # Article summaries
        results["articles"] = self._article_summaries(articles)

        return results

    def _aggregate_vader(self, scores: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate VADER scores.

        Args:
            scores: List of VADER sentiment scores

        Returns:
            Aggregated VADER sentiment
        """
        if not scores:
            return {}

        # Average compound score
        compounds = [s.get("compound", 0) for s in scores]
        avg_compound = float(np.mean(compounds))

        # Average component scores
        positives = [s.get("positive", 0) for s in scores]
        negatives = [s.get("negative", 0) for s in scores]
        neutrals = [s.get("neutral", 0) for s in scores]

        # Determine overall label
        if avg_compound >= 0.05:
            label = "positive"
        elif avg_compound <= -0.05:
            label = "negative"
        else:
            label = "neutral"

        # Count label distribution
        labels = [s.get("label", "neutral") for s in scores]
        label_counts = {
            "positive": labels.count("positive"),
            "negative": labels.count("negative"),
            "neutral": labels.count("neutral"),
        }

        return {
            "compound": avg_compound,
            "positive": float(np.mean(positives)),
            "negative": float(np.mean(negatives)),
            "neutral": float(np.mean(neutrals)),
            "label": label,
            "confidence": abs(avg_compound),
            "distribution": label_counts,
        }

    def _aggregate_vader_weighted(
        self, weighted_scores: List[tuple]
    ) -> Dict[str, Any]:
        """
        Aggregate VADER scores with weights.

        Args:
            weighted_scores: List of (score, weight) tuples

        Returns:
            Weighted aggregated VADER sentiment
        """
        if not weighted_scores:
            return {}

        # Weighted average of compound
        weighted_compound = sum(s["compound"] * w for s, w in weighted_scores)

        # Determine label
        if weighted_compound >= 0.05:
            label = "positive"
        elif weighted_compound <= -0.05:
            label = "negative"
        else:
            label = "neutral"

        return {
            "compound": weighted_compound,
            "label": label,
            "confidence": abs(weighted_compound),
        }

    def _aggregate_finbert(self, scores: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate FinBERT scores.

        Args:
            scores: List of FinBERT sentiment scores

        Returns:
            Aggregated FinBERT sentiment
        """
        if not scores:
            return {}

        # Average probabilities
        positives = [s.get("positive", 0) for s in scores]
        negatives = [s.get("negative", 0) for s in scores]
        neutrals = [s.get("neutral", 0) for s in scores]

        avg_positive = float(np.mean(positives))
        avg_negative = float(np.mean(negatives))
        avg_neutral = float(np.mean(neutrals))

        # Determine overall label
        max_prob = max(avg_positive, avg_negative, avg_neutral)
        if avg_positive == max_prob:
            label = "positive"
        elif avg_negative == max_prob:
            label = "negative"
        else:
            label = "neutral"

        # Label distribution
        labels = [s.get("label", "neutral") for s in scores]
        label_counts = {
            "positive": labels.count("positive"),
            "negative": labels.count("negative"),
            "neutral": labels.count("neutral"),
        }

        return {
            "positive": avg_positive,
            "negative": avg_negative,
            "neutral": avg_neutral,
            "label": label,
            "confidence": max_prob,
            "distribution": label_counts,
        }

    def _aggregate_finbert_weighted(
        self, weighted_scores: List[tuple]
    ) -> Dict[str, Any]:
        """
        Aggregate FinBERT scores with weights.

        Args:
            weighted_scores: List of (score, weight) tuples

        Returns:
            Weighted aggregated FinBERT sentiment
        """
        if not weighted_scores:
            return {}

        # Weighted average of probabilities
        weighted_positive = sum(s.get("positive", 0) * w for s, w in weighted_scores)
        weighted_negative = sum(s.get("negative", 0) * w for s, w in weighted_scores)
        weighted_neutral = sum(s.get("neutral", 0) * w for s, w in weighted_scores)

        # Determine label
        max_prob = max(weighted_positive, weighted_negative, weighted_neutral)
        if weighted_positive == max_prob:
            label = "positive"
        elif weighted_negative == max_prob:
            label = "negative"
        else:
            label = "neutral"

        return {
            "positive": weighted_positive,
            "negative": weighted_negative,
            "neutral": weighted_neutral,
            "label": label,
            "confidence": max_prob,
        }

    def _compute_statistics(self, sentiments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compute statistics from sentiments.

        Args:
            sentiments: List of sentiment scores

        Returns:
            Statistics dictionary
        """
        if not sentiments:
            return {}

        # Count labels
        labels = [s.get("label", "neutral") for s in sentiments]
        positive_count = labels.count("positive")
        negative_count = labels.count("negative")
        neutral_count = labels.count("neutral")

        total = len(labels)

        return {
            "total_articles": total,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "positive_ratio": positive_count / total if total > 0 else 0,
            "negative_ratio": negative_count / total if total > 0 else 0,
            "neutral_ratio": neutral_count / total if total > 0 else 0,
        }

    def _article_summaries(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create summaries of individual articles.

        Args:
            articles: List of articles

        Returns:
            List of article summaries
        """
        summaries = []

        for article in articles:
            summary = {
                "url": article.get("url", ""),
                "title": article.get("title", "")[:100],  # Truncate
                "sentiment": article.get("sentiment", {}),
            }

            # Add optional fields if available
            if "relevance_score" in article:
                summary["relevance_score"] = article["relevance_score"]
            if "quality_score" in article:
                summary["quality_score"] = article["quality_score"]
            if "source" in article:
                summary["source"] = article["source"]

            summaries.append(summary)

        return summaries

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result."""
        return {
            "statistics": {
                "total_articles": 0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
            },
            "articles": [],
        }
