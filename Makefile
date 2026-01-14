.PHONY: help install install-dev test lint format clean run doctor

# Default target
help:
	@echo "Earnings Sentiment Analyzer - Available Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install       Install production dependencies"
	@echo "  make install-dev   Install development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make test          Run test suite"
	@echo "  make lint          Run linters (ruff, mypy)"
	@echo "  make format        Format code (black, isort)"
	@echo "  make doctor        Run diagnostics"
	@echo ""
	@echo "Running:"
	@echo "  make run           Run example analysis (AAPL)"
	@echo "  make run-demo      Run demo with multiple tickers"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         Remove generated files"
	@echo "  make clean-all     Remove all data and outputs"

# Installation
install:
	pip install -r requirements.txt
	pip install -e .

install-dev:
	pip install -r requirements-dev.txt
	pip install -e .

# Testing
test:
	pytest tests/ -v --cov=app --cov-report=term-missing

test-fast:
	pytest tests/ -v -x  # Stop on first failure

# Code quality
lint:
	@echo "Running ruff..."
	ruff check src/
	@echo "Running mypy..."
	mypy src/app --ignore-missing-imports

format:
	@echo "Running black..."
	black src/ tests/
	@echo "Running isort..."
	isort src/ tests/

format-check:
	black --check src/ tests/
	isort --check-only src/ tests/

# Running the application
run:
	python -m app run --ticker AAPL --window 7d --top-k 10

run-dry:
	python -m app run --ticker AAPL --window 7d --top-k 10 --dry-run

run-demo:
	@echo "Running demo for AAPL..."
	python -m app run --ticker AAPL --window 7d --top-k 5
	@echo ""
	@echo "Running demo for TSLA..."
	python -m app run --ticker TSLA --window 7d --top-k 5

# Utilities
doctor:
	python -m app doctor --check-deps

config:
	python -m app config

list-results:
	python -m app list-results --limit 20

# Cleanup
clean:
	@echo "Removing Python artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ htmlcov/
	@echo "Clean complete!"

clean-all: clean
	@echo "Removing data and outputs..."
	rm -rf data/ outputs/
	@echo "All clean!"

# Download models (for FinBERT)
download-models:
	python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; \
		AutoTokenizer.from_pretrained('ProsusAI/finbert'); \
		AutoModelForSequenceClassification.from_pretrained('ProsusAI/finbert')"

# Initialize project directories
init:
	python -m app doctor
	@echo "Project initialized!"
