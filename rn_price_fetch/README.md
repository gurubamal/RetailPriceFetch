# Amazon Price Fetch

A robust, configurable tool for searching Amazon products and extracting price data with support for pagination, rate limiting, and multiple output formats.

## Features

- **Query-based search**: Search Amazon by keywords instead of URLs
- **Multi-page pagination**: Scrape multiple search result pages
- **Configurable rate limiting**: Prevent IP blocking with adjustable limits
- **Multiple storage formats**: CSV, JSON, and console output
- **Robust error handling**: Graceful degradation for network issues
- **Type-safe code**: Full type hints and validation
- **Legacy compatibility**: Support for direct URL scraping
- **Async support**: Both synchronous and asynchronous APIs
- **Configuration management**: YAML + environment variable overrides

## Installation

```bash
# Clone or navigate to the project directory
cd ~/ecommerce/amazon-scraper/RetailPriceFetch/rn_price_fetch/

# Install dependencies
poetry install

# Verify installation
poetry run amazon-price-fetch --help
```

## Usage

### CLI Usage

#### Get Help
```bash
poetry run amazon-price-fetch --help
poetry run amazon-price-fetch search --help
poetry run amazon-price-fetch scrape --help
```

#### Search by Query (Recommended)
```bash
# Basic search
poetry run amazon-price-fetch search --query "wireless mouse" --pages 3 --output data/mice.csv

# Search with price filters
poetry run amazon-price-fetch search --query "laptop" --pages 2 --min-price 500 --max-price 1500

# Search with verbose logging
poetry run amazon-price-fetch search --query "keyboard" --pages 1 -v

# Search and save to JSON
poetry run amazon-price-fetch search --query "headphones" --pages 2 --output data/headphones.json
```

#### Legacy URL Scraping
```bash
# Direct URL scraping
poetry run amazon-price-fetch scrape --url "https://www.amazon.com/s?k=laptop"

# URL scraping with output
poetry run amazon-price-fetch scrape --url "https://www.amazon.com/s?k=wireless+keyboard" --output data/keyboard.csv
```

#### Configuration Commands
```bash
# Show current configuration
poetry run amazon-price-fetch config

# Show version
poetry run amazon-price-fetch version
```

### Python API

#### Synchronous Search
```python
from amazon_price_fetch import search_products

# Basic search
result = search_products(
    query="wireless keyboard",
    pages=2,
    output_file="keyboards.csv"
)

# Access products and metadata
print(f"Found {len(result.products)} products")
print(f"Search took {result.metadata.duration_seconds:.2f} seconds")

for product in result.products:
    print(f"{product.title}: {product.price}")
```

#### Asynchronous Search
```python
from amazon_price_fetch import search_products_async
import asyncio

async def main():
    result = await search_products_async(
        query="gaming mouse",
        pages=3,
        output_file="mice.json"
    )

    print(f"Found {len(result.products)} products")

asyncio.run(main())
```

#### Direct URL Scraping
```python
from amazon_price_fetch import scrape_url

# Scrape products from specific URL
result = scrape_url(
    url="https://www.amazon.com/s?k=laptop",
    output_file="laptops.csv"
)
```

## Configuration

### Configuration Files

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

### Environment Variables

You can override configuration using environment variables:

```bash
# Set custom rate limit
export AMAZON_PRICE_FETCH_HTTP_RATE_LIMIT_PER_MINUTE=20

# Set custom timeout
export AMAZON_PRICE_FETCH_HTTP_TIMEOUT=30

# Set custom user agent
export AMAZON_PRICE_FETCH_HTTP_USER_AGENT="Custom User Agent"
```

Environment variables follow the pattern: `AMAZON_PRICE_FETCH_{SECTION}_{KEY}`

### Command Line Configuration

```bash
# Use custom config file
poetry run amazon-price-fetch --config custom_config.yml search --query "laptop"

# Enable verbose logging
poetry run amazon-price-fetch -v search --query "mouse"
```

## Architecture

The tool follows a layered architecture:

- **Config Layer**: Settings management with YAML and environment variables
- **Fetch Layer**: HTTP client with rate limiting and retries
- **Parse Layer**: HTML parsing with BeautifulSoup/lxml
- **Pipeline Layer**: Search orchestration and data processing
- **Storage Layer**: Multiple output format support
- **CLI Layer**: User interface with Click

## Troubleshooting

### Common Issues

**No products found**
- Amazon may have updated their HTML structure
- Check if the search URL is accessible in your browser
- Try reducing the rate limit or adding delays

**Rate limiting errors**
- Decrease `rate_limit_per_minute` in configuration
- Add delays between requests
- Use rotating user agents

**Network timeouts**
- Increase `timeout` in configuration
- Check your internet connection
- Try with fewer pages

**Command not found**
- Ensure you're in the correct directory: `~/ecommerce/amazon-scraper/RetailPriceFetch/rn_price_fetch/`
- Run `poetry install` to install the package
- Verify `[tool.poetry.scripts]` exists in `pyproject.toml`

### Debug Mode

Enable verbose logging to see detailed information:

```bash
poetry run amazon-price-fetch -v search --query "test" --pages 1
```

## Development

### Setup
```bash
# Install development dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=src

# Type checking
poetry run mypy src/

# Format code
poetry run black src/
poetry run isort src/

# Lint code
poetry run flake8 src/
```

### Project Structure
```
rn_price_fetch/
├── src/amazon_price_fetch/
│   ├── config/loader.py          # Configuration management
│   ├── fetch/http_client.py      # HTTP client with rate limiting
│   ├── parse/amazon_search_parser.py  # HTML parsing
│   ├── pipeline/search_service.py     # Search orchestration
│   ├── utils/validators.py       # Data validation
│   ├── models.py                 # Pydantic data models
│   ├── __init__.py               # Public API
│   └── __main__.py               # CLI interface
├── tests/test_basic.py           # Test suite
├── config/default.yml            # Default configuration
└── pyproject.toml               # Poetry configuration
```

## Legal Notice

This tool is intended for educational and research purposes. Please respect Amazon's Terms of Service and robots.txt. Use conservative rate limits and consider using official APIs when available.

### Responsible Usage

- Use conservative rate limits (10-20 requests per minute)
- Respect `robots.txt` directives
- Don't overwhelm Amazon's servers
- Consider using official APIs when available
- Be aware that web scraping may violate terms of service

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and ensure they pass
5. Submit a pull request
