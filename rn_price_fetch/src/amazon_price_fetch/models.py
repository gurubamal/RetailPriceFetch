"""
Data models for Amazon Price Fetch.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Product(BaseModel):
    """Product data model."""

    model_config = ConfigDict(frozen=True)

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


class SearchMetadata(BaseModel):
    """Metadata about a search operation."""

    model_config = ConfigDict(frozen=True)

    query: str
    pages_scraped: int
    total_results: int
    unique_products: int
    duration_seconds: float
    timestamp: datetime = Field(default_factory=datetime.now)
    marketplace: str = "US"


class SearchResult(BaseModel):
    """Complete search result with products and metadata."""

    model_config = ConfigDict(frozen=True)

    products: list[Product]
    metadata: SearchMetadata