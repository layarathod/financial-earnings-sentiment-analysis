"""
Main pipeline orchestrator for earnings sentiment analysis.
Coordinates discovery, fetching, extraction, analysis, and reporting.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from app.config.settings import get_settings
from app.utils.logger import LogTimer, get_logger
from app.utils.metrics import PipelineMetrics
from app.utils.storage import StorageManager

logger = get_logger(__name__)


class Pipeline:
    """
    Orchestrates the end-to-end earnings sentiment analysis pipeline.

    Phases:
        1. Discovery: Find relevant articles
        2. Fetching: Download article content
        3. Extraction: Parse and clean text
        4. Analysis: Run sentiment models
        5. Reporting: Generate outputs
    """

    def __init__(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        top_k: int = 20,
        sentiment_model: Optional[str] = None,
        output_dir: Optional[Path] = None,
        use_cache: bool = True,
    ):
        """
        Initialize pipeline.

        Args:
            ticker: Stock ticker symbol
            start_date: Start of date range for articles
            end_date: End of date range for articles
            top_k: Number of articles to analyze
            sentiment_model: Sentiment model to use (vader, finbert, both)
            output_dir: Custom output directory
            use_cache: Whether to use cached data
        """
        self.ticker = ticker.upper()
        self.start_date = start_date
        self.end_date = end_date
        self.top_k = top_k
        self.use_cache = use_cache

        self.settings = get_settings()
        self.sentiment_model = sentiment_model or self.settings.sentiment_model
        self.output_dir = output_dir or self.settings.output_dir

        self.storage = StorageManager()
        self.metrics = PipelineMetrics()

        logger.info(f"Pipeline initialized for {self.ticker}")
        logger.info(f"Date range: {self.start_date.date()} to {self.end_date.date()}")
        logger.info(f"Target articles: {self.top_k}")
        logger.info(f"Sentiment model: {self.sentiment_model}")

    def run(self) -> Dict[str, Any]:
        """
        Run the complete pipeline.

        Returns:
            Dictionary containing results and metadata
        """
        start_time = time.time()
        logger.info("Starting pipeline execution")

        try:
            # Phase 1: Discovery
            with LogTimer("Article Discovery", logger):
                urls = self._run_discovery()

            # Phase 2: Fetching
            with LogTimer("Content Fetching", logger):
                raw_articles = self._run_fetching(urls)

            # Phase 3: Extraction
            with LogTimer("Text Extraction", logger):
                parsed_articles = self._run_extraction(raw_articles)

            # Phase 4: Analysis
            with LogTimer("Sentiment Analysis", logger):
                analyzed_articles = self._run_analysis(parsed_articles)

            # Phase 5: Reporting
            with LogTimer("Report Generation", logger):
                report_path = self._run_reporting(analyzed_articles)

            # Record total duration
            self.metrics.total_duration_seconds = time.time() - start_time

            # Log final metrics
            self.metrics.log_summary()

            return {
                "ticker": self.ticker,
                "timestamp": datetime.now().isoformat(),
                "num_articles": len(analyzed_articles),
                "output_path": str(report_path),
                "metrics": self.metrics.summary(),
            }

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            self.metrics.add_error(str(e))
            raise

    def run_discovery(self) -> Dict[str, Any]:
        """
        Run only the discovery phase (for dry runs).

        Returns:
            Discovery results
        """
        urls = self._run_discovery()
        return {"ticker": self.ticker, "urls": urls, "count": len(urls)}

    def _run_discovery(self) -> list:
        """
        Phase 1: Discover relevant articles.

        Returns:
            List of URL dictionaries with metadata
        """
        logger.info("Phase 1: Discovery")

        # TODO: Implement in Chunk 2
        # For now, return mock data
        logger.warning("Discovery not yet implemented - using mock data")

        mock_urls = [
            {
                "url": f"https://example.com/article-{i}",
                "title": f"Mock {self.ticker} Earnings Article {i}",
                "source": "example.com",
                "published": datetime.now().isoformat(),
                "relevance_score": 0.9 - (i * 0.05),
            }
            for i in range(min(5, self.top_k))
        ]

        self.metrics.urls_discovered = len(mock_urls)
        self.metrics.urls_to_fetch = len(mock_urls)

        logger.info(f"Discovered {len(mock_urls)} articles")
        return mock_urls

    def _run_fetching(self, urls: list) -> list:
        """
        Phase 2: Fetch article content.

        Args:
            urls: List of URLs to fetch

        Returns:
            List of raw article data
        """
        logger.info("Phase 2: Fetching")

        # TODO: Implement in Chunk 3
        logger.warning("Fetching not yet implemented - using mock data")

        raw_articles = []
        for url_data in urls:
            raw_articles.append(
                {"url": url_data["url"], "html": "<html><body>Mock content</body></html>"}
            )
            self.metrics.fetch_success += 1

        logger.info(f"Fetched {len(raw_articles)} articles")
        return raw_articles

    def _run_extraction(self, raw_articles: list) -> list:
        """
        Phase 3: Extract and clean text.

        Args:
            raw_articles: List of raw article data

        Returns:
            List of parsed article dictionaries
        """
        logger.info("Phase 3: Extraction")

        # TODO: Implement in Chunk 3
        logger.warning("Extraction not yet implemented - using mock data")

        parsed_articles = []
        for raw in raw_articles:
            parsed_articles.append(
                {
                    "url": raw["url"],
                    "title": f"{self.ticker} Reports Strong Earnings",
                    "text": "This is mock article text about earnings results.",
                    "author": "Unknown",
                    "published": datetime.now().isoformat(),
                    "word_count": 50,
                }
            )
            self.metrics.extraction_success += 1

        logger.info(f"Extracted {len(parsed_articles)} articles")
        return parsed_articles

    def _run_analysis(self, parsed_articles: list) -> list:
        """
        Phase 4: Perform sentiment analysis.

        Args:
            parsed_articles: List of parsed article dictionaries

        Returns:
            List of articles with sentiment scores
        """
        logger.info("Phase 4: Sentiment Analysis")

        # TODO: Implement in Chunk 4
        logger.warning("Sentiment analysis not yet implemented - using mock data")

        analyzed_articles = []
        for article in parsed_articles:
            article["sentiment"] = {
                "model": self.sentiment_model,
                "label": "positive",
                "score": 0.75,
                "compound": 0.5,
            }
            analyzed_articles.append(article)
            self.metrics.sentiment_analyzed += 1

        logger.info(f"Analyzed {len(analyzed_articles)} articles")
        return analyzed_articles

    def _run_reporting(self, analyzed_articles: list) -> Path:
        """
        Phase 5: Generate reports and visualizations.

        Args:
            analyzed_articles: List of articles with sentiment scores

        Returns:
            Path to generated report
        """
        logger.info("Phase 5: Reporting")

        # TODO: Implement in Chunk 5
        logger.warning("Reporting not yet implemented - saving basic results")

        results = {
            "ticker": self.ticker,
            "timestamp": datetime.now().isoformat(),
            "date_range": {
                "start": self.start_date.isoformat(),
                "end": self.end_date.isoformat(),
            },
            "articles": analyzed_articles,
            "summary": {
                "total_articles": len(analyzed_articles),
                "average_sentiment": 0.75,
                "positive_count": len(analyzed_articles),
                "negative_count": 0,
                "neutral_count": 0,
            },
            "metrics": self.metrics.summary(),
        }

        # Save to disk
        output_path = self.storage.save_results(self.ticker, results)

        logger.info(f"Results saved to {output_path}")
        return output_path
