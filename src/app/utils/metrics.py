"""
Pipeline metrics and monitoring utilities.
Tracks success rates, failures, and processing statistics.
"""

from dataclasses import dataclass, field
from typing import Dict, List

from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PipelineMetrics:
    """Container for pipeline execution metrics."""

    # Discovery metrics
    urls_discovered: int = 0
    urls_filtered: int = 0
    urls_deduplicated: int = 0
    urls_to_fetch: int = 0

    # Fetch metrics
    fetch_success: int = 0
    fetch_failed: int = 0
    fetch_skipped: int = 0  # robots.txt blocks, etc.

    # Extraction metrics
    extraction_success: int = 0
    extraction_failed: int = 0
    articles_too_short: int = 0
    articles_too_long: int = 0

    # Sentiment analysis metrics
    sentiment_analyzed: int = 0
    sentiment_failed: int = 0

    # Timing
    total_duration_seconds: float = 0.0
    phase_durations: Dict[str, float] = field(default_factory=dict)

    # Errors
    errors: List[str] = field(default_factory=list)

    def add_error(self, error: str) -> None:
        """Record an error message."""
        self.errors.append(error)
        logger.warning(f"Pipeline error recorded: {error}")

    def record_phase_duration(self, phase: str, duration: float) -> None:
        """Record duration for a pipeline phase."""
        self.phase_durations[phase] = duration
        logger.debug(f"Phase '{phase}' completed in {duration:.2f}s")

    @property
    def fetch_success_rate(self) -> float:
        """Calculate fetch success rate."""
        total = self.fetch_success + self.fetch_failed
        if total == 0:
            return 0.0
        return (self.fetch_success / total) * 100

    @property
    def extraction_success_rate(self) -> float:
        """Calculate extraction success rate."""
        total = self.extraction_success + self.extraction_failed
        if total == 0:
            return 0.0
        return (self.extraction_success / total) * 100

    @property
    def sentiment_success_rate(self) -> float:
        """Calculate sentiment analysis success rate."""
        total = self.sentiment_analyzed + self.sentiment_failed
        if total == 0:
            return 0.0
        return (self.sentiment_analyzed / total) * 100

    def summary(self) -> Dict:
        """Generate summary dictionary for reporting."""
        return {
            "discovery": {
                "urls_discovered": self.urls_discovered,
                "urls_filtered": self.urls_filtered,
                "urls_deduplicated": self.urls_deduplicated,
                "urls_to_fetch": self.urls_to_fetch,
            },
            "fetching": {
                "success": self.fetch_success,
                "failed": self.fetch_failed,
                "skipped": self.fetch_skipped,
                "success_rate_pct": round(self.fetch_success_rate, 2),
            },
            "extraction": {
                "success": self.extraction_success,
                "failed": self.extraction_failed,
                "too_short": self.articles_too_short,
                "too_long": self.articles_too_long,
                "success_rate_pct": round(self.extraction_success_rate, 2),
            },
            "sentiment": {
                "analyzed": self.sentiment_analyzed,
                "failed": self.sentiment_failed,
                "success_rate_pct": round(self.sentiment_success_rate, 2),
            },
            "performance": {
                "total_duration_seconds": round(self.total_duration_seconds, 2),
                "phase_durations": {k: round(v, 2) for k, v in self.phase_durations.items()},
            },
            "errors": {
                "count": len(self.errors),
                "messages": self.errors[:10],  # Limit to first 10
            },
        }

    def log_summary(self) -> None:
        """Log metrics summary."""
        logger.info("=" * 60)
        logger.info("PIPELINE METRICS SUMMARY")
        logger.info("=" * 60)
        logger.info(f"URLs discovered: {self.urls_discovered}")
        logger.info(f"URLs to fetch: {self.urls_to_fetch}")
        logger.info(
            f"Fetch success: {self.fetch_success}/{self.urls_to_fetch} ({self.fetch_success_rate:.1f}%)"
        )
        logger.info(
            f"Extraction success: {self.extraction_success} ({self.extraction_success_rate:.1f}%)"
        )
        logger.info(f"Sentiment analyzed: {self.sentiment_analyzed}")
        logger.info(f"Total duration: {self.total_duration_seconds:.2f}s")
        if self.errors:
            logger.warning(f"Errors encountered: {len(self.errors)}")
        logger.info("=" * 60)
