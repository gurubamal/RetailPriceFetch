"""
Configuration loader for Amazon Price Fetch.
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Configuration-related errors."""
    pass


# Built-in defaults as fallback
DEFAULT_CONFIG = {
    "http": {
        "timeout": 15,
        "max_retries": 3,
        "rate_limit_per_minute": 30,
        "cache_enabled": False,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    },
    "amazon": {
        "base_url": "https://www.amazon.com",
        "marketplace": "US",
        "search_path": "/s",
    },
    "search": {
        "default_pages": 1,
        "max_pages": 10,
        "deduplicate": True,
        "max_results_per_page": 48,
    },
    "storage": {
        "type": "csv",
        "output_dir": "data/",
        "filename_prefix": "amazon_search_",
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": None,
    },
}


# Environment variable mappings
ENV_MAPPINGS = {
    "AMZ_HTTP_TIMEOUT": ("http", "timeout", int),
    "AMZ_HTTP_MAX_RETRIES": ("http", "max_retries", int),
    "AMZ_RATE_LIMIT_PER_MINUTE": ("http", "rate_limit_per_minute", int),
    "AMZ_CACHE_ENABLED": ("http", "cache_enabled", bool),
    "AMZ_BASE_URL": ("amazon", "base_url", str),
    "AMZ_MARKETPLACE": ("amazon", "marketplace", str),
    "AMZ_DEFAULT_PAGES": ("search", "default_pages", int),
    "AMZ_MAX_PAGES": ("search", "max_pages", int),
    "AMZ_DEDUPLICATE": ("search", "deduplicate", bool),
    "AMZ_STORAGE_TYPE": ("storage", "type", str),
    "AMZ_OUTPUT_DIR": ("storage", "output_dir", str),
    "AMZ_LOG_LEVEL": ("logging", "level", str),
}


def _load_yaml_config(config_path: Path) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.warning(f"Config file not found: {config_path}")
        return {}
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in config file {config_path}: {e}")


def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply environment variable overrides to configuration."""
    for env_var, (section, key, type_func) in ENV_MAPPINGS.items():
        if env_var in os.environ:
            value = os.environ[env_var]
            try:
                # Handle boolean values
                if type_func is bool:
                    value = value.lower() in ("true", "1", "yes", "on")
                else:
                    value = type_func(value)

                # Ensure section exists
                if section not in config:
                    config[section] = {}

                config[section][key] = value
                logger.debug(f"Applied environment override: {env_var} -> {section}.{key} = {value}")
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid value for {env_var}: {value} ({e})")

    return config


def _merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge two configuration dictionaries."""
    result = base.copy()

    for key, value in override.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = _merge_configs(result[key], value)
        else:
            result[key] = value

    return result


def _validate_config(config: Dict[str, Any]) -> None:
    """Validate configuration values."""
    # HTTP validation
    if config.get("http", {}).get("timeout") <= 0:
        raise ConfigError("HTTP timeout must be positive")

    if config.get("http", {}).get("max_retries") < 0:
        raise ConfigError("HTTP max_retries must be non-negative")

    if config.get("http", {}).get("rate_limit_per_minute") <= 0:
        raise ConfigError("Rate limit must be positive")

    # Search validation
    if config.get("search", {}).get("default_pages") <= 0:
        raise ConfigError("Default pages must be positive")

    if config.get("search", {}).get("max_pages") <= 0:
        raise ConfigError("Max pages must be positive")


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file with environment overrides.

    Args:
        config_path: Optional path to config file. If None, uses default location.

    Returns:
        Merged configuration dictionary
    """
    if config_path is None:
        # Look for config in standard locations
        possible_paths = [
            Path("config/default.yml"),
            Path("src/amazon_price_fetch/config/default.yml"),
            Path("~/.config/amazon_price_fetch/config.yml").expanduser(),
        ]

        for path in possible_paths:
            if path.exists():
                config_path = str(path)
                break
        else:
            config_path = None

    # Load YAML config if available
    file_config = {}
    if config_path:
        file_config = _load_yaml_config(Path(config_path))

    # Start with defaults, merge file config, then apply env overrides
    config = _merge_configs(DEFAULT_CONFIG, file_config)
    config = _apply_env_overrides(config)

    # Validate final config
    _validate_config(config)

    logger.debug("Configuration loaded successfully")
    return config


def get_setting(config: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    Get a setting from configuration using dot notation.

    Args:
        config: Configuration dictionary
        path: Dot-separated path (e.g., "http.timeout")
        default: Default value if path not found

    Returns:
        Configuration value or default
    """
    keys = path.split(".")
    current = config

    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            if default is not None:
                return default
            raise ConfigError(f"Configuration path not found: {path}")

    return current