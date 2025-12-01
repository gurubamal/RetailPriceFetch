"""
HTTP client for Amazon Price Fetch with rate limiting and retries.
"""

import time
from typing import Dict, Optional, Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..utils.logger import get_logger
from ..utils.cache import get_cached, set_cached
from .rate_limiter import TokenBucketRateLimiter


class FetchError(Exception):
    """Exception raised for fetch-related errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, url: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.url = url


class HttpClient:
    """
    Robust HTTP client with rate limiting, retries, and caching.
    """

    def __init__(
        self,
        timeout: int = 15,
        max_retries: int = 3,
        rate_limit_per_minute: int = 30,
        user_agent: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        cache_enabled: bool = False,
    ):
        """
        Initialize HTTP client.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            rate_limit_per_minute: Rate limit in requests per minute
            user_agent: User agent string
            headers: Additional headers
            cache_enabled: Enable response caching
        """
        self.logger = get_logger(__name__)
        self.timeout = timeout
        self.cache_enabled = cache_enabled

        # Set up rate limiter
        self.rate_limiter = TokenBucketRateLimiter(rate_limit_per_minute)

        # Set up session with retries
        self.session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        self.session.headers.update({
            "User-Agent": user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Connection": "keep-alive",
        })

        if headers:
            self.session.headers.update(headers)

    def _make_request(
        self,
        url: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> requests.Response:
        """
        Make HTTP request with rate limiting.

        Args:
            url: Request URL
            method: HTTP method
            params: Query parameters
            **kwargs: Additional request parameters

        Returns:
            Response object

        Raises:
            FetchError: If request fails
        """
        # Apply rate limiting
        self.rate_limiter.wait()

        # Merge timeout
        request_kwargs = {"timeout": self.timeout, **kwargs}
        if params:
            request_kwargs["params"] = params

        start_time = time.time()

        try:
            response = self.session.request(method, url, **request_kwargs)
            response.raise_for_status()

            elapsed = time.time() - start_time
            self.logger.debug(f"HTTP {method} {url} - {response.status_code} ({elapsed:.2f}s)")

            return response

        except requests.exceptions.Timeout as e:
            elapsed = time.time() - start_time
            self.logger.warning(f"Request timeout: {url} ({elapsed:.2f}s)")
            raise FetchError(f"Request timeout after {elapsed:.2f}s", url=url) from e

        except requests.exceptions.ConnectionError as e:
            self.logger.warning(f"Connection error: {url}")
            raise FetchError("Connection error", url=url) from e

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            self.logger.warning(f"HTTP error {status_code}: {url}")
            raise FetchError(f"HTTP error {status_code}", status_code=status_code, url=url) from e

        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Request error: {url} - {e}")
            raise FetchError(f"Request error: {e}", url=url) from e

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: Optional[bool] = None,
        **kwargs
    ) -> str:
        """
        GET request with optional caching.

        Args:
            url: Request URL
            params: Query parameters
            use_cache: Override cache setting
            **kwargs: Additional request parameters

        Returns:
            Response text

        Raises:
            FetchError: If request fails
        """
        # Check cache first
        cache_enabled = use_cache if use_cache is not None else self.cache_enabled
        if cache_enabled:
            cached_content = get_cached(url)
            if cached_content is not None:
                self.logger.debug(f"Cache hit: {url}")
                return cached_content

        # Make request
        response = self._make_request(url, "GET", params, **kwargs)
        content = response.text

        # Cache response
        if cache_enabled:
            set_cached(url, content)

        return content

    def head(self, url: str, **kwargs) -> requests.Response:
        """
        HEAD request.

        Args:
            url: Request URL
            **kwargs: Additional request parameters

        Returns:
            Response object
        """
        return self._make_request(url, "HEAD", **kwargs)

    def close(self) -> None:
        """Close HTTP session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()