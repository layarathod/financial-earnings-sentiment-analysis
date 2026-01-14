"""
Article discovery via RSS feeds and search APIs.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import yaml

from app.config.settings import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Try to import feedparser, fall back to our custom parser
try:
    import feedparser
except ImportError:
    from app.discovery import rss_parser as feedparser
    logger.info("Using custom RSS parser (feedparser not available)")


class ArticleDiscovery:
    """
    Discovers financial articles using RSS feeds and search APIs.
    """

    def __init__(self, ticker: str, start_date: datetime, end_date: datetime, top_k: int = 20):
        """
        Initialize article discovery.

        Args:
            ticker: Stock ticker symbol
            start_date: Start of search window
            end_date: End of search window
            top_k: Maximum number of articles to return
        """
        self.ticker = ticker.upper()
        self.company_name = self._get_company_name(ticker)
        self.start_date = start_date
        self.end_date = end_date
        self.top_k = top_k
        self.settings = get_settings()

        # Load sources configuration
        self.sources = self._load_sources_config()

        logger.info(f"ArticleDiscovery initialized for {self.ticker}")
        logger.debug(
            f"Date range: {self.start_date.date()} to {self.end_date.date()}, top_k={self.top_k}"
        )

    def _get_company_name(self, ticker: str) -> str:
        """
        Get company name from ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Company name (simple mapping for common tickers)
        """
        # Simple mapping for demo - in production, use yfinance or similar
        ticker_to_name = {
            "AAPL": "Apple",
            "MSFT": "Microsoft",
            "GOOGL": "Google",
            "GOOG": "Google",
            "AMZN": "Amazon",
            "TSLA": "Tesla",
            "META": "Meta",
            "NVDA": "NVIDIA",
            "NFLX": "Netflix",
            "JPM": "JPMorgan",
            "BAC": "Bank of America",
            "WMT": "Walmart",
            "DIS": "Disney",
        }
        return ticker_to_name.get(ticker.upper(), ticker.upper())

    def _load_sources_config(self) -> Dict[str, Any]:
        """
        Load news sources configuration.

        Returns:
            Sources configuration dictionary
        """
        config_path = self.settings.sources_config_path

        if not config_path.exists():
            logger.warning(f"Sources config not found at {config_path}, using defaults")
            return {"sources": {}}

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        logger.debug(f"Loaded sources config from {config_path}")
        return config

    def discover(self) -> List[Dict[str, Any]]:
        """
        Discover articles from all enabled sources.

        Returns:
            List of article metadata dictionaries
        """
        logger.info(f"Starting article discovery for {self.ticker}")

        articles = []

        # RSS discovery
        if self.settings.enable_rss:
            rss_articles = self._discover_rss()
            articles.extend(rss_articles)
            logger.info(f"RSS discovery found {len(rss_articles)} articles")

        # Search API discovery (if enabled)
        if self.settings.enable_search_api:
            api_articles = self._discover_search_api()
            articles.extend(api_articles)
            logger.info(f"Search API found {len(api_articles)} articles")

        logger.info(f"Total articles discovered: {len(articles)}")
        return articles

    def _discover_rss(self) -> List[Dict[str, Any]]:
        """
        Discover articles via RSS feeds.

        Returns:
            List of article metadata from RSS feeds
        """
        articles = []
        sources = self.sources.get("sources", {})

        # Iterate through all tiers
        for tier_name, tier_sources in sources.items():
            if not isinstance(tier_sources, list):
                continue

            logger.debug(f"Processing {tier_name} sources")

            for source in tier_sources:
                source_articles = self._fetch_rss_source(source)
                articles.extend(source_articles)

                # Respect per-source limit
                if len(source_articles) > self.settings.max_articles_per_source:
                    logger.debug(
                        f"Limiting {source['name']} to {self.settings.max_articles_per_source} articles"
                    )

        return articles

    def _fetch_rss_source(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch articles from a single RSS source.

        Args:
            source: Source configuration dictionary

        Returns:
            List of article metadata
        """
        source_name = source.get("name", "Unknown")
        rss_feeds = source.get("rss_feeds", [])
        quality_score = source.get("quality_score", 0.5)

        if not rss_feeds:
            logger.debug(f"No RSS feeds configured for {source_name}")
            return []

        articles = []

        for feed_url in rss_feeds:
            try:
                logger.debug(f"Fetching RSS feed: {feed_url}")

                # Parse feed with timeout
                feed = feedparser.parse(
                    feed_url,
                    agent=self.settings.user_agent,
                )

                # Check for errors
                if feed.bozo:
                    logger.warning(
                        f"RSS feed parse warning for {feed_url}: {feed.bozo_exception}"
                    )

                # Process entries
                for entry in feed.entries:
                    article = self._parse_rss_entry(entry, source_name, quality_score)
                    if article:
                        articles.append(article)

                logger.debug(f"Fetched {len(feed.entries)} entries from {feed_url}")

            except Exception as e:
                logger.error(f"Failed to fetch RSS feed {feed_url}: {e}")
                continue

        # Limit per source
        articles = articles[: self.settings.max_articles_per_source]

        logger.info(f"Fetched {len(articles)} articles from {source_name}")
        return articles

    def _parse_rss_entry(
        self, entry: Any, source_name: str, quality_score: float
    ) -> Optional[Dict[str, Any]]:
        """
        Parse a single RSS feed entry into article metadata.

        Args:
            entry: Feedparser entry object
            source_name: Name of the source
            quality_score: Quality score for this source

        Returns:
            Article metadata dictionary or None if invalid
        """
        try:
            # Extract URL
            url = entry.get("link", "")
            if not url:
                return None

            # Extract title
            title = entry.get("title", "")

            # Extract published date
            published_parsed = entry.get("published_parsed") or entry.get("updated_parsed")
            if published_parsed:
                published = datetime(*published_parsed[:6])
            else:
                # Fallback to current time if no date
                published = datetime.now()

            # Extract summary/description
            summary = entry.get("summary", "") or entry.get("description", "")

            # Clean HTML tags from summary
            summary = re.sub(r"<[^>]+>", "", summary)

            # Extract domain
            domain = urlparse(url).netloc

            return {
                "url": url,
                "title": title,
                "summary": summary,
                "published": published,
                "source": source_name,
                "domain": domain,
                "quality_score": quality_score,
                "discovered_at": datetime.now(),
            }

        except Exception as e:
            logger.debug(f"Failed to parse RSS entry: {e}")
            return None

    def _discover_search_api(self) -> List[Dict[str, Any]]:
        """
        Discover articles via search APIs (SerpAPI, etc.).

        Returns:
            List of article metadata from search APIs
        """
        # Placeholder for API-based discovery
        logger.info("Search API discovery not yet implemented")
        return []

    def get_search_keywords(self) -> List[str]:
        """
        Generate search keywords for this ticker.

        Returns:
            List of search keyword strings
        """
        templates = self.sources.get("search_templates", {})
        earnings_templates = templates.get("earnings_release", [])

        keywords = []
        for template in earnings_templates:
            keyword = template.format(ticker=self.ticker, company=self.company_name)
            keywords.append(keyword)

        logger.debug(f"Generated {len(keywords)} search keywords")
        return keywords
