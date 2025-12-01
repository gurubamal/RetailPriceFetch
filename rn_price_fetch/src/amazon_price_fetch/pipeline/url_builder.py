"""
URL building utilities for Amazon Price Fetch.
"""

import urllib.parse
from typing import Dict, Optional

from ..utils.validators import validate_query


def build_search_url(
    query: str,
    page: int = 1,
    base_url: str = "https://www.amazon.com",
    **filters
) -> str:
    """
    Build Amazon search URL from query and filters.

    Args:
        query: Search query
        page: Page number (1-based)
        base_url: Amazon base URL
        **filters: Additional search filters

    Returns:
        Complete search URL

    Raises:
        ValueError: If query is invalid
    """
    # Validate and clean query
    query = validate_query(query)

    # Build base URL
    base_url = base_url.rstrip("/")
    search_path = "/s"

    # Build query parameters
    params: Dict[str, str] = {
        "k": query,
        "page": str(page),
    }

    # Add filters
    if filters:
        params.update(_process_filters(filters))

    # Encode parameters
    query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)

    return f"{base_url}{search_path}?{query_string}"


def _process_filters(filters: Dict) -> Dict[str, str]:
    """
    Process search filters into URL parameters.

    Args:
        filters: Filter dictionary

    Returns:
        URL parameters dictionary
    """
    params = {}

    # Price filters
    if "min_price" in filters:
        params["low-price"] = str(filters["min_price"])

    if "max_price" in filters:
        params["high-price"] = str(filters["max_price"])

    # Sort filters
    if "sort_by" in filters:
        sort_mapping = {
            "relevance": "relevanceblender",
            "price_low_high": "price-asc-rank",
            "price_high_low": "price-desc-rank",
            "newest": "date-desc-rank",
            "featured": "featured-rank",
        }
        params["s"] = sort_mapping.get(filters["sort_by"], "relevanceblender")

    # Category filters
    if "category" in filters:
        params["i"] = filters["category"]

    # Brand filters
    if "brand" in filters:
        params["rh"] = f"p_89:{filters['brand']}"

    # Condition filters
    if "condition" in filters:
        condition_mapping = {
            "new": "p_n_condition-type:2224371011",
            "used": "p_n_condition-type:2224372011",
            "refurbished": "p_n_condition-type:2224373011",
        }
        if filters["condition"] in condition_mapping:
            params["rh"] = condition_mapping[filters["condition"]]

    return params


def extract_query_from_url(url: str) -> Optional[str]:
    """
    Extract search query from Amazon URL.

    Args:
        url: Amazon search URL

    Returns:
        Search query or None if not found
    """
    try:
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)

        # Extract query from 'k' parameter
        if "k" in params:
            return params["k"][0]

        # Alternative parameter names
        for param in ["keywords", "field-keywords"]:
            if param in params:
                return params[param][0]

        return None

    except Exception:
        return None


def is_search_url(url: str) -> bool:
    """
    Check if URL is an Amazon search URL.

    Args:
        url: URL to check

    Returns:
        True if it's a search URL
    """
    try:
        parsed = urllib.parse.urlparse(url)
        return (
            "amazon." in parsed.netloc
            and parsed.path == "/s"
            and "k=" in parsed.query
        )
    except Exception:
        return False