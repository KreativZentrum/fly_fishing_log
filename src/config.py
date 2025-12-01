"""
Configuration loader for NZ Flyfishing Web Scraper.
Article 8.4 Compliance: Centralized configuration.
"""

from pathlib import Path
from typing import Any, Dict

import yaml


class ConfigError(Exception):
    """Configuration validation error."""

    pass


class Config:
    """Configuration manager for scraper settings."""

    def __init__(self, config_path: str = "config/nzfishing_config.yaml"):
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to YAML configuration file

        Raises:
            ConfigError: If configuration is invalid or missing required fields
        """
        self.config_path = Path(config_path)

        if not self.config_path.exists():
            raise ConfigError(f"Configuration file not found: {config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            self.data = yaml.safe_load(f)

        self._validate()

    def _validate(self):
        """Validate required configuration fields (Article 2 compliance)."""
        required_fields = ["base_url", "user_agent", "request_delay", "database_path", "log_path"]

        for field in required_fields:
            if field not in self.data:
                raise ConfigError(f"Missing required field: {field}")

        # Validate request_delay is at least 3 seconds (Article 3.1)
        if self.data["request_delay"] < 3.0:
            raise ConfigError(
                f"request_delay must be >= 3.0 seconds (Article 3.1), "
                f"got {self.data['request_delay']}"
            )

        # Validate base_url is a valid HTTP(S) URL
        if not self.data["base_url"].startswith(("http://", "https://")):
            raise ConfigError(f"base_url must start with http:// or https://")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.

        Args:
            key: Configuration key (supports nested keys with dot notation, e.g., 'pdf.page_size')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self.data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    @property
    def base_url(self) -> str:
        """Base URL for scraping (e.g., https://nzfishing.com)."""
        return self.data["base_url"]

    @property
    def user_agent(self) -> str:
        """User-Agent string (Article 2.1)."""
        return self.data["user_agent"]

    @property
    def request_delay(self) -> float:
        """Minimum delay between requests in seconds (Article 3.1)."""
        return float(self.data["request_delay"])

    @property
    def jitter_max(self) -> float:
        """Maximum random jitter to add to request delay."""
        return float(self.data.get("jitter_max", 0.0))

    @property
    def cache_dir(self) -> str:
        """Cache directory path."""
        return self.data.get("cache_dir", ".cache/nzfishing/")

    @property
    def cache_ttl(self) -> int:
        """Cache time-to-live in seconds."""
        return int(self.data.get("cache_ttl", 86400))

    @property
    def max_retries(self) -> int:
        """Maximum retry attempts for failed requests."""
        return int(self.data.get("max_retries", 3))

    @property
    def retry_backoff(self) -> list:
        """Exponential backoff delays for retries."""
        return self.data.get("retry_backoff", [1, 2, 4, 8])

    @property
    def halt_on_consecutive_5xx(self) -> int:
        """Number of consecutive 5xx errors before halting (Article 3.3)."""
        return int(self.data.get("halt_on_consecutive_5xx", 3))

    @property
    def database_path(self) -> str:
        """Path to SQLite database file."""
        return self.data["database_path"]

    @property
    def log_path(self) -> str:
        """Path to JSON log file."""
        return self.data["log_path"]

    @property
    def output_dir(self) -> str:
        """Output directory for PDFs."""
        return self.data.get("output_dir", "pdfs/")

    @property
    def discovery_rules(self) -> Dict[str, Any]:
        """Discovery rules (selectors, paths)."""
        return self.data.get("discovery_rules", {})

    @property
    def pdf_config(self) -> Dict[str, Any]:
        """PDF generation configuration."""
        return self.data.get("pdf", {})
