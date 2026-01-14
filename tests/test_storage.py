"""
Tests for storage utilities.
"""

import json

from app.utils.storage import StorageManager


def test_storage_manager_init(test_settings):
    """Test StorageManager initialization."""
    storage = StorageManager()
    assert storage.settings is not None


def test_save_urls(test_settings, mock_urls):
    """Test saving URLs."""
    storage = StorageManager()

    filepath = storage.save_urls("AAPL", mock_urls)

    assert filepath.exists()
    assert filepath.suffix == ".json"

    # Verify content
    with open(filepath, "r") as f:
        data = json.load(f)

    assert data["ticker"] == "AAPL"
    assert len(data["urls"]) == 2


def test_save_raw_html(test_settings):
    """Test saving raw HTML."""
    storage = StorageManager()

    html = "<html><body>Test content</body></html>"
    filepath = storage.save_raw_html("AAPL", "https://example.com/article", html)

    assert filepath.exists()
    assert filepath.suffix == ".html"

    # Verify content
    with open(filepath, "r") as f:
        content = f.read()

    assert content == html


def test_save_parsed_article(test_settings, mock_article_data):
    """Test saving parsed article."""
    storage = StorageManager()

    filepath = storage.save_parsed_article("AAPL", mock_article_data)

    assert filepath.exists()
    assert filepath.suffix == ".json"

    # Verify content
    with open(filepath, "r") as f:
        data = json.load(f)

    assert data["url"] == mock_article_data["url"]
    assert data["title"] == mock_article_data["title"]


def test_save_and_load_results(test_settings):
    """Test saving and loading results."""
    storage = StorageManager()

    results = {
        "ticker": "AAPL",
        "num_articles": 10,
        "average_sentiment": 0.75,
    }

    # Save
    filepath = storage.save_results("AAPL", results)
    assert filepath.exists()

    # Load
    loaded = storage.load_results(filepath)
    assert loaded["ticker"] == "AAPL"
    assert loaded["num_articles"] == 10


def test_list_results(test_settings):
    """Test listing results."""
    storage = StorageManager()

    # Create some results
    storage.save_results("AAPL", {"ticker": "AAPL"})
    storage.save_results("TSLA", {"ticker": "TSLA"})

    # List all
    all_results = storage.list_results()
    assert len(all_results) >= 2

    # List filtered
    aapl_results = storage.list_results("AAPL")
    assert all("AAPL" in str(p) for p in aapl_results)
