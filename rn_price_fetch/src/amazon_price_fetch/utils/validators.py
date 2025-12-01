"""
Validation utilities for Amazon Price Fetch.
"""

import re
from typing import Optional
from urllib.parse import urlparse


class ValidationError(Exception):
    """Validation-related errors."""
    pass


def validate_url(url: str) -> str:
    """
    Validate and normalize URL.

    Args:
        url: URL to validate

    Returns:
        Normalized URL

    Raises:
        ValidationError: If URL is invalid
    """
    if not url:
        raise ValidationError("URL cannot be empty")

    # Parse URL
    parsed = urlparse(url)

    # Check scheme
    if parsed.scheme not in ("http", "https"):
        raise ValidationError("URL must use http or https scheme")

    # Check netloc (domain)
    if not parsed.netloc:
        raise ValidationError("URL must contain a domain")

    # Check if it's an Amazon URL
    if "amazon." not in parsed.netloc:
        raise ValidationError("URL must be from Amazon domain")

    return url


def validate_query(query: str) -> str:
    """
    Validate search query.

    Args:
        query: Search query to validate

    Returns:
        Normalized query

    Raises:
        ValidationError: If query is invalid
    """
    if not query:
        raise ValidationError("Search query cannot be empty")

    # Strip whitespace
    query = query.strip()

    if not query:
        raise ValidationError("Search query cannot be empty")

    # Check length
    if len(query) > 200:
        raise ValidationError("Search query too long (max 200 characters)")

    # Check for potentially dangerous characters
    dangerous_patterns = [
        r"<script",
        r"javascript:",
        r"onload=",
        r"onerror=",
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            raise ValidationError("Search query contains potentially dangerous content")

    return query


def validate_pages(pages: int, max_pages: Optional[int] = None) -> int:
    """
    Validate number of pages to scrape.

    Args:
        pages: Number of pages
        max_pages: Maximum allowed pages

    Returns:
        Validated pages

    Raises:
        ValidationError: If pages is invalid
    """
    if pages < 1:
        raise ValidationError("Pages must be at least 1")

    if max_pages and pages > max_pages:
        raise ValidationError(f"Pages cannot exceed {max_pages}")

    return pages


def validate_price_range(
    min_price: Optional[float] = None, max_price: Optional[float] = None
) -> None:
    """
    Validate price range.

    Args:
        min_price: Minimum price
        max_price: Maximum price

    Raises:
        ValidationError: If price range is invalid
    """
    if min_price is not None and min_price < 0:
        raise ValidationError("Minimum price cannot be negative")

    if max_price is not None and max_price < 0:
        raise ValidationError("Maximum price cannot be negative")

    if min_price is not None and max_price is not None:
        if min_price > max_price:
            raise ValidationError("Minimum price cannot be greater than maximum price")