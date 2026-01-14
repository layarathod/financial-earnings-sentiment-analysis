"""
Tests for extraction module.
"""

import pytest

from app.extraction.cleaner import TextCleaner
from app.extraction.parser import ArticleParser


class TestArticleParser:
    """Tests for article parser."""

    def test_initialization(self):
        """Test ArticleParser initialization."""
        parser = ArticleParser()

        assert parser is not None
        assert len(parser.remove_tags) > 0

    def test_extract_title_from_title_tag(self):
        """Test title extraction from <title> tag."""
        parser = ArticleParser()

        html = "<html><head><title>Test Article - Example Site</title></head><body></body></html>"

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")

        title = parser._extract_title(soup)

        assert title == "Test Article"

    def test_extract_title_from_og_meta(self):
        """Test title extraction from Open Graph meta."""
        parser = ArticleParser()

        html = '<html><head><meta property="og:title" content="Test Article"></head><body></body></html>'

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")

        title = parser._extract_title(soup)

        assert title == "Test Article"

    def test_extract_author(self):
        """Test author extraction."""
        parser = ArticleParser()

        html = '<html><head><meta name="author" content="John Doe"></head><body></body></html>'

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")

        author = parser._extract_author(soup)

        assert author == "John Doe"

    def test_extract_text_from_paragraphs(self):
        """Test text extraction from paragraphs."""
        parser = ArticleParser()

        html = """
        <html>
        <body>
            <article>
                <p>This is the first paragraph with enough text to be considered content.</p>
                <p>This is the second paragraph also with sufficient length for extraction.</p>
                <p>And here is a third paragraph to make it a proper article.</p>
            </article>
        </body>
        </html>
        """

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")

        text = parser._extract_text(soup)

        assert text is not None
        assert "first paragraph" in text
        assert "second paragraph" in text
        assert "third paragraph" in text

    def test_parse_full_article(self):
        """Test parsing a full article."""
        parser = ArticleParser()

        html = """
        <html>
        <head>
            <title>AAPL Earnings Report</title>
            <meta name="author" content="Jane Smith">
        </head>
        <body>
            <article>
                <h1>Apple Reports Strong Q4 Earnings</h1>
                <p>Apple Inc. reported strong quarterly earnings that exceeded analyst expectations.</p>
                <p>The company's revenue grew by 15% year-over-year, driven by strong iPhone sales.</p>
                <p>Management provided optimistic guidance for the upcoming quarter.</p>
            </article>
        </body>
        </html>
        """

        result = parser.parse(html, url="https://example.com/article")

        assert result is not None
        assert result["title"] == "AAPL Earnings Report"
        assert result["author"] == "Jane Smith"
        assert "Apple Inc." in result["text"]
        assert result["word_count"] > 0

    def test_parse_returns_none_for_empty_html(self):
        """Test that parsing empty HTML returns None."""
        parser = ArticleParser()

        result = parser.parse("", url="https://example.com")

        assert result is None


class TestTextCleaner:
    """Tests for text cleaner."""

    def test_initialization(self):
        """Test TextCleaner initialization."""
        cleaner = TextCleaner()

        assert cleaner is not None

    def test_fix_encoding(self):
        """Test encoding fixes."""
        cleaner = TextCleaner()

        text = "Apple's earnings"  # Smart quote
        fixed = cleaner._fix_encoding(text)

        assert "'" in fixed  # Regular quote
        assert "'" not in fixed  # Smart quote removed

    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        cleaner = TextCleaner()

        text = "This  has   extra    spaces\n\n\n\nand newlines"
        normalized = cleaner._normalize_whitespace(text)

        assert "  " not in normalized  # No double spaces
        assert "\n\n\n" not in normalized  # Max double newlines

    def test_remove_emails(self):
        """Test email removal."""
        cleaner = TextCleaner()

        text = "Contact us at test@example.com for more info."
        cleaned = cleaner._remove_emails(text)

        assert "test@example.com" not in cleaned

    def test_clean_article(self):
        """Test cleaning full article."""
        cleaner = TextCleaner()

        article = {
            "text": "This  is   a   test    article\n\n\n\nwith  bad   formatting",
            "word_count": 0,
        }

        cleaned = cleaner.clean(article)

        assert "  " not in cleaned["text"]
        assert cleaned["word_count"] > 0

    def test_article_too_short_flag(self, test_settings):
        """Test that too-short articles are flagged."""
        cleaner = TextCleaner()

        article = {
            "text": "Short text.",
            "word_count": 2,
        }

        cleaned = cleaner.clean(article)

        assert cleaned.get("too_short") is True

    def test_clean_punctuation(self):
        """Test punctuation cleaning."""
        cleaner = TextCleaner()

        text = "What!!! Really??? Yes."
        cleaned = cleaner._clean_punctuation(text)

        assert "!!!" not in cleaned
        assert "???" not in cleaned
