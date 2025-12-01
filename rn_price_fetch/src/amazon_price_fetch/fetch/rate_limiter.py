"""
Rate limiting utilities for Amazon Price Fetch.
"""

import time
import threading
from typing import Optional


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter implementation.
    """

    def __init__(self, rate_per_minute: int, burst_capacity: Optional[int] = None):
        """
        Initialize rate limiter.

        Args:
            rate_per_minute: Maximum requests per minute
            burst_capacity: Maximum burst capacity (defaults to rate_per_minute)
        """
        self.rate_per_second = rate_per_minute / 60.0
        self.burst_capacity = burst_capacity or rate_per_minute
        self.tokens = float(self.burst_capacity)
        self.last_refill = time.time()
        self._lock = threading.Lock()

    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.rate_per_second

        self.tokens = min(self.tokens + new_tokens, self.burst_capacity)
        self.last_refill = now

    def acquire(self, tokens: int = 1) -> bool:
        """
        Acquire tokens from the bucket.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if tokens were acquired, False if would exceed rate limit
        """
        with self._lock:
            self._refill_tokens()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            return False

    def wait(self, tokens: int = 1) -> None:
        """
        Wait until tokens are available.

        Args:
            tokens: Number of tokens to acquire

        Raises:
            RateLimitExceeded: If waiting would exceed burst capacity
        """
        if tokens > self.burst_capacity:
            raise RateLimitExceeded(f"Requested tokens ({tokens}) exceed burst capacity ({self.burst_capacity})")

        while True:
            with self._lock:
                self._refill_tokens()

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return

            # Calculate wait time
            deficit = tokens - self.tokens
            wait_time = deficit / self.rate_per_second

            # Add small buffer to ensure tokens are available
            time.sleep(wait_time + 0.1)

    def get_wait_time(self, tokens: int = 1) -> float:
        """
        Get estimated wait time for tokens.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            Estimated wait time in seconds
        """
        with self._lock:
            self._refill_tokens()

            if self.tokens >= tokens:
                return 0.0

            deficit = tokens - self.tokens
            return deficit / self.rate_per_second