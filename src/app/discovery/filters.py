"""
Filtering and ranking logic for discovered articles.
"""

import re
from datetime import datetime
from typing import Any, Dict, List

from app.utils.logger import get_logger

logger = get_logger(__name__)


class ArticleFilter:
    """
    Filters and ranks articles based on relevance, date, and quality.
    """

    def __init__(
        self,
        ticker: str,
        company_name: str,
        start_date: datetime,
        end_date: datetime,
        exclude_domains: List[str] = None,
    ):
        """
        Initialize article filter.

        Args:
            ticker: Stock ticker symbol
            company_name: Company name for matching
            start_date: Start of valid date range
            end_date: End of valid date range
            exclude_domains: List of domains to exclude
        """
        self.ticker = ticker.upper()
        self.company_name = company_name
        self.start_date = start_date
        self.end_date = end_date
        self.exclude_domains = exclude_domains or []

        # Earnings-related keywords
        self.earnings_keywords = [
            "earnings",
            "quarterly results",
            "reports earnings",
            "Q1",
            "Q2",
            "Q3",
            "Q4",
            "revenue",
            "profit",
            "EPS",
            "guidance",
            "outlook",
            "conference call",
            "results",
        ]

        logger.debug(f"ArticleFilter initialized for {self.ticker}")

    def filter_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter articles by date, domain, and basic criteria.

        Args:
            articles: List of article metadata dictionaries

        Returns:
            Filtered list of articles
        """
        logger.info(f"Filtering {len(articles)} articles")

        filtered = []
        stats = {"date_filtered": 0, "domain_filtered": 0, "passed": 0}

        for article in articles:
            # Date filter
            if not self._is_in_date_range(article):
                stats["date_filtered"] += 1
                continue

            # Domain filter
            if self._is_excluded_domain(article):
                stats["domain_filtered"] += 1
                continue

            filtered.append(article)
            stats["passed"] += 1

        logger.info(
            f"Filtered: {stats['passed']} passed, "
            f"{stats['date_filtered']} date filtered, "
            f"{stats['domain_filtered']} domain filtered"
        )

        return filtered

    def _is_in_date_range(self, article: Dict[str, Any]) -> bool:
        """
        Check if article is within date range.

        Args:
            article: Article metadata

        Returns:
            True if article is within date range
        """
        published = article.get("published")

        if not published:
            logger.debug(f"Article missing published date: {article.get('url', 'unknown')}")
            return True  # Include if no date (let user decide)

        # Ensure published is datetime
        if isinstance(published, str):
            try:
                published = datetime.fromisoformat(published)
            except ValueError:
                logger.debug(f"Invalid date format: {published}")
                return True

        # Check range
        in_range = self.start_date <= published <= self.end_date

        if not in_range:
            logger.debug(
                f"Article outside date range: {published.date()} not in "
                f"{self.start_date.date()} to {self.end_date.date()}"
            )

        return in_range

    def _is_excluded_domain(self, article: Dict[str, Any]) -> bool:
        """
        Check if article is from an excluded domain.

        Args:
            article: Article metadata

        Returns:
            True if domain should be excluded
        """
        domain = article.get("domain", "")

        for excluded in self.exclude_domains:
            if excluded.lower() in domain.lower():
                logger.debug(f"Excluded domain: {domain}")
                return True

        return False

    def score_relevance(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Score articles by relevance to ticker and earnings.

        Args:
            articles: List of article metadata

        Returns:
            Articles with added 'relevance_score' field
        """
        logger.info(f"Scoring relevance for {len(articles)} articles")

        for article in articles:
            score = self._calculate_relevance_score(article)
            article["relevance_score"] = score

        # Sort by relevance (descending)
        articles.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        logger.debug(
            f"Top article score: {articles[0].get('relevance_score', 0):.3f} - {articles[0].get('title', 'N/A')[:60]}"
            if articles
            else "No articles to score"
        )

        return articles

    def _calculate_relevance_score(self, article: Dict[str, Any]) -> float:
        """
        Calculate relevance score for an article.

        Scoring factors:
        - Ticker mention in title/summary: +0.5
        - Company name mention: +0.3
        - Earnings keywords: +0.1 per keyword (max +0.5)
        - Source quality score: weight 0.3
        - Recency: +0.1 for articles within last 24 hours

        Args:
            article: Article metadata

        Returns:
            Relevance score (0-2.0)
        """
        score = 0.0

        title = article.get("title", "").lower()
        summary = article.get("summary", "").lower()
        text = f"{title} {summary}"

        # Ticker mention
        ticker_pattern = r"\b" + re.escape(self.ticker.lower()) + r"\b"
        if re.search(ticker_pattern, text):
            score += 0.5
            logger.debug(f"Ticker match: +0.5 for {article.get('url', 'unknown')[:50]}")

        # Company name mention
        if self.company_name.lower() in text:
            score += 0.3
            logger.debug(f"Company name match: +0.3")

        # Earnings keywords
        keyword_score = 0.0
        matched_keywords = []
        for keyword in self.earnings_keywords:
            if keyword.lower() in text:
                keyword_score += 0.1
                matched_keywords.append(keyword)

        keyword_score = min(keyword_score, 0.5)  # Cap at 0.5
        score += keyword_score

        if matched_keywords:
            logger.debug(f"Keyword matches: {matched_keywords[:3]} (+{keyword_score:.1f})")

        # Source quality
        quality_score = article.get("quality_score", 0.5)
        score += quality_score * 0.3

        # Recency bonus
        published = article.get("published")
        if published:
            if isinstance(published, str):
                try:
                    published = datetime.fromisoformat(published)
                except ValueError:
                    published = None

            if published:
                age_hours = (datetime.now() - published).total_seconds() / 3600
                if age_hours < 24:
                    score += 0.1
                    logger.debug(f"Recency bonus: +0.1 ({age_hours:.1f}h old)")

        return round(score, 3)

    def filter_and_rank(
        self, articles: List[Dict[str, Any]], top_k: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Filter, score, and rank articles.

        Args:
            articles: List of article metadata
            top_k: Number of top articles to return

        Returns:
            Top K ranked articles
        """
        logger.info(f"Filter and rank {len(articles)} articles, returning top {top_k}")

        # Filter
        filtered = self.filter_articles(articles)

        # Score
        scored = self.score_relevance(filtered)

        # Return top K
        top_articles = scored[:top_k]

        logger.info(f"Returning {len(top_articles)} top articles")

        return top_articles


class KeywordMatcher:
    """
    Advanced keyword matching for specific contexts.
    """

    @staticmethod
    def contains_earnings_keywords(text: str) -> bool:
        """
        Check if text contains earnings-related keywords.

        Args:
            text: Text to check

        Returns:
            True if earnings keywords found
        """
        earnings_patterns = [
            r"\bearnings\b",
            r"\bQ[1-4]\s+\d{4}\b",
            r"\bquarterly\s+results\b",
            r"\breports?\s+earnings\b",
            r"\bEPS\b",
            r"\bconfere.nce\s+call\b",
            r"\bguidance\b",
        ]

        text_lower = text.lower()

        for pattern in earnings_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True

        return False

    @staticmethod
    def extract_quarter_mentions(text: str) -> List[str]:
        """
        Extract quarter mentions (Q1 2024, etc.) from text.

        Args:
            text: Text to search

        Returns:
            List of quarter strings found
        """
        pattern = r"\bQ([1-4])\s+(\d{4})\b"
        matches = re.findall(pattern, text, re.IGNORECASE)

        quarters = [f"Q{q} {year}" for q, year in matches]
        return quarters
