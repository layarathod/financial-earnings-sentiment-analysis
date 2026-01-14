"""
HTTP downloader with retries, rate limiting, and polite behavior.
"""

import time
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config.settings import get_settings
from app.fetcher.robots import RobotsChecker
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ArticleDownloader:
    """
    Downloads article HTML with polite behavior and error handling.
    """

    def __init__(
        self,
        user_agent: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None,
        respect_robots: Optional[bool] = None,
        rate_limit_delay: Optional[float] = None,
    ):
        """
        Initialize downloader.

        Args:
            user_agent: User agent string
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            retry_delay: Delay between retries
            respect_robots: Whether to respect robots.txt
            rate_limit_delay: Minimum delay between requests to same domain
        """
        self.settings = get_settings()

        # Use provided values or fall back to settings
        self.user_agent = user_agent or self.settings.user_agent
        self.timeout = timeout or self.settings.request_timeout
        self.max_retries = max_retries or self.settings.max_retries
        self.retry_delay = retry_delay or self.settings.retry_delay
        self.rate_limit_delay = rate_limit_delay or self.settings.rate_limit_delay
        respect_robots = (
            respect_robots if respect_robots is not None else self.settings.respect_robots_txt
        )

        # Initialize robots.txt checker
        self.robots_checker = RobotsChecker(
            user_agent=self.user_agent, respect_robots=respect_robots
        )

        # Create session with retry strategy
        self.session = self._create_session()

        logger.info(
            f"ArticleDownloader initialized "
            f"(timeout={self.timeout}s, retries={self.max_retries}, "
            f"respect_robots={respect_robots})"
        )

    def _create_session(self) -> requests.Session:
        """
        Create requests session with retry strategy.

        Returns:
            Configured requests.Session
        """
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,  # Exponential backoff
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these status codes
            allowed_methods=["GET", "HEAD"],  # Only retry safe methods
        )

        # Mount adapter with retry strategy
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set default headers
        session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "DNT": "1",  # Do Not Track
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )

        return session

    def download(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Download article HTML from URL.

        Args:
            url: URL to download

        Returns:
            Dictionary with 'html', 'url', 'status_code', 'headers' or None if failed
        """
        try:
            # Check robots.txt
            if not self.robots_checker.can_fetch(url):
                logger.warning(f"Skipping {url} (disallowed by robots.txt)")
                return None

            # Wait if needed for rate limiting
            self.robots_checker.wait_if_needed(url, min_delay=self.rate_limit_delay)

            logger.info(f"Downloading: {url}")

            # Fetch URL
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)

            # Check status code
            response.raise_for_status()

            logger.info(
                f"Successfully downloaded {url} "
                f"({len(response.content)} bytes, status={response.status_code})"
            )

            return {
                "html": response.text,
                "url": url,
                "final_url": response.url,  # After redirects
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "encoding": response.encoding,
            }

        except requests.exceptions.Timeout:
            logger.error(f"Timeout downloading {url}")
            return None

        except requests.exceptions.TooManyRedirects:
            logger.error(f"Too many redirects for {url}")
            return None

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error downloading {url}: {e.response.status_code}")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error downloading {url}: {e}")
            return None

        except Exception as e:
            logger.error(f"Unexpected error downloading {url}: {e}")
            return None

    def download_many(self, urls: list, stop_on_error: bool = False) -> list:
        """
        Download multiple URLs.

        Args:
            urls: List of URLs to download
            stop_on_error: Whether to stop on first error

        Returns:
            List of download results (includes None for failures)
        """
        results = []

        logger.info(f"Starting batch download of {len(urls)} URLs")

        for i, url in enumerate(urls, 1):
            logger.debug(f"Download {i}/{len(urls)}: {url}")

            result = self.download(url)

            if result is None and stop_on_error:
                logger.error(f"Stopping batch download after error on {url}")
                break

            results.append(result)

            # Small delay between requests (in addition to per-domain rate limiting)
            if i < len(urls):
                time.sleep(0.5)

        successful = sum(1 for r in results if r is not None)
        logger.info(
            f"Batch download complete: {successful}/{len(urls)} successful "
            f"({successful/len(urls)*100:.1f}%)"
        )

        return results

    def close(self):
        """Close the session."""
        self.session.close()
        logger.debug("Downloader session closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
