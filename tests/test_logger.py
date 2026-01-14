"""
Tests for logging utilities.
"""

from app.utils.logger import LogTimer, get_logger, setup_logger


def test_setup_logger():
    """Test logger setup."""
    setup_logger(log_level="DEBUG")
    logger = get_logger(__name__)

    assert logger is not None


def test_get_logger_with_name():
    """Test getting logger with name."""
    logger = get_logger("test_module")
    assert logger is not None


def test_log_timer():
    """Test LogTimer context manager."""
    logger = get_logger(__name__)

    with LogTimer("test operation", logger) as timer:
        assert timer is not None
        # Simulate some work
        x = sum(range(100))

    # Should complete without errors


def test_log_timer_with_exception():
    """Test LogTimer handles exceptions."""
    logger = get_logger(__name__)

    try:
        with LogTimer("failing operation", logger):
            raise ValueError("Test error")
    except ValueError:
        pass  # Expected

    # Timer should log error but not suppress exception
