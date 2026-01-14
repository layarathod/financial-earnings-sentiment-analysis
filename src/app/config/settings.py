"""
Configuration management using Pydantic Settings.
Supports environment variables and config files.
"""

from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation and type safety."""

    model_config = SettingsConfigDict(
        env_prefix="EARNINGS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Project paths
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path("data"))
    output_dir: Path = Field(default_factory=lambda: Path("outputs"))
    config_dir: Path = Field(default_factory=lambda: Path("configs"))

    # Data subdirectories
    raw_data_dir: Path = Field(default_factory=lambda: Path("data/raw"))
    parsed_data_dir: Path = Field(default_factory=lambda: Path("data/parsed"))
    results_data_dir: Path = Field(default_factory=lambda: Path("data/results"))
    cache_dir: Path = Field(default_factory=lambda: Path("data/cache"))

    # Output subdirectories
    reports_dir: Path = Field(default_factory=lambda: Path("outputs/reports"))
    plots_dir: Path = Field(default_factory=lambda: Path("outputs/plots"))

    # Logging
    log_level: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR)")
    log_to_file: bool = Field(default=True, description="Whether to log to file")
    log_file: str = Field(default="outputs/earnings_analyzer.log", description="Log file path")

    # HTTP Client settings
    user_agent: str = Field(
        default="EarningsAnalyzer/0.1.0 (Educational Research; +https://github.com/yourorg/earnings-analyzer)",
        description="User agent for HTTP requests",
    )
    request_timeout: int = Field(default=30, description="HTTP request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries for failed requests")
    retry_delay: float = Field(default=1.0, description="Delay between retries in seconds")
    rate_limit_delay: float = Field(
        default=1.0, description="Minimum delay between requests to same domain (seconds)"
    )
    respect_robots_txt: bool = Field(default=True, description="Whether to respect robots.txt")

    # Discovery settings
    default_search_window_days: int = Field(
        default=7, description="Default window for article search (days)"
    )
    default_top_k: int = Field(default=20, description="Default number of articles to fetch")
    max_articles_per_source: int = Field(
        default=10, description="Maximum articles to fetch from a single source"
    )
    enable_rss: bool = Field(default=True, description="Enable RSS feed discovery")
    enable_search_api: bool = Field(default=False, description="Enable search API (SerpAPI, etc.)")

    # Content filtering
    min_article_length: int = Field(
        default=100, description="Minimum article length in characters"
    )
    max_article_length: int = Field(
        default=50000, description="Maximum article length in characters"
    )
    exclude_domains: List[str] = Field(
        default_factory=lambda: [
            "twitter.com",
            "facebook.com",
            "reddit.com",
            "youtube.com",
        ],
        description="Domains to exclude from scraping",
    )

    # Sentiment analysis
    sentiment_model: str = Field(
        default="vader", description="Sentiment model to use (vader, finbert, both)"
    )
    finbert_model_name: str = Field(
        default="ProsusAI/finbert",
        description="HuggingFace model name for FinBERT",
    )
    sentiment_batch_size: int = Field(default=8, description="Batch size for sentiment analysis")
    use_gpu: bool = Field(default=False, description="Use GPU for transformers if available")

    # Reporting
    generate_html: bool = Field(default=True, description="Generate HTML report")
    generate_csv: bool = Field(default=True, description="Generate CSV export")
    generate_plots: bool = Field(default=True, description="Generate visualizations")
    plot_format: str = Field(default="png", description="Plot format (png, svg, pdf)")
    plot_dpi: int = Field(default=300, description="Plot DPI for raster formats")

    # API Keys (optional)
    serpapi_key: Optional[str] = Field(default=None, description="SerpAPI key for search")
    newsapi_key: Optional[str] = Field(default=None, description="NewsAPI key")

    # Advanced features (stretch goals)
    enable_aspect_extraction: bool = Field(default=False, description="Enable aspect-based sentiment")
    enable_deduplication: bool = Field(default=True, description="Enable content deduplication")
    deduplication_threshold: float = Field(
        default=0.85, description="Similarity threshold for deduplication (0-1)"
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper

    @field_validator("sentiment_model")
    @classmethod
    def validate_sentiment_model(cls, v: str) -> str:
        """Validate sentiment model choice."""
        valid_models = ["vader", "finbert", "both"]
        v_lower = v.lower()
        if v_lower not in valid_models:
            raise ValueError(f"sentiment_model must be one of {valid_models}")
        return v_lower

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            self.data_dir,
            self.raw_data_dir,
            self.parsed_data_dir,
            self.results_data_dir,
            self.cache_dir,
            self.output_dir,
            self.reports_dir,
            self.plots_dir,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    @property
    def sources_config_path(self) -> Path:
        """Path to sources configuration file."""
        return self.project_root / self.config_dir / "sources.yaml"

    def __repr__(self) -> str:
        """Pretty representation."""
        return f"Settings(log_level={self.log_level}, sentiment_model={self.sentiment_model})"


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.ensure_directories()
    return _settings


def reset_settings() -> None:
    """Reset settings (mainly for testing)."""
    global _settings
    _settings = None
