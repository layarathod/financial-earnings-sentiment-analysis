"""
Text cleaning and normalization for extracted articles.
"""

import re
from typing import Dict, Any

from app.config.settings import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TextCleaner:
    """
    Cleans and normalizes extracted article text.
    """

    def __init__(self):
        """Initialize text cleaner."""
        self.settings = get_settings()

    def clean(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean article text and metadata.

        Args:
            article: Article dictionary with 'text' field

        Returns:
            Article dictionary with cleaned text
        """
        if not article or "text" not in article:
            logger.warning("No text to clean in article")
            return article

        original_text = article["text"]
        cleaned_text = self._clean_text(original_text)

        # Update article
        article["text"] = cleaned_text
        article["word_count"] = len(cleaned_text.split())

        # Check length constraints
        min_length = self.settings.min_article_length
        max_length = self.settings.max_article_length

        if len(cleaned_text) < min_length:
            logger.warning(
                f"Article too short: {len(cleaned_text)} chars (min: {min_length})"
            )
            article["too_short"] = True
        elif len(cleaned_text) > max_length:
            logger.warning(
                f"Article too long: {len(cleaned_text)} chars (max: {max_length})"
            )
            article["too_long"] = True
            # Optionally truncate
            article["text"] = cleaned_text[:max_length]
            article["truncated"] = True

        logger.debug(
            f"Cleaned text: {len(original_text)} -> {len(cleaned_text)} chars, "
            f"{article['word_count']} words"
        )

        return article

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Fix encoding issues
        text = self._fix_encoding(text)

        # Normalize whitespace
        text = self._normalize_whitespace(text)

        # Normalize quotes and dashes
        text = self._normalize_punctuation(text)

        # Remove URLs (optional - keep for now)
        # text = self._remove_urls(text)

        # Remove email addresses (optional)
        text = self._remove_emails(text)

        # Remove excessive punctuation
        text = self._clean_punctuation(text)

        # Final whitespace cleanup
        text = text.strip()

        return text

    def _fix_encoding(self, text: str) -> str:
        """
        Fix common encoding issues.

        Args:
            text: Input text

        Returns:
            Fixed text
        """
        # Common encoding fixes
        replacements = {
            "\u2018": "'",  # Left single quote
            "\u2019": "'",  # Right single quote
            "\u201c": '"',  # Left double quote
            "\u201d": '"',  # Right double quote
            "\u2013": "-",  # En dash
            "\u2014": "--",  # Em dash
            "\u2026": "...",  # Ellipsis
            "\xa0": " ",  # Non-breaking space
            "\u00a0": " ",  # Non-breaking space (alternate)
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text

    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace.

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        # Replace multiple spaces with single space
        text = re.sub(r" +", " ", text)

        # Replace multiple newlines with double newline (paragraph break)
        text = re.sub(r"\n\n+", "\n\n", text)

        # Remove spaces before/after newlines
        text = re.sub(r" *\n *", "\n", text)

        return text

    def _normalize_punctuation(self, text: str) -> str:
        """
        Normalize quotes, dashes, etc.

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        # Standardize quotes (if not already done in encoding fix)
        text = re.sub(r"[''`]", "'", text)
        text = re.sub(r"[""«»]", '"', text)

        # Standardize dashes
        text = re.sub(r"—|–", "--", text)

        return text

    def _remove_urls(self, text: str) -> str:
        """
        Remove URLs from text.

        Args:
            text: Input text

        Returns:
            Text without URLs
        """
        # Remove http(s) URLs
        text = re.sub(
            r"https?://[^\s]+",
            "",
            text,
            flags=re.IGNORECASE,
        )

        # Remove www URLs
        text = re.sub(r"www\.[^\s]+", "", text, flags=re.IGNORECASE)

        return text

    def _remove_emails(self, text: str) -> str:
        """
        Remove email addresses.

        Args:
            text: Input text

        Returns:
            Text without emails
        """
        text = re.sub(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "",
            text,
        )

        return text

    def _clean_punctuation(self, text: str) -> str:
        """
        Clean excessive or malformed punctuation.

        Args:
            text: Input text

        Returns:
            Cleaned text
        """
        # Remove repeated punctuation (e.g., "!!!" -> "!")
        text = re.sub(r"([!?.]){2,}", r"\1", text)

        # Fix spacing around punctuation
        text = re.sub(r"\s+([,.!?;:])", r"\1", text)  # Remove space before
        text = re.sub(r"([,.!?;:])([^\s])", r"\1 \2", text)  # Add space after

        return text


def clean_article(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to clean article.

    Args:
        article: Article dictionary

    Returns:
        Cleaned article
    """
    cleaner = TextCleaner()
    return cleaner.clean(article)
