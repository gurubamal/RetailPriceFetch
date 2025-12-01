"""
Search service orchestrator for Amazon Price Fetch.
"""

import time
from datetime import datetime
from typing import List, Optional, Dict, Any

from ..fetch.http_client import HttpClient
from ..parse.amazon_search_parser import AmazonSearchParser
from ..pipeline.storage import StorageBackend, create_storage
from ..pipeline.url_builder import build_search_url
from ..models import Product, SearchMetadata, SearchResult
from ..utils.logger import get_logger
from ..utils.validators import validate_query, validate_pages


class SearchService:
    """
    Orchestrates search operations with pagination and deduplication.
    """

    def __init__(
        self,
        http_client: HttpClient,
        parser: AmazonSearchParser,
        storage: Optional[StorageBackend] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize search service.

        Args:
            http_client: HTTP client for fetching
            parser: Parser for HTML content
            storage: Optional storage backend
            config: Optional configuration
        """
        self.logger = get_logger(__name__)
        self.http_client = http_client
        self.parser = parser
        self.storage = storage
        self.config = config or {}

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "SearchService":
        """
        Create SearchService from configuration.

        Args:
            config: Configuration dictionary

        Returns:
            SearchService instance
        """
        # Create HTTP client
        http_config = config.get("http", {})
        http_client = HttpClient(
            timeout=http_config.get("timeout", 15),
            max_retries=http_config.get("max_retries", 3),
            rate_limit_per_minute=http_config.get("rate_limit_per_minute", 30),
            user_agent=http_config.get("user_agent"),
            headers=http_config.get("headers"),
            cache_enabled=http_config.get("cache_enabled", False),
        )

        # Create parser
        amazon_config = config.get("amazon", {})
        parser = AmazonSearchParser(
            base_url=amazon_config.get("base_url", "https://www.amazon.com")
        )

        # Create storage if specified
        storage_config = config.get("storage", {})
        storage = None
        if storage_config.get("type"):
            storage = create_storage(
                storage_type=storage_config["type"],
                file_path=storage_config.get("output_dir", "data/") +
                         storage_config.get("filename_prefix", "amazon_search_") +
                         "results.csv",
                append=True,
            )

        return cls(http_client, parser, storage, config)

    def search_products(
        self,
        query: str,
        pages: int = 1,
        output_file: Optional[str] = None,
        **filters
    ) -> List[Product]:
        """
        Search Amazon products by query.

        Args:
            query: Search query
            pages: Number of pages to scrape
            output_file: Optional output file path
            **filters: Additional search filters

        Returns:
            List of Product objects
        """
        start_time = time.time()

        # Validate inputs
        query = validate_query(query)
        pages = validate_pages(pages, self.config.get("search", {}).get("max_pages"))

        self.logger.info(f"Starting search for '{query}' ({pages} pages)")

        # Set up storage
        storage = self._get_storage(output_file)

        # Collect products
        all_products: List[Product] = []
        seen_asins = set()

        for page in range(1, pages + 1):
            try:
                page_products = self._search_page(query, page, filters)

                # Deduplicate by ASIN
                unique_products = []
                for product in page_products:
                    if product.asin_code not in seen_asins:
                        seen_asins.add(product.asin_code)
                        unique_products.append(product)

                if unique_products:
                    all_products.extend(unique_products)

                    # Save batch if storage available
                    if storage:
                        storage.save_batch(unique_products)

                    self.logger.info(
                        f"Page {page}: Found {len(unique_products)} unique products "
                        f"({len(page_products)} total)"
                    )
                else:
                    self.logger.warning(f"Page {page}: No new products found")

            except Exception as e:
                self.logger.error(f"Failed to process page {page}: {e}")
                # Continue with next page
                continue

        # Calculate metadata
        duration = time.time() - start_time
        metadata = SearchMetadata(
            query=query,
            pages_scraped=pages,
            total_results=len(all_products),
            unique_products=len(seen_asins),
            duration_seconds=duration,
        )

        self.logger.info(
            f"Search completed: {len(all_products)} products from {pages} pages "
            f"({duration:.2f}s)"
        )

        return all_products

    def _search_page(
        self,
        query: str,
        page: int,
        filters: Dict[str, Any]
    ) -> List[Product]:
        """
        Search a single page.

        Args:
            query: Search query
            page: Page number
            filters: Search filters

        Returns:
            List of Product objects from the page
        """
        # Build search URL
        url = build_search_url(
            query=query,
            page=page,
            base_url=self.parser.base_url,
            **filters
        )

        self.logger.debug(f"Fetching page {page}: {url}")

        try:
            # Fetch HTML
            html = self.http_client.get(url)

            # Parse products
            product_dicts = self.parser.parse_search(html, url)

            # Convert to models
            products = self.parser.to_product_models(product_dicts)

            return products

        except Exception as e:
            self.logger.error(f"Failed to process page {page}: {e}")
            return []

    def _get_storage(self, output_file: Optional[str]) -> Optional[StorageBackend]:
        """
        Get storage backend.

        Args:
            output_file: Optional output file path

        Returns:
            Storage backend or None
        """
        if output_file:
            # Use specified output file
            file_ext = output_file.split(".")[-1].lower()
            if file_ext == "json":
                return create_storage("json", output_file, append=False)
            else:
                return create_storage("csv", output_file, append=True)

        return self.storage

    async def search_products_async(
        self,
        query: str,
        pages: int = 1,
        **filters
    ) -> List[Product]:
        """
        Async version of search_products (placeholder for future implementation).

        Args:
            query: Search query
            pages: Number of pages to scrape
            **filters: Additional search filters

        Returns:
            List of Product objects
        """
        # For now, delegate to synchronous version
        # Future implementation would use async HTTP client
        self.logger.warning("Async search not yet implemented, using sync version")
        return self.search_products(query, pages, **filters)