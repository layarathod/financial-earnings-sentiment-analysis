"""
robots.txt compliance checker for polite web scraping.
"""

import time
from typing import Dict, Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from app.utils.logger import get_logger

logger = get_logger(__name__)


class RobotsChecker:
    """
    Checks robots.txt compliance and manages crawl delays.
    """

    def __init__(self, user_agent: str, respect_robots: bool = True):
        """
        Initialize robots.txt checker.

        Args:
            user_agent: User agent string for the bot
            respect_robots: Whether to respect robots.txt rules
        """
        self.user_agent = user_agent
        self.respect_robots = respect_robots

        # Cache robots.txt parsers per domain
        self._parsers: Dict[str, RobotFileParser] = {}

        # Track last access time per domain for crawl delay
        self._last_access: Dict[str, float] = {}

        logger.debug(f"RobotsChecker initialized (respect_robots={respect_robots})")

    def can_fetch(self, url: str) -> bool:
        """
        Check if URL can be fetched according to robots.txt.

        Args:
            url: URL to check

        Returns:
            True if URL can be fetched
        """
        if not self.respect_robots:
            logger.debug("robots.txt checking disabled")
            return True

        try:
            parsed = urlparse(url)
            domain = f"{parsed.scheme}://{parsed.netloc}"

            # Get or create parser for this domain
            parser = self._get_parser(domain)

            if parser is None:
                # If we can't fetch robots.txt, allow by default
                logger.debug(f"No robots.txt for {domain}, allowing")
                return True

            # Check if path is allowed
            can_fetch = parser.can_fetch(self.user_agent, url)

            if not can_fetch:
                logger.warning(f"robots.txt disallows: {url}")
            else:
                logger.debug(f"robots.txt allows: {url}")

            return can_fetch

        except Exception as e:
            logger.error(f"Error checking robots.txt for {url}: {e}")
            # On error, allow by default (be permissive)
            return True

    def get_crawl_delay(self, url: str) -> Optional[float]:
        """
        Get crawl delay for domain from robots.txt.

        Args:
            url: URL to check

        Returns:
            Crawl delay in seconds, or None
        """
        if not self.respect_robots:
            return None

        try:
            parsed = urlparse(url)
            domain = f"{parsed.scheme}://{parsed.netloc}"

            parser = self._get_parser(domain)

            if parser is None:
                return None

            # Get crawl delay for our user agent
            delay = parser.crawl_delay(self.user_agent)

            if delay:
                logger.debug(f"Crawl delay for {domain}: {delay}s")

            return delay

        except Exception as e:
            logger.debug(f"Error getting crawl delay for {url}: {e}")
            return None

    def wait_if_needed(self, url: str, min_delay: float = 1.0):
        """
        Wait if needed to respect crawl delay.

        Args:
            url: URL being fetched
            min_delay: Minimum delay between requests (seconds)
        """
        try:
            parsed = urlparse(url)
            domain = f"{parsed.scheme}://{parsed.netloc}"

            # Get crawl delay from robots.txt
            robots_delay = self.get_crawl_delay(url)

            # Use the larger of min_delay or robots_delay
            delay = max(min_delay, robots_delay or 0)

            # Check last access time
            if domain in self._last_access:
                elapsed = time.time() - self._last_access[domain]
                if elapsed < delay:
                    wait_time = delay - elapsed
                    logger.debug(f"Waiting {wait_time:.2f}s before fetching {domain}")
                    time.sleep(wait_time)

            # Update last access time
            self._last_access[domain] = time.time()

        except Exception as e:
            logger.debug(f"Error in wait_if_needed: {e}")
            # Default to min_delay
            time.sleep(min_delay)

    def _get_parser(self, domain: str) -> Optional[RobotFileParser]:
        """
        Get cached robots.txt parser for domain.

        Args:
            domain: Domain URL (e.g., https://example.com)

        Returns:
            RobotFileParser or None if unavailable
        """
        # Check cache
        if domain in self._parsers:
            return self._parsers[domain]

        # Fetch and parse robots.txt
        try:
            robots_url = f"{domain}/robots.txt"
            logger.debug(f"Fetching robots.txt from {robots_url}")

            parser = RobotFileParser()
            parser.set_url(robots_url)

            # Read robots.txt with timeout
            try:
                parser.read()
                self._parsers[domain] = parser
                logger.debug(f"Successfully loaded robots.txt for {domain}")
                return parser
            except Exception as e:
                logger.debug(f"Could not fetch robots.txt from {robots_url}: {e}")
                # Cache None to avoid repeated failures
                self._parsers[domain] = None
                return None

        except Exception as e:
            logger.debug(f"Error loading robots.txt for {domain}: {e}")
            self._parsers[domain] = None
            return None

    def clear_cache(self):
        """Clear cached robots.txt parsers."""
        self._parsers.clear()
        self._last_access.clear()
        logger.debug("Robots cache cleared")
