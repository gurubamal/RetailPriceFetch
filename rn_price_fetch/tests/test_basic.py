"""
Basic tests for Amazon Price Fetch.
"""

import pytest
from amazon_price_fetch.config.loader import load_config
from amazon_price_fetch.utils.validators import validate_query, validate_url, ValidationError


def test_config_loading():
    """Test that configuration loads correctly."""
    config = load_config()

    assert "http" in config
    assert "amazon" in config
    assert "search" in config
    assert "storage" in config

    # Check default values
    assert config["http"]["timeout"] == 15
    assert config["amazon"]["base_url"] == "https://www.amazon.com"


def test_query_validation():
    """Test query validation."""
    # Valid queries
    assert validate_query("laptop") == "laptop"
    assert validate_query("wireless mouse") == "wireless mouse"

    # Invalid queries
    with pytest.raises(ValidationError):
        validate_query("")

    with pytest.raises(ValidationError):
        validate_query("   ")


def test_url_validation():
    """Test URL validation."""
    # Valid URLs
    valid_url = "https://www.amazon.com/s?k=laptop"
    assert validate_url(valid_url) == valid_url

    # Invalid URLs
    with pytest.raises(ValidationError):
        validate_url("not-a-url")

    with pytest.raises(ValidationError):
        validate_url("https://example.com/page")  # Not Amazon


def test_imports():
    """Test that all modules can be imported."""
    # This test ensures the package structure is correct
    from amazon_price_fetch import search_products
    from amazon_price_fetch.fetch import HttpClient
    from amazon_price_fetch.parse import AmazonSearchParser
    from amazon_price_fetch.pipeline import SearchService

    # If we get here, imports work
    assert True