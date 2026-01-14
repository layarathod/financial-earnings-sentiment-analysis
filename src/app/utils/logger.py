"""
Centralized logging configuration using loguru.
Provides structured logging with file rotation and custom formatting.
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from app.config.settings import get_settings


class LoggerConfig:
    """Logger configuration and setup."""

    def __init__(self):
        self.settings = get_settings()
        self._initialized = False

    def setup(self, log_level: Optional[str] = None) -> None:
        """
        Configure logger with console and file handlers.

        Args:
            log_level: Override default log level from settings
        """
        if self._initialized:
            return

        # Remove default handler
        logger.remove()

        # Use provided level or fall back to settings
        level = log_level or self.settings.log_level

        # Console handler with color
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=level,
            colorize=True,
        )

        # File handler with rotation
        if self.settings.log_to_file:
            log_path = Path(self.settings.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            logger.add(
                log_path,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                level=level,
                rotation="10 MB",  # Rotate when file reaches 10MB
                retention="7 days",  # Keep logs for 7 days
                compression="zip",  # Compress rotated logs
                enqueue=True,  # Thread-safe
            )

        self._initialized = True
        logger.info(f"Logger initialized with level: {level}")

    def get_logger(self, name: Optional[str] = None):
        """
        Get a logger instance with optional name binding.

        Args:
            name: Module or component name for context

        Returns:
            Logger instance
        """
        if not self._initialized:
            self.setup()

        if name:
            return logger.bind(name=name)
        return logger


# Global logger instance
_logger_config: Optional[LoggerConfig] = None


def setup_logger(log_level: Optional[str] = None) -> None:
    """
    Initialize global logger configuration.

    Args:
        log_level: Override default log level
    """
    global _logger_config
    if _logger_config is None:
        _logger_config = LoggerConfig()
    _logger_config.setup(log_level)


def get_logger(name: Optional[str] = None):
    """
    Get configured logger instance.

    Args:
        name: Module name for context binding

    Returns:
        Logger instance

    Example:
        >>> from app.utils.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Starting analysis")
    """
    global _logger_config
    if _logger_config is None:
        _logger_config = LoggerConfig()
        _logger_config.setup()
    return _logger_config.get_logger(name)


# Context managers for timing operations
class LogTimer:
    """Context manager for logging operation duration."""

    def __init__(self, operation_name: str, logger_instance=None):
        self.operation_name = operation_name
        self.logger = logger_instance or logger
        self.start_time = None

    def __enter__(self):
        self.logger.info(f"Starting: {self.operation_name}")
        import time

        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time

        duration = time.time() - self.start_time
        if exc_type is None:
            self.logger.success(f"Completed: {self.operation_name} (took {duration:.2f}s)")
        else:
            self.logger.error(
                f"Failed: {self.operation_name} (took {duration:.2f}s) - {exc_type.__name__}: {exc_val}"
            )
        return False  # Don't suppress exceptions
