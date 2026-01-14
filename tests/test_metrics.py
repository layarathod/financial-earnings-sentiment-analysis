"""
Tests for metrics tracking.
"""

from app.utils.metrics import PipelineMetrics


def test_metrics_initialization():
    """Test metrics initialization."""
    metrics = PipelineMetrics()

    assert metrics.urls_discovered == 0
    assert metrics.fetch_success == 0
    assert metrics.sentiment_analyzed == 0
    assert len(metrics.errors) == 0


def test_metrics_add_error():
    """Test adding errors."""
    metrics = PipelineMetrics()

    metrics.add_error("Test error 1")
    metrics.add_error("Test error 2")

    assert len(metrics.errors) == 2
    assert "Test error 1" in metrics.errors


def test_metrics_success_rates():
    """Test success rate calculations."""
    metrics = PipelineMetrics()

    # Test with no data
    assert metrics.fetch_success_rate == 0.0

    # Test with data
    metrics.fetch_success = 8
    metrics.fetch_failed = 2

    assert metrics.fetch_success_rate == 80.0


def test_metrics_record_phase_duration():
    """Test phase duration recording."""
    metrics = PipelineMetrics()

    metrics.record_phase_duration("discovery", 1.5)
    metrics.record_phase_duration("fetching", 3.2)

    assert metrics.phase_durations["discovery"] == 1.5
    assert metrics.phase_durations["fetching"] == 3.2


def test_metrics_summary():
    """Test metrics summary generation."""
    metrics = PipelineMetrics()

    metrics.urls_discovered = 50
    metrics.urls_to_fetch = 20
    metrics.fetch_success = 18
    metrics.fetch_failed = 2
    metrics.sentiment_analyzed = 15

    summary = metrics.summary()

    assert summary["discovery"]["urls_discovered"] == 50
    assert summary["fetching"]["success"] == 18
    assert summary["fetching"]["success_rate_pct"] == 90.0
    assert summary["sentiment"]["analyzed"] == 15
