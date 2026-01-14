"""
Storage utilities for saving and loading data at different pipeline stages.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from app.config.settings import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class StorageManager:
    """Manages data persistence across pipeline stages."""

    def __init__(self):
        self.settings = get_settings()

    def _generate_filename(self, ticker: str, stage: str, extension: str) -> str:
        """
        Generate timestamped filename.

        Args:
            ticker: Stock ticker symbol
            stage: Pipeline stage (discovery, raw, parsed, results)
            extension: File extension (json, html, txt, csv)

        Returns:
            Filename string
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{ticker}_{stage}_{timestamp}.{extension}"

    def save_urls(self, ticker: str, urls: List[Dict[str, Any]]) -> Path:
        """
        Save discovered URLs to JSON.

        Args:
            ticker: Stock ticker
            urls: List of URL metadata dictionaries

        Returns:
            Path to saved file
        """
        filename = self._generate_filename(ticker, "urls", "json")
        filepath = self.settings.parsed_data_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                {"ticker": ticker, "timestamp": datetime.now().isoformat(), "urls": urls},
                f,
                indent=2,
            )

        logger.info(f"Saved {len(urls)} URLs to {filepath}")
        return filepath

    def save_raw_html(self, ticker: str, url: str, html_content: str) -> Path:
        """
        Save raw HTML content.

        Args:
            ticker: Stock ticker
            url: Source URL
            html_content: Raw HTML string

        Returns:
            Path to saved file
        """
        # Create safe filename from URL
        from urllib.parse import urlparse

        parsed = urlparse(url)
        domain = parsed.netloc.replace(".", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{ticker}_{domain}_{timestamp}.html"

        filepath = self.settings.raw_data_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.debug(f"Saved raw HTML to {filepath}")
        return filepath

    def save_parsed_article(self, ticker: str, article_data: Dict[str, Any]) -> Path:
        """
        Save parsed article with metadata.

        Args:
            ticker: Stock ticker
            article_data: Dictionary containing parsed article data

        Returns:
            Path to saved file
        """
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{ticker}_article_{timestamp}.json"
        filepath = self.settings.parsed_data_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(article_data, f, indent=2, default=str)

        logger.debug(f"Saved parsed article to {filepath}")
        return filepath

    def save_results(self, ticker: str, results: Dict[str, Any]) -> Path:
        """
        Save final analysis results.

        Args:
            ticker: Stock ticker
            results: Analysis results dictionary

        Returns:
            Path to saved file
        """
        filename = self._generate_filename(ticker, "results", "json")
        filepath = self.settings.results_data_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Saved analysis results to {filepath}")
        return filepath

    def load_results(self, filepath: Path) -> Dict[str, Any]:
        """
        Load results from JSON file.

        Args:
            filepath: Path to results file

        Returns:
            Results dictionary
        """
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_results(self, ticker: str = None) -> List[Path]:
        """
        List available result files.

        Args:
            ticker: Optional ticker to filter by

        Returns:
            List of result file paths
        """
        pattern = f"{ticker}_results_*.json" if ticker else "*_results_*.json"
        return sorted(self.settings.results_data_dir.glob(pattern), reverse=True)
