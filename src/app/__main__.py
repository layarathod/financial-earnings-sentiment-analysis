"""
CLI entry point for the earnings sentiment analyzer.
Usage: python -m app [command] [options]
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

import click

from app.config.settings import get_settings
from app.pipeline import Pipeline
from app.utils.logger import get_logger, setup_logger

# Initialize logger
setup_logger()
logger = get_logger(__name__)


@click.group()
@click.version_option(version="0.1.0", prog_name="earnings-sentiment-analyzer")
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default=None,
    help="Set logging level (overrides config)",
)
def cli(log_level):
    """
    Earnings Sentiment Analyzer - Automated NLP pipeline for financial news analysis.

    Analyzes sentiment in earnings-related articles for specified companies.
    """
    if log_level:
        setup_logger(log_level.upper())


@cli.command()
@click.option(
    "--ticker",
    "-t",
    required=True,
    type=str,
    help="Stock ticker symbol (e.g., AAPL, TSLA, GOOGL)",
)
@click.option(
    "--window",
    "-w",
    default="7d",
    type=str,
    help="Time window for article search (e.g., 7d, 14d, 30d)",
)
@click.option(
    "--top-k",
    "-k",
    default=20,
    type=int,
    help="Number of top articles to analyze",
)
@click.option(
    "--start-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
    help="Start date for article search (YYYY-MM-DD)",
)
@click.option(
    "--end-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
    help="End date for article search (YYYY-MM-DD)",
)
@click.option(
    "--sentiment-model",
    type=click.Choice(["vader", "finbert", "both"], case_sensitive=False),
    default=None,
    help="Sentiment model to use (overrides config)",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Custom output directory",
)
@click.option(
    "--no-cache",
    is_flag=True,
    default=False,
    help="Disable caching and force fresh downloads",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Run discovery only without fetching/analyzing",
)
def run(ticker, window, top_k, start_date, end_date, sentiment_model, output_dir, no_cache, dry_run):
    """
    Run the earnings sentiment analysis pipeline.

    Example:
        python -m app run --ticker AAPL --window 7d --top-k 20
    """
    logger.info("=" * 60)
    logger.info("EARNINGS SENTIMENT ANALYZER")
    logger.info("=" * 60)
    logger.info(f"Ticker: {ticker.upper()}")
    logger.info(f"Window: {window}")
    logger.info(f"Top K articles: {top_k}")

    # Parse window into date range if start/end not provided
    if not start_date or not end_date:
        end_date = datetime.now()

        # Parse window string (e.g., "7d" -> 7 days)
        try:
            if window.endswith("d"):
                days = int(window[:-1])
            elif window.endswith("w"):
                days = int(window[:-1]) * 7
            else:
                days = 7  # default

            start_date = end_date - timedelta(days=days)
            logger.info(f"Date range: {start_date.date()} to {end_date.date()}")
        except ValueError:
            logger.error(f"Invalid window format: {window}. Use format like '7d', '14d', etc.")
            sys.exit(1)

    # Initialize pipeline
    try:
        pipeline = Pipeline(
            ticker=ticker.upper(),
            start_date=start_date,
            end_date=end_date,
            top_k=top_k,
            sentiment_model=sentiment_model,
            output_dir=output_dir,
            use_cache=not no_cache,
        )

        # Run pipeline
        if dry_run:
            logger.info("DRY RUN mode - discovery only")
            results = pipeline.run_discovery()
            logger.info(f"Would fetch {len(results.get('urls', []))} articles")
        else:
            results = pipeline.run()

        # Display summary
        logger.success("Pipeline completed successfully!")
        logger.info(f"Results saved to: {results.get('output_path', 'N/A')}")

    except KeyboardInterrupt:
        logger.warning("Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        logger.exception("Full traceback:")
        sys.exit(1)


@cli.command()
@click.option(
    "--ticker",
    "-t",
    default=None,
    type=str,
    help="Filter results by ticker",
)
@click.option(
    "--limit",
    "-n",
    default=10,
    type=int,
    help="Number of results to show",
)
def list_results(ticker, limit):
    """List available analysis results."""
    from app.utils.storage import StorageManager

    storage = StorageManager()
    results = storage.list_results(ticker=ticker)

    if not results:
        click.echo("No results found.")
        return

    click.echo(f"\nFound {len(results)} result(s):\n")
    for i, result_path in enumerate(results[:limit], 1):
        click.echo(f"{i}. {result_path.name}")

    if len(results) > limit:
        click.echo(f"\n... and {len(results) - limit} more")


@cli.command()
@click.argument("result_file", type=click.Path(exists=True, path_type=Path))
def show(result_file):
    """Display a summary of analysis results."""
    import json

    with open(result_file, "r") as f:
        data = json.load(f)

    click.echo(f"\nResults for: {data.get('ticker', 'N/A')}")
    click.echo(f"Analyzed: {data.get('timestamp', 'N/A')}")
    click.echo(f"Articles: {data.get('num_articles', 0)}")

    if "summary" in data:
        summary = data["summary"]
        click.echo(f"\nOverall Sentiment: {summary.get('overall_sentiment', 'N/A')}")
        click.echo(f"Average Score: {summary.get('average_score', 'N/A'):.3f}")


@cli.command()
def config():
    """Show current configuration."""
    settings = get_settings()

    click.echo("\nCurrent Configuration:")
    click.echo(f"  Log Level: {settings.log_level}")
    click.echo(f"  Sentiment Model: {settings.sentiment_model}")
    click.echo(f"  Top K: {settings.default_top_k}")
    click.echo(f"  Window: {settings.default_search_window_days} days")
    click.echo(f"  Output Dir: {settings.output_dir}")
    click.echo(f"  Enable RSS: {settings.enable_rss}")
    click.echo(f"  Respect robots.txt: {settings.respect_robots_txt}")


@cli.command()
@click.option(
    "--check-deps",
    is_flag=True,
    default=False,
    help="Check if all dependencies are installed",
)
def doctor(check_deps):
    """
    Run diagnostics to check system health.
    """
    click.echo("Running diagnostics...\n")

    settings = get_settings()

    # Check directories
    click.echo("Checking directories:")
    dirs_ok = True
    for dir_name in ["data_dir", "output_dir", "raw_data_dir", "parsed_data_dir", "results_data_dir"]:
        dir_path = getattr(settings, dir_name)
        exists = dir_path.exists()
        status = "✓" if exists else "✗"
        click.echo(f"  {status} {dir_name}: {dir_path}")
        if not exists:
            dirs_ok = False

    if not dirs_ok:
        click.echo("\nCreating missing directories...")
        settings.ensure_directories()
        click.echo("Done!")

    # Check sources config
    click.echo("\nChecking sources configuration:")
    sources_path = settings.sources_config_path
    if sources_path.exists():
        click.echo(f"  ✓ {sources_path}")
    else:
        click.echo(f"  ✗ {sources_path} not found")

    # Check dependencies if requested
    if check_deps:
        click.echo("\nChecking dependencies:")
        deps = [
            "click",
            "pydantic",
            "httpx",
            "feedparser",
            "newspaper",
            "vaderSentiment",
            "transformers",
            "pandas",
            "matplotlib",
        ]

        for dep in deps:
            try:
                __import__(dep)
                click.echo(f"  ✓ {dep}")
            except ImportError:
                click.echo(f"  ✗ {dep} not installed")

    click.echo("\nDiagnostics complete!")


if __name__ == "__main__":
    cli()
