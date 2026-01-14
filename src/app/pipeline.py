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
        from app.discovery.deduplicator import URLDeduplicator
        from app.discovery.filters import ArticleFilter
        from app.discovery.search import ArticleDiscovery

        logger.info("Phase 1: Discovery")

        # Initialize discovery components
        discovery = ArticleDiscovery(
            ticker=self.ticker,
            start_date=self.start_date,
            end_date=self.end_date,
            top_k=self.top_k,
        )

        # Get company name for filtering
        company_name = discovery.company_name

        # Discover articles from RSS feeds
        raw_articles = discovery.discover()
        self.metrics.urls_discovered = len(raw_articles)

        if not raw_articles:
            logger.warning(f"No articles discovered for {self.ticker}")
            self.metrics.urls_to_fetch = 0
            return []

        # Filter by date, domain, etc.
        article_filter = ArticleFilter(
            ticker=self.ticker,
            company_name=company_name,
            start_date=self.start_date,
            end_date=self.end_date,
            exclude_domains=self.settings.exclude_domains,
        )

        filtered_articles = article_filter.filter_and_rank(raw_articles, top_k=self.top_k * 2)
        self.metrics.urls_filtered = len(raw_articles) - len(filtered_articles)

        # Deduplicate URLs
        deduplicator = URLDeduplicator()
        unique_articles = deduplicator.deduplicate(filtered_articles)
        self.metrics.urls_deduplicated = len(filtered_articles) - len(unique_articles)

        # Limit to top K
        final_articles = unique_articles[: self.top_k]
        self.metrics.urls_to_fetch = len(final_articles)

        logger.info(f"Discovery complete: {len(final_articles)} articles ready to fetch")
        logger.info(
            f"Stats: discovered={self.metrics.urls_discovered}, "
            f"filtered={self.metrics.urls_filtered}, "
            f"deduplicated={self.metrics.urls_deduplicated}"
        )

        # Save discovered URLs
        if final_articles:
            self.storage.save_urls(self.ticker, final_articles)

        return final_articles

    def _run_fetching(self, urls: list) -> list:
        """
        Phase 2: Fetch article content.

        Args:
            urls: List of URLs to fetch

        Returns:
            List of raw article data
        """
        from app.fetcher.downloader import ArticleDownloader

        logger.info("Phase 2: Fetching")

        if not urls:
            logger.warning("No URLs to fetch")
            return []

        # Initialize downloader
        downloader = ArticleDownloader()

        raw_articles = []

        for i, url_data in enumerate(urls, 1):
            url = url_data.get("url", "")
            if not url:
                continue

            logger.debug(f"Fetching {i}/{len(urls)}: {url}")

            # Download article
            result = downloader.download(url)

            if result:
                # Save raw HTML
                try:
                    html_path = self.storage.save_raw_html(self.ticker, url, result["html"])
                    result["html_path"] = str(html_path)
                except Exception as e:
                    logger.warning(f"Failed to save raw HTML for {url}: {e}")

                raw_articles.append(result)
                self.metrics.fetch_success += 1
            else:
                self.metrics.fetch_failed += 1
                logger.warning(f"Failed to fetch {url}")

        # Close downloader
        downloader.close()

        logger.info(
            f"Fetching complete: {self.metrics.fetch_success}/{len(urls)} successful "
            f"({self.metrics.fetch_success_rate:.1f}%)"
        )

        return raw_articles

    def _run_extraction(self, raw_articles: list) -> list:
        """
        Phase 3: Extract and clean text.

        Args:
            raw_articles: List of raw article data

        Returns:
            List of parsed article dictionaries
        """
        from app.extraction.cleaner import TextCleaner
        from app.extraction.parser import ArticleParser

        logger.info("Phase 3: Extraction")

        if not raw_articles:
            logger.warning("No articles to extract")
            return []

        # Initialize parser and cleaner
        parser = ArticleParser()
        cleaner = TextCleaner()

        parsed_articles = []

        for i, raw in enumerate(raw_articles, 1):
            url = raw.get("url", "")
            html = raw.get("html", "")

            if not html:
                logger.warning(f"No HTML content for {url}")
                self.metrics.extraction_failed += 1
                continue

            logger.debug(f"Extracting {i}/{len(raw_articles)}: {url}")

            # Parse HTML to extract article
            article = parser.parse(html, url=url)

            if not article:
                logger.warning(f"Failed to extract article from {url}")
                self.metrics.extraction_failed += 1
                continue

            # Clean text
            article = cleaner.clean(article)

            # Check length constraints
            if article.get("too_short"):
                self.metrics.articles_too_short += 1
                logger.debug(f"Article too short: {url}")
                continue

            if article.get("too_long"):
                self.metrics.articles_too_long += 1
                logger.debug(f"Article too long (truncated): {url}")

            # Save parsed article
            try:
                parsed_path = self.storage.save_parsed_article(self.ticker, article)
                article["parsed_path"] = str(parsed_path)
            except Exception as e:
                logger.warning(f"Failed to save parsed article for {url}: {e}")

            parsed_articles.append(article)
            self.metrics.extraction_success += 1

        logger.info(
            f"Extraction complete: {self.metrics.extraction_success}/{len(raw_articles)} successful "
            f"({self.metrics.extraction_success_rate:.1f}%)"
        )

        return parsed_articles

    def _run_analysis(self, parsed_articles: list) -> list:
        """
        Phase 4: Perform sentiment analysis.

        Args:
            parsed_articles: List of parsed article dictionaries

        Returns:
            List of articles with sentiment scores
        """
        from app.analysis.sentiment import get_sentiment_analyzer

        logger.info("Phase 4: Sentiment Analysis")

        if not parsed_articles:
            logger.warning("No articles to analyze")
            return []

        # Initialize sentiment analyzer
        try:
            analyzer = get_sentiment_analyzer(
                model=self.sentiment_model, use_gpu=self.settings.use_gpu
            )
        except Exception as e:
            logger.error(f"Failed to initialize sentiment analyzer: {e}")
            return parsed_articles

        analyzed_articles = []

        for i, article in enumerate(parsed_articles, 1):
            text = article.get("text", "")
            if not text:
                logger.warning(f"No text to analyze for article {i}")
                self.metrics.sentiment_failed += 1
                continue

            logger.debug(f"Analyzing sentiment {i}/{len(parsed_articles)}")

            try:
                # Analyze sentiment
                sentiment = analyzer.analyze(text)
                article["sentiment"] = sentiment

                analyzed_articles.append(article)
                self.metrics.sentiment_analyzed += 1

                logger.debug(
                    f"Sentiment: {sentiment.get('label', 'N/A')} "
                    f"(confidence: {sentiment.get('confidence', 0):.3f})"
                )

            except Exception as e:
                logger.error(f"Failed to analyze article {i}: {e}")
                self.metrics.sentiment_failed += 1
                continue

        logger.info(
            f"Sentiment analysis complete: {self.metrics.sentiment_analyzed}/{len(parsed_articles)} successful "
            f"({self.metrics.sentiment_success_rate:.1f}%)"
        )

        return analyzed_articles

    def _run_reporting(self, analyzed_articles: list) -> Path:
        """
        Phase 5: Generate reports and visualizations.

        Args:
            analyzed_articles: List of articles with sentiment scores

        Returns:
            Path to generated report
        """
        from app.analysis.aggregator import SentimentAggregator

        logger.info("Phase 5: Reporting")

        # Aggregate sentiment scores
        aggregator = SentimentAggregator()

        # Use weighted aggregation based on relevance and quality
        weights = []
        for article in analyzed_articles:
            # Combine relevance and quality scores
            relevance = article.get("relevance_score", 0.5)
            quality = article.get("quality_score", 0.5)
            weight = (relevance * 0.6) + (quality * 0.4)
            weights.append(weight)

        # Get aggregated sentiment
        if weights and len(weights) == len(analyzed_articles):
            aggregated = aggregator.aggregate_weighted(analyzed_articles, weights)
        else:
            aggregated = aggregator.aggregate(analyzed_articles)

        # Build results
        results = {
            "ticker": self.ticker,
            "timestamp": datetime.now().isoformat(),
            "date_range": {
                "start": self.start_date.isoformat(),
                "end": self.end_date.isoformat(),
            },
            "sentiment_summary": aggregated,
            "articles": analyzed_articles,
            "metrics": self.metrics.summary(),
            "configuration": {
                "sentiment_model": self.sentiment_model,
                "top_k": self.top_k,
            },
        }

        # Save to disk
        output_path = self.storage.save_results(self.ticker, results)

        logger.info(f"Results saved to {output_path}")

        # Log summary
        if "overall" in aggregated:
            overall = aggregated["overall"]
            logger.info(
                f"Overall sentiment: {overall.get('label', 'N/A')} "
                f"(confidence: {overall.get('confidence', 0):.3f})"
            )
        if "statistics" in aggregated:
            stats = aggregated["statistics"]
            logger.info(
                f"Distribution: {stats.get('positive_count', 0)} positive, "
                f"{stats.get('negative_count', 0)} negative, "
                f"{stats.get('neutral_count', 0)} neutral"
            )

        return output_path
