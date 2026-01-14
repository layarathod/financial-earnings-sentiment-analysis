"""
Article text extraction from HTML.
"""

import re
from datetime import datetime
from typing import Any, Dict, Optional

from bs4 import BeautifulSoup

from app.utils.logger import get_logger

logger = get_logger(__name__)


class ArticleParser:
    """
    Extracts article content from HTML.
    """

    def __init__(self):
        """Initialize parser."""
        # Common tags to remove (ads, navigation, etc.)
        self.remove_tags = [
            "script",
            "style",
            "nav",
            "header",
            "footer",
            "aside",
            "iframe",
            "noscript",
            "form",
        ]

        # Common class/id patterns for ads and junk
        self.junk_patterns = [
            r"ad[-_]",
            r"advertisement",
            r"social[-_]",
            r"share",
            r"comment",
            r"related",
            r"sidebar",
            r"widget",
            r"promo",
            r"newsletter",
        ]

    def parse(self, html: str, url: str = "") -> Optional[Dict[str, Any]]:
        """
        Extract article content from HTML.

        Args:
            html: Raw HTML string
            url: Source URL (for context)

        Returns:
            Dictionary with extracted article data or None if parsing fails
        """
        try:
            soup = BeautifulSoup(html, "lxml")

            # Extract metadata
            title = self._extract_title(soup)
            author = self._extract_author(soup)
            published_date = self._extract_date(soup)
            description = self._extract_description(soup)

            # Extract main content
            text = self._extract_text(soup)

            if not text:
                logger.warning(f"No text extracted from {url}")
                return None

            # Calculate word count
            word_count = len(text.split())

            logger.debug(
                f"Extracted article: {word_count} words, title='{title[:50] if title else 'N/A'}'"
            )

            return {
                "url": url,
                "title": title,
                "author": author,
                "published": published_date,
                "description": description,
                "text": text,
                "word_count": word_count,
                "extracted_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error parsing HTML from {url}: {e}")
            return None

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract article title.

        Args:
            soup: BeautifulSoup object

        Returns:
            Title string or None
        """
        # Try <title> tag
        if soup.title:
            title = soup.title.string
            if title:
                # Clean up title (often includes " - Site Name")
                title = re.sub(r"\s*[-|]\s*.*$", "", title.strip())
                return title

        # Try Open Graph title
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()

        # Try article h1
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)

        return None

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract article author.

        Args:
            soup: BeautifulSoup object

        Returns:
            Author string or None
        """
        # Try meta author tag
        author_meta = soup.find("meta", attrs={"name": "author"})
        if author_meta and author_meta.get("content"):
            return author_meta["content"].strip()

        # Try article:author meta tag
        author_article = soup.find("meta", property="article:author")
        if author_article and author_article.get("content"):
            return author_article["content"].strip()

        # Try common author class names
        for class_name in ["author", "byline", "article-author"]:
            author_elem = soup.find(class_=re.compile(class_name, re.I))
            if author_elem:
                return author_elem.get_text(strip=True)

        return None

    def _extract_date(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract publication date.

        Args:
            soup: BeautifulSoup object

        Returns:
            ISO format date string or None
        """
        # Try article:published_time
        published = soup.find("meta", property="article:published_time")
        if published and published.get("content"):
            return published["content"]

        # Try <time> tag
        time_tag = soup.find("time")
        if time_tag:
            # Try datetime attribute first
            if time_tag.get("datetime"):
                return time_tag["datetime"]
            # Fall back to text content
            return time_tag.get_text(strip=True)

        # Try meta datePublished
        date_meta = soup.find("meta", attrs={"name": "datePublished"})
        if date_meta and date_meta.get("content"):
            return date_meta["content"]

        return None

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract article description/summary.

        Args:
            soup: BeautifulSoup object

        Returns:
            Description string or None
        """
        # Try Open Graph description
        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            return og_desc["content"].strip()

        # Try meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            return meta_desc["content"].strip()

        return None

    def _extract_text(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract main article text.

        Args:
            soup: BeautifulSoup object

        Returns:
            Article text or None
        """
        # Remove junk tags
        for tag in self.remove_tags:
            for element in soup.find_all(tag):
                element.decompose()

        # Remove elements with junk class/id
        for pattern in self.junk_patterns:
            for element in soup.find_all(class_=re.compile(pattern, re.I)):
                element.decompose()
            for element in soup.find_all(id=re.compile(pattern, re.I)):
                element.decompose()

        # Try to find article content container
        article_content = None

        # Try <article> tag
        article_tag = soup.find("article")
        if article_tag:
            article_content = article_tag

        # Try common content class names
        if not article_content:
            for class_pattern in ["article[-_]body", "article[-_]content", "post[-_]content", "entry[-_]content"]:
                content = soup.find(class_=re.compile(class_pattern, re.I))
                if content:
                    article_content = content
                    break

        # Fall back to main tag
        if not article_content:
            article_content = soup.find("main")

        # Last resort: find largest text block
        if not article_content:
            article_content = soup.find("body")

        if not article_content:
            return None

        # Extract paragraphs
        paragraphs = []
        for p in article_content.find_all("p"):
            text = p.get_text(strip=True)
            # Filter out very short paragraphs (likely not content)
            if len(text) > 50:
                paragraphs.append(text)

        if not paragraphs:
            # Fall back to all text
            text = article_content.get_text(separator="\n", strip=True)
            return text if len(text) > 100 else None

        # Join paragraphs
        full_text = "\n\n".join(paragraphs)

        return full_text if len(full_text) > 100 else None
