"""
Amazon Price Fetch - A robust tool for searching Amazon products and extracting price data.
"""

from typing import List, Optional

from .models import Product
from .pipeline.search_service import SearchService
from .config.loader import load_config

__version__ = "0.1.0"
__author__ = "Ram Nath Bamal"


def search_products(
    query: str,
    pages: int = 1,
    output_file: Optional[str] = None,
    **kwargs
) -> List[Product]:
    """
    Search Amazon products by query.

    Args:
        query: Search query string
        pages: Number of pages to scrape (default: 1)
        output_file: Optional output file path
        **kwargs: Additional search parameters

    Returns:
        List of Product objects
    """
    config = load_config()
    service = SearchService.from_config(config)

    return service.search_products(
        query=query,
        pages=pages,
        output_file=output_file,
        **kwargs
    )


async def search_products_async(
    query: str,
    pages: int = 1,
    **kwargs
) -> List[Product]:
    """
    Async version of search_products for high-throughput applications.

    Args:
        query: Search query string
        pages: Number of pages to scrape (default: 1)
        **kwargs: Additional search parameters

    Returns:
        List of Product objects
    """
    config = load_config()
    service = SearchService.from_config(config)

    return await service.search_products_async(
        query=query,
        pages=pages,
        **kwargs
    )