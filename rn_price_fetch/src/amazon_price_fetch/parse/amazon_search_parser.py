"""
Amazon-specific search result parser.
"""

import re
from typing import List, Dict, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ..utils.logger import get_logger
from .base_parser import BaseParser, ParseError
from .selectors import AmazonSelectors


class AmazonSearchParser(BaseParser):
    """
    Parser for Amazon search result pages.
    """

    def __init__(self, base_url: str = "https://www.amazon.com"):
        """
        Initialize parser.

        Args:
            base_url: Base URL for Amazon marketplace
        """
        self.logger = get_logger(__name__)
        self.base_url = base_url.rstrip("/")

    def parse_search(self, html: str, url: Optional[str] = None) -> List[Dict]:
        """
        Parse Amazon search results from HTML.

        Args:
            html: HTML content to parse
            url: Optional URL for context

        Returns:
            List of product dictionaries
        """
        try:
            soup = BeautifulSoup(html, "lxml")
            products = []

            # Find all product containers
            product_elements = soup.select(AmazonSelectors.SEARCH_RESULTS)

            self.logger.debug(f"Found {len(product_elements)} product elements")

            for element in product_elements:
                try:
                    product_data = self._parse_product_element(element)
                    if product_data:
                        products.append(product_data)

                except Exception as e:
                    self.logger.debug(f"Failed to parse product element: {e}")
                    continue

            self.logger.info(f"Successfully parsed {len(products)} products")
            return products

        except Exception as e:
            raise ParseError(f"Failed to parse search results: {e}")

    def _parse_product_element(self, element) -> Optional[Dict]:
        """
        Parse individual product element.

        Args:
            element: BeautifulSoup element

        Returns:
            Product dictionary or None if invalid
        """
        try:
            # Extract basic information
            title = self._extract_title(element)
            url = self._extract_url(element)
            asin_code = self._extract_asin(element)
            image_url = self._extract_image(element)

            # Skip if required fields are missing
            if not all([title, url, asin_code, image_url]):
                return None

            # Extract additional information
            price = self._extract_price(element)
            rating = self._extract_rating(element)
            review_count = self._extract_review_count(element)
            availability = self._extract_availability(element)
            seller = self._extract_seller(element)
            sponsored = self._is_sponsored(element)

            return {
                "title": title,
                "url": url,
                "asin_code": asin_code,
                "image_url": image_url,
                "price": price,
                "rating": rating,
                "review_count": review_count,
                "availability": availability,
                "seller": seller,
                "sponsored": sponsored,
            }

        except Exception as e:
            self.logger.debug(f"Error parsing product element: {e}")
            return None

    def _extract_title(self, element) -> Optional[str]:
        """Extract product title."""
        for selector in AmazonSelectors.ALTERNATIVE_SELECTORS["title"]:
            title_element = element.select_one(selector)
            if title_element:
                return title_element.get_text(strip=True)
        return None

    def _extract_url(self, element) -> Optional[str]:
        """Extract product URL."""
        url_element = element.select_one(AmazonSelectors.PRODUCT_URL)
        if url_element and url_element.get("href"):
            relative_url = url_element["href"]
            return urljoin(self.base_url, relative_url)
        return None

    def _extract_asin(self, element) -> Optional[str]:
        """Extract ASIN code."""
        # Try data-asin attribute first
        asin = element.get("data-asin")
        if asin:
            return asin

        # Fallback: extract from URL
        url_element = element.select_one(AmazonSelectors.PRODUCT_URL)
        if url_element and url_element.get("href"):
            url = url_element["href"]
            # Extract ASIN from URL pattern
            asin_match = re.search(r"/([A-Z0-9]{10})(?:[/?]|$)", url)
            if asin_match:
                return asin_match.group(1)

        return None

    def _extract_image(self, element) -> Optional[str]:
        """Extract product image URL."""
        for selector in AmazonSelectors.ALTERNATIVE_SELECTORS["image"]:
            image_element = element.select_one(selector)
            if image_element:
                # Try src first, then data-src for lazy loading
                image_url = image_element.get("src") or image_element.get("data-src")
                if image_url:
                    return image_url
        return None

    def _extract_price(self, element) -> Optional[str]:
        """Extract product price."""
        # Try price whole + fractional
        price_whole = element.select_one(AmazonSelectors.PRICE_WHOLE)
        price_fractional = element.select_one(AmazonSelectors.PRICE_FRACTIONAL)

        if price_whole and price_fractional:
            whole_text = price_whole.get_text(strip=True).replace(",", "")
            fractional_text = price_fractional.get_text(strip=True)
            return f"{whole_text}.{fractional_text}"

        # Try alternative price selectors
        for selector in AmazonSelectors.ALTERNATIVE_SELECTORS["price"]:
            price_element = element.select_one(selector)
            if price_element:
                price_text = price_element.get_text(strip=True)
                # Clean price text
                price_match = re.search(r"[\d.,]+", price_text)
                if price_match:
                    return price_match.group().replace(",", "")

        return None

    def _extract_rating(self, element) -> Optional[float]:
        """Extract product rating."""
        rating_element = element.select_one(AmazonSelectors.RATING)
        if rating_element:
            rating_text = rating_element.get_text(strip=True)
            # Extract numeric rating from text like "4.5 out of 5 stars"
            rating_match = re.search(r"(\d+\.\d+|\d+)", rating_text)
            if rating_match:
                try:
                    return float(rating_match.group())
                except ValueError:
                    pass
        return None

    def _extract_review_count(self, element) -> Optional[int]:
        """Extract review count."""
        review_element = element.select_one(AmazonSelectors.REVIEW_COUNT)
        if review_element:
            review_text = review_element.get_text(strip=True)
            # Extract numeric count from text like "1,234"
            count_match = re.search(r"[\d,]+", review_text)
            if count_match:
                try:
                    return int(count_match.group().replace(",", ""))
                except ValueError:
                    pass
        return None

    def _extract_availability(self, element) -> Optional[str]:
        """Extract availability information."""
        availability_element = element.select_one(AmazonSelectors.AVAILABILITY)
        if availability_element:
            return availability_element.get_text(strip=True)
        return None

    def _extract_seller(self, element) -> Optional[str]:
        """Extract seller information."""
        seller_element = element.select_one(AmazonSelectors.SELLER)
        if seller_element:
            return seller_element.get_text(strip=True)
        return None

    def _is_sponsored(self, element) -> bool:
        """Check if product is sponsored/ad."""
        # Look for sponsored indicators
        sponsored_texts = ["Sponsored", "Ad"]
        element_text = element.get_text()

        for text in sponsored_texts:
            if text.lower() in element_text.lower():
                return True

        return False

    def parse_product(self, html: str, url: Optional[str] = None) -> Dict:
        """
        Parse individual product page.

        Args:
            html: HTML content to parse
            url: Optional URL for context

        Returns:
            Product dictionary

        Raises:
            NotImplementedError: Product page parsing not yet implemented
        """
        raise NotImplementedError("Product page parsing not yet implemented")