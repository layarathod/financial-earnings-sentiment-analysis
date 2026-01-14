# Financial Earnings Sentiment Analysis

An end-to-end Python NLP pipeline for analyzing sentiment in earnings-related financial articles. Automatically discovers, fetches, extracts, and analyzes news articles around quarterly earnings announcements.

## Features

- **Automated Article Discovery**: RSS feeds + optional search APIs
- **Polite Web Scraping**: Respects robots.txt, rate limiting, and ethical guidelines
- **Multi-Model Sentiment**: VADER (baseline) + FinBERT (financial-tuned transformer)
- **Aspect-Based Analysis**: Extract sentiment for guidance, revenue, EPS, margins (stretch goal)
- **Rich Reporting**: CSV exports, HTML dashboards, visualizations
- **Production-Ready**: Logging, metrics, error handling, tests

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/financial-earnings-sentiment-analysis.git
cd financial-earnings-sentiment-analysis

# Install dependencies
make install

# Or manually:
pip install -r requirements.txt
pip install -e .

# Run diagnostics
make doctor
```

### Basic Usage

```bash
# Analyze AAPL earnings articles from last 7 days
python -m app run --ticker AAPL --window 7d --top-k 20

# Use a different time window
python -m app run --ticker TSLA --window 14d --top-k 30

# Dry run (discovery only, no fetching)
python -m app run --ticker GOOGL --window 7d --dry-run

# Use FinBERT instead of VADER
python -m app run --ticker MSFT --window 7d --sentiment-model finbert
```

### CLI Commands

```bash
# Run analysis
python -m app run --ticker AAPL --window 7d --top-k 20

# List available results
python -m app list-results --ticker AAPL

# Show configuration
python -m app config

# Run diagnostics
python -m app doctor --check-deps
```

## Project Structure

```
financial-earnings-sentiment-analysis/
├── src/app/                  # Main application code
│   ├── config/               # Configuration management
│   ├── discovery/            # Article discovery (RSS, search APIs)
│   ├── fetcher/              # HTTP client, robots.txt compliance
│   ├── extraction/           # HTML parsing, text extraction
│   ├── analysis/             # Sentiment models (VADER, FinBERT)
│   ├── reporting/            # Visualization and report generation
│   └── utils/                # Logging, storage, metrics
├── tests/                    # Test suite
├── data/                     # Data storage (gitignored)
│   ├── raw/                  # Raw HTML files
│   ├── parsed/               # Extracted text + metadata
│   ├── results/              # Final analysis results
│   └── cache/                # HTTP cache
├── outputs/                  # Generated reports (gitignored)
│   ├── reports/              # HTML reports
│   └── plots/                # Visualizations
├── configs/                  # Configuration files
└── notebooks/                # Analysis notebooks
```

## Configuration

Create a `.env` file (see `.env.example`):

```bash
EARNINGS_LOG_LEVEL=INFO
EARNINGS_SENTIMENT_MODEL=vader
EARNINGS_RESPECT_ROBOTS_TXT=true
```

Or modify `configs/default.yaml` for source configuration.

## Development

### Setup Development Environment

```bash
make install-dev
```

### Run Tests

```bash
make test           # Run full test suite
make test-fast      # Stop on first failure
```

### Code Quality

```bash
make lint           # Run ruff and mypy
make format         # Format with black and isort
```

### Make Commands

```bash
make help           # Show all available commands
make run            # Run example analysis
make clean          # Remove artifacts
make doctor         # Run diagnostics
```

## Implementation Roadmap

### MVP (Chunk 1-4) ✅ In Progress

- [x] Project scaffold, config, logging, CLI
- [ ] RSS-based article discovery
- [ ] Polite HTTP fetching with robots.txt
- [ ] Text extraction (newspaper3k)
- [ ] VADER sentiment baseline
- [ ] CSV + HTML reporting

### Stretch Goals (Chunk 5-6)

- [ ] FinBERT transformer model
- [ ] Aspect-based sentiment
- [ ] Advanced deduplication (MinHash)
- [ ] SerpAPI integration
- [ ] Interactive Plotly dashboards
- [ ] Return correlation analysis
- [ ] Docker containerization

## Data Sources

**Tier 1 (Premium)**:
- Reuters, Bloomberg, Wall Street Journal, Financial Times

**Tier 2 (Major Outlets)**:
- CNBC, MarketWatch, Yahoo Finance, Barron's

**Tier 3 (Analysis)**:
- Seeking Alpha, The Motley Fool, IBD

See `configs/sources.yaml` for full configuration.

## Architecture

```
CLI Entry → Pipeline Orchestrator
              ↓
    ┌─────────┼─────────┬─────────┬─────────┐
    ↓         ↓         ↓         ↓         ↓
Discovery → Fetcher → Extractor → Analyzer → Reporter
    ↓         ↓         ↓         ↓         ↓
  URLs     Raw HTML   Clean Text Sentiment  Reports
```

## Ethics & Legal

- **Respects robots.txt** by default
- **Rate limiting** to avoid overloading servers
- **User-agent** identifies as research tool
- **Educational purpose** - not for commercial redistribution
- **No paywalled content** - only publicly accessible articles

## Requirements

- Python 3.9+
- See `requirements.txt` for full dependencies

## License

MIT License - see LICENSE file

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## Troubleshooting

**Issue: Import errors**
```bash
pip install -e .
```

**Issue: Missing directories**
```bash
make doctor
```

**Issue: SSL certificate errors**
```bash
pip install --upgrade certifi
```

## Citation

If you use this project in research, please cite:

```bibtex
@software{earnings_sentiment_analyzer,
  title = {Financial Earnings Sentiment Analysis},
  author = {Your Name},
  year = {2026},
  url = {https://github.com/yourusername/financial-earnings-sentiment-analysis}
}
```

## Acknowledgments

- VADER Sentiment: Hutto & Gilbert (2014)
- FinBERT: Araci (2019)
- Newspaper3k: Lucas Ou-Yang
- Data sources: Reuters, CNBC, Yahoo Finance, etc.

---

**Status**: MVP Development (Chunk 1/6 Complete)

For questions or issues, please open a GitHub issue.
