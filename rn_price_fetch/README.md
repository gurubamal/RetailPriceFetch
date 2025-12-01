# Amazon Price Fetch

A robust, configurable tool for searching Amazon products and extracting price data with support for pagination, rate limiting, and multiple output formats.

## Features

- **Query-based search**: Search Amazon by keywords instead of URLs
- **Multi-page pagination**: Scrape multiple search result pages
- **Configurable rate limiting**: Prevent IP blocking with adjustable limits
- **Multiple storage formats**: CSV, JSON, and database support
- **Robust error handling**: Graceful degradation for network issues
- **Type-safe code**: Full type hints and validation

## Installation

```bash
cd rn_price_fetch
poetry install
```

## Usage

### CLI Usage

```bash
# Search by query
poetry run amazon-price-fetch search --query "wireless mouse" --pages 3 --output data/mice.csv

# Search with filters
poetry run amazon-price-fetch search --query "laptop" --pages 2 --min-price 500 --max-price 1500

# Legacy URL scraping (backward compatibility)
poetry run amazon-price-fetch scrape --url "https://www.amazon.com/s?k=laptop"
```

### Python API

```python
from amazon_price_fetch import search_products

# Search products
products = search_products(
    query="wireless keyboard",
    pages=2,
    output_file="keyboards.csv"
)

# Async search
from amazon_price_fetch import search_products_async
import asyncio

async def main():
    products = await search_products_async(
        query="gaming mouse",
        pages=3
    )

asyncio.run(main())
```

## Configuration

Create `config/default.yml` to customize behavior:

```yaml
http:
  timeout: 15
  max_retries: 3
  rate_limit_per_minute: 30
  user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

amazon:
  base_url: "https://www.amazon.com"
  marketplace: "US"

search:
  default_pages: 1
  max_pages: 10
  deduplicate: true

storage:
  type: "csv"
  output_dir: "data/"
```

## Architecture

The tool follows a layered architecture:

- **Config Layer**: Settings management with YAML and environment variables
- **Fetch Layer**: HTTP client with rate limiting and retries
- **Parse Layer**: HTML parsing with BeautifulSoup/lxml
- **Pipeline Layer**: Search orchestration and data processing
- **Storage Layer**: Multiple output format support
- **CLI Layer**: User interface with Click

## Development

```bash
# Install development dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Type checking
poetry run mypy src/

# Format code
poetry run black src/
poetry run isort src/
```

## Legal Notice

This tool is intended for educational and research purposes. Please respect Amazon's Terms of Service and robots.txt. Use conservative rate limits and consider using official APIs when available.