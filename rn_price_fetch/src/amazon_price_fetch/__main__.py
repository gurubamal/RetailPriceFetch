"""
Main CLI module for Amazon Price Fetch.
"""

import sys
from pathlib import Path
from typing import Optional

import click

from .config.loader import load_config
from .pipeline.search_service import SearchService
from .pipeline.url_builder import extract_query_from_url, is_search_url
from .utils.logger import setup_logging
from .utils.validators import validate_url, validate_price_range


@click.group()
@click.option(
    "--config",
    "config_file",
    type=click.Path(exists=True),
    help="Path to configuration file",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose logging",
)
@click.pass_context
def cli(ctx, config_file: Optional[str], verbose: bool):
    """Amazon Price Fetch - Robust Amazon product search and data extraction."""
    # Load configuration
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config(config_file)

    # Setup logging
    if verbose:
        ctx.obj["config"]["logging"]["level"] = "DEBUG"
    setup_logging(ctx.obj["config"])


@cli.command()
@click.option(
    "--query", "-q",
    required=True,
    help="Search query",
)
@click.option(
    "--pages", "-p",
    default=1,
    show_default=True,
    help="Number of pages to scrape",
)
@click.option(
    "--output", "-o",
    help="Output file path",
)
@click.option(
    "--format", "-f",
    type=click.Choice(["csv", "json"]),
    default="csv",
    show_default=True,
    help="Output format",
)
@click.option(
    "--min-price",
    type=float,
    help="Minimum price filter",
)
@click.option(
    "--max-price",
    type=float,
    help="Maximum price filter",
)
@click.option(
    "--sort-by",
    type=click.Choice(["relevance", "price_low_high", "price_high_low", "newest"]),
    help="Sort results by",
)
@click.pass_context
def search(
    ctx,
    query: str,
    pages: int,
    output: Optional[str],
    format: str,
    min_price: Optional[float],
    max_price: Optional[float],
    sort_by: Optional[str],
):
    """Search Amazon products by query."""
    config = ctx.obj["config"]

    try:
        # Validate price range
        validate_price_range(min_price, max_price)

        # Set output file if not specified
        if not output:
            output_dir = config.get("storage", {}).get("output_dir", "data/")
            filename_prefix = config.get("storage", {}).get("filename_prefix", "amazon_search_")
            safe_query = "_".join(query.split())
            output = f"{output_dir}{filename_prefix}{safe_query}.{format}"

        # Create search service
        service = SearchService.from_config(config)

        # Build filters
        filters = {}
        if min_price is not None:
            filters["min_price"] = min_price
        if max_price is not None:
            filters["max_price"] = max_price
        if sort_by:
            filters["sort_by"] = sort_by

        # Execute search
        products = service.search_products(
            query=query,
            pages=pages,
            output_file=output,
            **filters
        )

        # Display results
        click.echo(f"\n✅ Search completed successfully!")
        click.echo(f"📦 Products found: {len(products)}")
        click.echo(f"💾 Output file: {output}")

        if products:
            click.echo("\n📋 Sample products:")
            for i, product in enumerate(products[:3], 1):
                price_display = product.price or "N/A"
                click.echo(f"  {i}. {product.title[:60]}... - ${price_display}")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--url",
    required=True,
    help="Amazon page URL to scrape",
)
@click.option(
    "--output", "-o",
    help="Output file path",
)
@click.pass_context
def scrape(ctx, url: str, output: Optional[str]):
    """Scrape products from Amazon URL (legacy compatibility)."""
    config = ctx.obj["config"]

    try:
        # Validate URL
        url = validate_url(url)

        # Check if it's a search URL
        if is_search_url(url):
            # Extract query and use search command
            query = extract_query_from_url(url)
            if query:
                click.echo(f"🔍 Detected search URL, extracting query: '{query}'")

                # Set output file if not specified
                if not output:
                    output_dir = config.get("storage", {}).get("output_dir", "data/")
                    filename_prefix = config.get("storage", {}).get("filename_prefix", "amazon_search_")
                    safe_query = "_".join(query.split())
                    output = f"{output_dir}{filename_prefix}{safe_query}.csv"

                # Create search service
                service = SearchService.from_config(config)

                # Execute search
                products = service.search_products(
                    query=query,
                    pages=1,  # Single page for URL scraping
                    output_file=output,
                )

                click.echo(f"✅ Scraped {len(products)} products from URL")
                click.echo(f"💾 Output file: {output}")
                return

        # Fallback: direct URL scraping (placeholder for future implementation)
        click.echo("⚠️  Direct URL scraping not yet implemented")
        click.echo("💡 Try using the search command with --query instead")
        sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def config(ctx):
    """Show current configuration."""
    config = ctx.obj["config"]

    click.echo("🔧 Current Configuration:")
    click.echo(f"  HTTP Timeout: {config.get('http', {}).get('timeout')}s")
    click.echo(f"  Rate Limit: {config.get('http', {}).get('rate_limit_per_minute')} req/min")
    click.echo(f"  Amazon Base URL: {config.get('amazon', {}).get('base_url')}")
    click.echo(f"  Default Pages: {config.get('search', {}).get('default_pages')}")
    click.echo(f"  Storage Type: {config.get('storage', {}).get('type')}")
    click.echo(f"  Output Directory: {config.get('storage', {}).get('output_dir')}")


@cli.command()
@click.pass_context
def version(ctx):
    """Show version information."""
    from . import __version__, __author__

    click.echo(f"Amazon Price Fetch v{__version__}")
    click.echo(f"Author: {__author__}")


if __name__ == "__main__":
    cli()