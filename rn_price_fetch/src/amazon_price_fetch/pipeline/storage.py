"""
Storage backends for Amazon Price Fetch.
"""

import csv
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

import pandas as pd

from ..models import Product
from ..utils.logger import get_logger


class StorageError(Exception):
    """Exception raised for storage-related errors."""
    pass


class StorageBackend(ABC):
    """
    Abstract storage backend interface.
    """

    @abstractmethod
    def save(self, products: List[Product]) -> None:
        """
        Save products to storage.

        Args:
            products: List of products to save
        """
        pass

    @abstractmethod
    def save_batch(self, products: List[Product]) -> None:
        """
        Save batch of products to storage.

        Args:
            products: List of products to save
        """
        pass


class CSVStorage(StorageBackend):
    """
    CSV file storage backend.
    """

    def __init__(
        self,
        file_path: str,
        append: bool = True,
        encoding: str = "utf-8",
    ):
        """
        Initialize CSV storage.

        Args:
            file_path: Output file path
            append: Append to existing file
            encoding: File encoding
        """
        self.logger = get_logger(__name__)
        self.file_path = Path(file_path)
        self.append = append
        self.encoding = encoding

        # Ensure directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # Track if we've written header
        self._header_written = False
        if not append:
            self._header_written = True

    def save(self, products: List[Product]) -> None:
        """
        Save products to CSV file.

        Args:
            products: List of products to save
        """
        self.save_batch(products)

    def save_batch(self, products: List[Product]) -> None:
        """
        Save batch of products to CSV file.

        Args:
            products: List of products to save
        """
        if not products:
            return

        try:
            # Convert to dictionaries
            product_dicts = [product.model_dump() for product in products]

            # Determine write mode
            mode = "a" if self.append and self.file_path.exists() else "w"

            with open(self.file_path, mode, newline="", encoding=self.encoding) as f:
                writer = csv.DictWriter(f, fieldnames=product_dicts[0].keys())

                # Write header if needed
                if mode == "w" or (mode == "a" and not self._header_written):
                    writer.writeheader()
                    self._header_written = True

                writer.writerows(product_dicts)

            self.logger.debug(f"Saved {len(products)} products to {self.file_path}")

        except Exception as e:
            raise StorageError(f"Failed to save products to CSV: {e}")


class JSONStorage(StorageBackend):
    """
    JSON file storage backend.
    """

    def __init__(
        self,
        file_path: str,
        append: bool = False,
        encoding: str = "utf-8",
    ):
        """
        Initialize JSON storage.

        Args:
            file_path: Output file path
            append: Append to existing file (not supported for JSON)
            encoding: File encoding
        """
        self.logger = get_logger(__name__)
        self.file_path = Path(file_path)
        self.encoding = encoding

        # Ensure directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        if append:
            self.logger.warning("Append mode not supported for JSON storage")

    def save(self, products: List[Product]) -> None:
        """
        Save products to JSON file.

        Args:
            products: List of products to save
        """
        self.save_batch(products)

    def save_batch(self, products: List[Product]) -> None:
        """
        Save batch of products to JSON file.

        Args:
            products: List of products to save
        """
        if not products:
            return

        try:
            # Convert to dictionaries with JSON serialization
            product_dicts = [
                {
                    **product.model_dump(),
                    "timestamp": product.timestamp.isoformat(),
                }
                for product in products
            ]

            with open(self.file_path, "w", encoding=self.encoding) as f:
                json.dump(product_dicts, f, indent=2, ensure_ascii=False)

            self.logger.debug(f"Saved {len(products)} products to {self.file_path}")

        except Exception as e:
            raise StorageError(f"Failed to save products to JSON: {e}")


class PandasStorage(StorageBackend):
    """
    Pandas-based storage backend for various formats.
    """

    def __init__(
        self,
        file_path: str,
        format: str = "csv",
        append: bool = True,
    ):
        """
        Initialize Pandas storage.

        Args:
            file_path: Output file path
            format: Output format (csv, excel, parquet)
            append: Append to existing file
        """
        self.logger = get_logger(__name__)
        self.file_path = Path(file_path)
        self.format = format.lower()
        self.append = append

        # Ensure directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # Supported formats
        self.supported_formats = ["csv", "excel", "parquet"]
        if self.format not in self.supported_formats:
            raise StorageError(f"Unsupported format: {self.format}")

    def save(self, products: List[Product]) -> None:
        """
        Save products using Pandas.

        Args:
            products: List of products to save
        """
        self.save_batch(products)

    def save_batch(self, products: List[Product]) -> None:
        """
        Save batch of products using Pandas.

        Args:
            products: List of products to save
        """
        if not products:
            return

        try:
            # Convert to DataFrame
            product_dicts = [product.model_dump() for product in products]
            df = pd.DataFrame(product_dicts)

            # Save based on format
            if self.format == "csv":
                mode = "a" if self.append and self.file_path.exists() else "w"
                header = mode == "w"
                df.to_csv(self.file_path, mode=mode, header=header, index=False)

            elif self.format == "excel":
                if self.append and self.file_path.exists():
                    # Read existing file and append
                    existing_df = pd.read_excel(self.file_path)
                    df = pd.concat([existing_df, df], ignore_index=True)
                df.to_excel(self.file_path, index=False)

            elif self.format == "parquet":
                df.to_parquet(self.file_path, index=False)

            self.logger.debug(f"Saved {len(products)} products to {self.file_path}")

        except Exception as e:
            raise StorageError(f"Failed to save products with Pandas: {e}")


def create_storage(
    storage_type: str,
    file_path: str,
    **kwargs
) -> StorageBackend:
    """
    Create storage backend based on type.

    Args:
        storage_type: Storage type (csv, json, pandas)
        file_path: Output file path
        **kwargs: Additional storage parameters

    Returns:
        Storage backend instance

    Raises:
        StorageError: If storage type is invalid
    """
    storage_type = storage_type.lower()

    if storage_type == "csv":
        return CSVStorage(file_path, **kwargs)

    elif storage_type == "json":
        return JSONStorage(file_path, **kwargs)

    elif storage_type == "pandas":
        return PandasStorage(file_path, **kwargs)

    else:
        raise StorageError(f"Unsupported storage type: {storage_type}")