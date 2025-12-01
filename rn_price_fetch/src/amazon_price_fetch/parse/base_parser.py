"""
Base parser interface for Amazon Price Fetch.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional

from ..models import Product


class ParseError(Exception):
    """Exception raised for parsing-related errors."""
    pass


class BaseParser(ABC):
    """
    Abstract base class for all parsers.
    """

    @abstractmethod
    def parse_search(self, html: str, url: Optional[str] = None) -> List[Dict]:
        """
        Parse search results from HTML.

        Args:
            html: HTML content to parse
            url: Optional URL for context

        Returns:
            List of product dictionaries
        """
        pass

    @abstractmethod
    def parse_product(self, html: str, url: Optional[str] = None) -> Dict:
        """
        Parse individual product page from HTML.

        Args:
            html: HTML content to parse
            url: Optional URL for context

        Returns:
            Product dictionary
        """
        pass

    def to_product_models(self, items: List[Dict]) -> List[Product]:
        """
        Convert parsed dictionaries to Product models.

        Args:
            items: List of product dictionaries

        Returns:
            List of Product objects

        Raises:
            ParseError: If required fields are missing
        """
        products = []

        for item in items:
            try:
                # Validate required fields
                required_fields = ["title", "url", "asin_code", "image_url"]
                for field in required_fields:
                    if not item.get(field):
                        raise ValueError(f"Missing required field: {field}")

                product = Product(
                    title=item["title"],
                    url=item["url"],
                    asin_code=item["asin_code"],
                    image_url=item["image_url"],
                    price=item.get("price"),
                    currency=item.get("currency", "USD"),
                    rating=item.get("rating"),
                    review_count=item.get("review_count"),
                    availability=item.get("availability"),
                    seller=item.get("seller"),
                    sponsored=item.get("sponsored", False),
                )
                products.append(product)

            except (ValueError, KeyError) as e:
                raise ParseError(f"Failed to create product model: {e}")

        return products