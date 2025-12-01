"""
Data models for Amazon Price Fetch.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Product(BaseModel):
    """Product data model."""

    title: str
    url: str
    asin_code: str
    image_url: str
    price: Optional[str] = None
    currency: Optional[str] = "USD"
    rating: Optional[float] = None
    review_count: Optional[int] = None
    availability: Optional[str] = None
    seller: Optional[str] = None
    sponsored: bool = False
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        frozen = True  # Immutable objects


class SearchMetadata(BaseModel):
    """Metadata about a search operation."""

    query: str
    pages_scraped: int
    total_results: int
    unique_products: int
    duration_seconds: float
    timestamp: datetime = Field(default_factory=datetime.now)
    marketplace: str = "US"

    class Config:
        frozen = True


class SearchResult(BaseModel):
    """Complete search result with products and metadata."""

    products: list[Product]
    metadata: SearchMetadata

    class Config:
        frozen = True