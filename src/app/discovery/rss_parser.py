"""
Simple RSS feed parser using requests and BeautifulSoup.
Alternative to feedparser for environments where feedparser has dependency issues.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree as ET

import requests
from bs4 import BeautifulSoup

from app.utils.logger import get_logger

logger = get_logger(__name__)


class SimpleRSSParser:
    """
    Simple RSS/Atom feed parser.
    """

    def __init__(self, user_agent: str = "Mozilla/5.0", timeout: int = 30):
        """
        Initialize RSS parser.

        Args:
            user_agent: User agent string for requests
            timeout: Request timeout in seconds
        """
        self.user_agent = user_agent
        self.timeout = timeout

    def parse(self, feed_url: str) -> Dict[str, Any]:
        """
        Parse RSS or Atom feed from URL.

        Args:
            feed_url: URL of the RSS/Atom feed

        Returns:
            Dictionary with feed data and entries
        """
        try:
            logger.debug(f"Fetching feed: {feed_url}")

            # Fetch feed content
            headers = {"User-Agent": self.user_agent}
            response = requests.get(feed_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            # Parse XML
            soup = BeautifulSoup(response.content, "xml")

            # Detect feed type
            if soup.find("rss"):
                entries = self._parse_rss(soup)
                feed_type = "rss"
            elif soup.find("feed"):
                entries = self._parse_atom(soup)
                feed_type = "atom"
            else:
                logger.warning(f"Unknown feed format for {feed_url}")
                return {"bozo": True, "entries": [], "feed_type": "unknown"}

            logger.debug(f"Parsed {len(entries)} entries from {feed_type} feed")

            return {"bozo": False, "entries": entries, "feed_type": feed_type}

        except requests.RequestException as e:
            logger.error(f"Failed to fetch feed {feed_url}: {e}")
            return {"bozo": True, "bozo_exception": str(e), "entries": []}
        except Exception as e:
            logger.error(f"Failed to parse feed {feed_url}: {e}")
            return {"bozo": True, "bozo_exception": str(e), "entries": []}

    def _parse_rss(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Parse RSS 2.0 feed.

        Args:
            soup: BeautifulSoup parsed XML

        Returns:
            List of entry dictionaries
        """
        entries = []

        for item in soup.find_all("item"):
            entry = {}

            # Title
            if item.find("title"):
                entry["title"] = item.find("title").get_text(strip=True)

            # Link
            if item.find("link"):
                entry["link"] = item.find("link").get_text(strip=True)

            # Description/Summary
            if item.find("description"):
                entry["summary"] = item.find("description").get_text(strip=True)
            elif item.find("content:encoded"):
                entry["summary"] = item.find("content:encoded").get_text(strip=True)

            # Published date
            pub_date = item.find("pubDate") or item.find("dc:date")
            if pub_date:
                entry["published_parsed"] = self._parse_date(pub_date.get_text(strip=True))

            # Author
            if item.find("author") or item.find("dc:creator"):
                author_tag = item.find("author") or item.find("dc:creator")
                entry["author"] = author_tag.get_text(strip=True)

            entries.append(entry)

        return entries

    def _parse_atom(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Parse Atom feed.

        Args:
            soup: BeautifulSoup parsed XML

        Returns:
            List of entry dictionaries
        """
        entries = []

        for entry_tag in soup.find_all("entry"):
            entry = {}

            # Title
            if entry_tag.find("title"):
                entry["title"] = entry_tag.find("title").get_text(strip=True)

            # Link
            link_tag = entry_tag.find("link", {"rel": "alternate"}) or entry_tag.find("link")
            if link_tag:
                entry["link"] = link_tag.get("href", "")

            # Summary
            if entry_tag.find("summary"):
                entry["summary"] = entry_tag.find("summary").get_text(strip=True)
            elif entry_tag.find("content"):
                entry["summary"] = entry_tag.find("content").get_text(strip=True)

            # Published/Updated date
            pub_date = entry_tag.find("published") or entry_tag.find("updated")
            if pub_date:
                entry["published_parsed"] = self._parse_date(pub_date.get_text(strip=True))

            # Author
            author_tag = entry_tag.find("author")
            if author_tag and author_tag.find("name"):
                entry["author"] = author_tag.find("name").get_text(strip=True)

            entries.append(entry)

        return entries

    def _parse_date(self, date_str: str) -> Optional[tuple]:
        """
        Parse date string to tuple (compatible with feedparser format).

        Args:
            date_str: Date string in various formats

        Returns:
            Tuple of (year, month, day, hour, minute, second) or None
        """
        try:
            # Try common date formats
            formats = [
                "%a, %d %b %Y %H:%M:%S %z",  # RFC 822
                "%a, %d %b %Y %H:%M:%S %Z",
                "%Y-%m-%dT%H:%M:%S%z",  # ISO 8601
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d %H:%M:%S",
            ]

            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str.strip(), fmt)
                    return (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
                except ValueError:
                    continue

            # If all else fails, try dateutil (more flexible)
            from dateutil import parser

            dt = parser.parse(date_str)
            return (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

        except Exception as e:
            logger.debug(f"Failed to parse date '{date_str}': {e}")
            return None


# Create a mock feedparser module interface
class FeedParserCompat:
    """
    Compatibility layer to mimic feedparser interface.
    """

    def __init__(self):
        self.parser = SimpleRSSParser()

    def parse(self, feed_url: str, agent: str = None) -> Any:
        """
        Parse feed with feedparser-like interface.

        Args:
            feed_url: Feed URL
            agent: User agent string

        Returns:
            Feed result object
        """
        if agent:
            self.parser.user_agent = agent

        result = self.parser.parse(feed_url)

        # Convert to feedparser-like object
        class FeedResult:
            def __init__(self, data):
                self.bozo = data.get("bozo", False)
                self.bozo_exception = data.get("bozo_exception")
                self.entries = data.get("entries", [])

        return FeedResult(result)


# Create global instance
_compat_parser = FeedParserCompat()


def parse(feed_url: str, agent: str = None) -> Any:
    """
    Parse feed (feedparser-compatible function).

    Args:
        feed_url: Feed URL
        agent: User agent

    Returns:
        Parsed feed result
    """
    return _compat_parser.parse(feed_url, agent)
