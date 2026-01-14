"""
URL and content deduplication for discovered articles.
"""

import hashlib
import re
from typing import Any, Dict, List, Set
from urllib.parse import parse_qs, urlparse, urlunparse

from app.utils.logger import get_logger

logger = get_logger(__name__)


class URLDeduplicator:
    """
    Deduplicates articles based on URL normalization and content similarity.
    """

    def __init__(self):
        """Initialize deduplicator."""
        self.seen_urls: Set[str] = set()
        self.seen_titles: Set[str] = set()

    def deduplicate(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate articles.

        Deduplication strategy:
        1. Normalize URLs (remove tracking params, fragments)
        2. Check for exact URL matches
        3. Check for similar titles (optional)

        Args:
            articles: List of article metadata

        Returns:
            Deduplicated list of articles
        """
        logger.info(f"Deduplicating {len(articles)} articles")

        unique_articles = []
        stats = {"url_duplicates": 0, "title_duplicates": 0, "kept": 0}

        for article in articles:
            # Normalize URL
            normalized_url = self.normalize_url(article.get("url", ""))

            # Check URL duplicates
            if normalized_url in self.seen_urls:
                stats["url_duplicates"] += 1
                logger.debug(f"Duplicate URL: {normalized_url[:60]}")
                continue

            # Check title duplicates (optional, less strict)
            title = article.get("title", "")
            title_hash = self._hash_title(title)

            if title_hash in self.seen_titles and title:
                stats["title_duplicates"] += 1
                logger.debug(f"Duplicate title: {title[:60]}")
                continue

            # Keep this article
            self.seen_urls.add(normalized_url)
            if title:
                self.seen_titles.add(title_hash)

            article["normalized_url"] = normalized_url
            unique_articles.append(article)
            stats["kept"] += 1

        logger.info(
            f"Deduplication: kept {stats['kept']}, "
            f"removed {stats['url_duplicates']} URL duplicates, "
            f"{stats['title_duplicates']} title duplicates"
        )

        return unique_articles

    @staticmethod
    def normalize_url(url: str) -> str:
        """
        Normalize URL for comparison.

        Removes:
        - Tracking parameters (utm_*, fbclid, etc.)
        - Fragments (#section)
        - www. prefix
        - Trailing slashes
        - Protocol (http vs https)

        Args:
            url: Original URL

        Returns:
            Normalized URL string
        """
        if not url:
            return ""

        try:
            parsed = urlparse(url)

            # Remove www.
            netloc = parsed.netloc.lower()
            if netloc.startswith("www."):
                netloc = netloc[4:]

            # Parse query parameters
            query_params = parse_qs(parsed.query)

            # Remove tracking parameters
            tracking_params = {
                "utm_source",
                "utm_medium",
                "utm_campaign",
                "utm_term",
                "utm_content",
                "fbclid",
                "gclid",
                "msclkid",
                "mc_cid",
                "mc_eid",
                "_ga",
                "ref",
                "source",
            }

            clean_params = {k: v for k, v in query_params.items() if k not in tracking_params}

            # Rebuild query string
            clean_query = "&".join(f"{k}={v[0]}" for k, v in sorted(clean_params.items()))

            # Remove trailing slash from path
            path = parsed.path.rstrip("/")

            # Rebuild URL (without scheme and fragment)
            normalized = urlunparse(("", netloc, path, "", clean_query, ""))

            return normalized

        except Exception as e:
            logger.debug(f"Failed to normalize URL {url}: {e}")
            return url

    @staticmethod
    def _hash_title(title: str) -> str:
        """
        Create hash of title for comparison.

        Normalizes title by:
        - Converting to lowercase
        - Removing punctuation
        - Removing extra whitespace

        Args:
            title: Article title

        Returns:
            Hash string
        """
        if not title:
            return ""

        # Normalize
        normalized = title.lower()
        normalized = re.sub(r"[^\w\s]", "", normalized)  # Remove punctuation
        normalized = re.sub(r"\s+", " ", normalized).strip()  # Normalize whitespace

        # Hash
        return hashlib.md5(normalized.encode()).hexdigest()

    def reset(self):
        """Reset seen URLs and titles (for testing)."""
        self.seen_urls.clear()
        self.seen_titles.clear()
        logger.debug("Deduplicator reset")


class ContentDeduplicator:
    """
    Advanced content-based deduplication using similarity hashing.
    (Stretch goal - MinHash/SimHash implementation)
    """

    def __init__(self, threshold: float = 0.85):
        """
        Initialize content deduplicator.

        Args:
            threshold: Similarity threshold (0-1)
        """
        self.threshold = threshold
        self.seen_hashes: Set[str] = set()

    def is_duplicate(self, text: str) -> bool:
        """
        Check if text is duplicate using simple hashing.

        Args:
            text: Text to check

        Returns:
            True if duplicate
        """
        text_hash = self._hash_text(text)

        if text_hash in self.seen_hashes:
            return True

        self.seen_hashes.add(text_hash)
        return False

    @staticmethod
    def _hash_text(text: str) -> str:
        """
        Create hash of text content.

        Args:
            text: Text to hash

        Returns:
            Hash string
        """
        # Normalize text
        normalized = text.lower().strip()
        normalized = re.sub(r"\s+", " ", normalized)

        # Hash
        return hashlib.sha256(normalized.encode()).hexdigest()

    def reset(self):
        """Reset seen hashes."""
        self.seen_hashes.clear()
