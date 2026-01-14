"""
Tests for pipeline orchestrator.
"""

from datetime import datetime, timedelta

import pytest

from app.pipeline import Pipeline


def test_pipeline_initialization(test_settings):
    """Test pipeline initialization."""
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()

    pipeline = Pipeline(
        ticker="AAPL",
        start_date=start_date,
        end_date=end_date,
        top_k=10,
    )

    assert pipeline.ticker == "AAPL"
    assert pipeline.top_k == 10
    assert pipeline.start_date == start_date
    assert pipeline.end_date == end_date


def test_pipeline_run_discovery(test_settings):
    """Test discovery phase."""
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()

    pipeline = Pipeline(
        ticker="AAPL",
        start_date=start_date,
        end_date=end_date,
        top_k=5,
    )

    results = pipeline.run_discovery()

    assert "ticker" in results
    assert "urls" in results
    assert results["ticker"] == "AAPL"


def test_pipeline_full_run(test_settings):
    """Test full pipeline run."""
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()

    pipeline = Pipeline(
        ticker="AAPL",
        start_date=start_date,
        end_date=end_date,
        top_k=5,
    )

    results = pipeline.run()

    assert results["ticker"] == "AAPL"
    assert "output_path" in results
    assert "metrics" in results
    assert results["num_articles"] >= 0
