"""
CSS and XPath selectors for Amazon parsing.
"""

from typing import Dict


class AmazonSelectors:
    """
    Centralized selectors for Amazon parsing.
    """

    # Search result page selectors
    SEARCH_RESULTS = "div[data-component-type='s-search-result']"

    # Product element selectors
    PRODUCT_TITLE = "h2 a span"
    PRODUCT_URL = "h2 a"
    PRODUCT_ASIN = "data-asin"  # Attribute
    PRODUCT_IMAGE = "img.s-image"

    # Price selectors
    PRICE_WHOLE = ".a-price .a-price-whole"
    PRICE_FRACTIONAL = ".a-price .a-price-fraction"
    PRICE_SYMBOL = ".a-price .a-price-symbol"
    PRICE_RANGE = ".a-price-range .a-price"

    # Rating selectors
    RATING = "span.a-icon-alt"
    REVIEW_COUNT = "span.a-size-base.s-underline-text"

    # Availability selectors
    AVAILABILITY = ".a-color-price, .a-size-base.a-color-price"

    # Seller selectors
    SELLER = ".a-row.a-size-base.a-color-secondary .a-link-normal"

    # Sponsored/ads indicators
    SPONSORED = "span:contains('Sponsored'), .s-sponsored-label-info-icon"

    # Pagination selectors
    NEXT_PAGE = "a.s-pagination-next"
    PAGINATION_ITEMS = "span.s-pagination-item"

    # Alternative selectors for different Amazon layouts
    ALTERNATIVE_SELECTORS = {
        "title": ["h2 a span", ".a-size-medium.a-color-base.a-text-normal"],
        "price": [".a-price .a-offscreen", ".a-price-whole"],
        "image": ["img.s-image", "img[data-a-image-name='productImage']"],
    }

    @classmethod
    def get_selectors(cls) -> Dict[str, str]:
        """
        Get all selectors as a dictionary.

        Returns:
            Dictionary of selectors
        """
        return {
            key: value
            for key, value in cls.__dict__.items()
            if not key.startswith("_") and not callable(value)
        }