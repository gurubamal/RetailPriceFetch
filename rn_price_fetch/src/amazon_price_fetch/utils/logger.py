"""
Logging utilities for Amazon Price Fetch.
"""

import logging
import logging.config
import sys
from typing import Optional

from ..config.loader import load_config


class ColorFormatter(logging.Formatter):
    """Color formatter for console output."""

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    COLORS = {
        logging.DEBUG: grey,
        logging.INFO: grey,
        logging.WARNING: yellow,
        logging.ERROR: red,
        logging.CRITICAL: bold_red,
    }

    def format(self, record):
        log_fmt = self.COLORS.get(record.levelno, self.grey)
        log_fmt += "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + self.reset
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def setup_logging(config: Optional[dict] = None) -> None:
    """
    Set up logging configuration.

    Args:
        config: Optional configuration dictionary
    """
    if config is None:
        config = load_config()

    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": config.get("logging", {}).get(
                    "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "color": {
                "()": ColorFormatter,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "color",
                "stream": sys.stdout,
            },
        },
        "loggers": {
            "amazon_price_fetch": {
                "level": config.get("logging", {}).get("level", "INFO"),
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }

    # Add file handler if specified
    log_file = config.get("logging", {}).get("file")
    if log_file:
        log_config["handlers"]["file"] = {
            "class": "logging.FileHandler",
            "filename": log_file,
            "level": "DEBUG",
            "formatter": "standard",
        }
        log_config["loggers"]["amazon_price_fetch"]["handlers"].append("file")

    logging.config.dictConfig(log_config)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given name.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    # Ensure logging is set up
    root_logger = logging.getLogger("amazon_price_fetch")
    if not root_logger.handlers:
        setup_logging()

    return logging.getLogger(f"amazon_price_fetch.{name}")