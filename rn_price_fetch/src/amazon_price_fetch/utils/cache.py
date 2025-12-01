"""
Caching utilities for Amazon Price Fetch.
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Optional

from ..config.loader import load_config


class Cache:
    """Simple file-based cache for HTTP responses."""

    def __init__(self, cache_dir: Optional[str] = None, ttl: int = 3600):
        """
        Initialize cache.

        Args:
            cache_dir: Cache directory path
            ttl: Time-to-live in seconds
        """
        if cache_dir is None:
            config = load_config()
            cache_dir = config.get("http", {}).get("cache_dir", ".cache")

        self.cache_dir = Path(cache_dir)
        self.ttl = ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for a key."""
        # Create hash of key for filename
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.json"

    def get(self, key: str) -> Optional[str]:
        """
        Get cached value for key.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        cache_file = self._get_cache_path(key)

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Check TTL
            if time.time() - data.get("timestamp", 0) > self.ttl:
                cache_file.unlink()  # Remove expired cache
                return None

            return data["value"]

        except (json.JSONDecodeError, KeyError, OSError):
            # Remove corrupted cache files
            try:
                cache_file.unlink()
            except OSError:
                pass
            return None

    def set(self, key: str, value: str) -> None:
        """
        Set cached value for key.

        Args:
            key: Cache key
            value: Value to cache
        """
        cache_file = self._get_cache_path(key)

        try:
            data = {
                "timestamp": time.time(),
                "value": value,
                "key": key,
            }

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)

        except OSError:
            # Silently fail on cache write errors
            pass

    def clear(self) -> None:
        """Clear all cache files."""
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
            except OSError:
                pass


# Global cache instance
_cache_instance: Optional[Cache] = None


def get_cache() -> Cache:
    """Get global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        config = load_config()
        cache_enabled = config.get("http", {}).get("cache_enabled", False)
        cache_dir = config.get("http", {}).get("cache_dir", ".cache")
        ttl = config.get("http", {}).get("cache_ttl", 3600)

        _cache_instance = Cache(cache_dir=cache_dir, ttl=ttl)

    return _cache_instance


def get_cached(url: str) -> Optional[str]:
    """
    Get cached HTML for URL.

    Args:
        url: URL to get cached content for

    Returns:
        Cached HTML or None
    """
    config = load_config()
    if not config.get("http", {}).get("cache_enabled", False):
        return None

    return get_cache().get(url)


def set_cached(url: str, html: str) -> None:
    """
    Set cached HTML for URL.

    Args:
        url: URL to cache
        html: HTML content to cache
    """
    config = load_config()
    if not config.get("http", {}).get("cache_enabled", False):
        return

    get_cache().set(url, html)