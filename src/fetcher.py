"""
HTTP fetcher module for NZ Flyfishing Web Scraper.
Article 2 & 3 Compliance: robots.txt, 3-second delays, retry logic, caching.
"""

import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import requests

from .config import Config
from .exceptions import FetchError, HaltError
from .logger import ScraperLogger


class Fetcher:
    """HTTP client with polite crawling features."""

    def __init__(self, config: Config, logger: ScraperLogger):
        """
        Initialize fetcher with configuration.

        Args:
            config: Configuration instance
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config.user_agent})

        # Rate limiting state
        self._last_request_time = 0.0
        self._consecutive_5xx_count = 0

        # Caching state
        self.cache_dir = Path(config.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_hits = 0
        self._cache_misses = 0

        # robots.txt parser
        self.robots_parser = None
        self._load_robots_txt()

    def _load_robots_txt(self):
        """Fetch and parse robots.txt (Article 2.1)."""
        robots_url = urljoin(self.config.base_url, "/robots.txt")

        try:
            self.robots_parser = RobotFileParser()
            self.robots_parser.set_url(robots_url)
            self.robots_parser.read()
            self.logger.info(f"Loaded robots.txt from {robots_url}")
        except Exception as e:
            self.logger.warning(f"Failed to load robots.txt: {e}")
            # Create permissive parser if robots.txt unavailable
            self.robots_parser = RobotFileParser()
            self.robots_parser.parse([])

    def is_allowed(self, url: str) -> bool:
        """
        Check if URL is allowed by robots.txt.

        Args:
            url: URL to check

        Returns:
            True if allowed, False if disallowed
        """
        if not self.robots_parser:
            return True

        return self.robots_parser.can_fetch(self.config.user_agent, url)

    def _get_cache_key(self, url: str) -> str:
        """Generate cache key from URL."""
        return hashlib.md5(url.encode("utf-8")).hexdigest()

    def _get_cache_path(self, url: str) -> Path:
        """Get cache file path for URL."""
        cache_key = self._get_cache_key(url)
        return self.cache_dir / f"{cache_key}.html"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cached file is still valid (within TTL)."""
        if not cache_path.exists():
            return False

        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - mtime

        return age.total_seconds() < self.config.cache_ttl

    def _read_cache(self, url: str) -> Optional[str]:
        """Read content from cache if valid."""
        cache_path = self._get_cache_path(url)

        if self._is_cache_valid(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                content = f.read()
            self._cache_hits += 1
            return content

        return None

    def _write_cache(self, url: str, content: str):
        """Write content to cache."""
        cache_path = self._get_cache_path(url)

        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _enforce_rate_limit(self):
        """
        Enforce 3-second minimum delay between requests (Article 3.1).

        Side effects:
            - Sleeps if needed to respect rate limit
            - Updates _last_request_time
        """
        now = time.time()
        elapsed = now - self._last_request_time

        if self._last_request_time > 0:  # Skip delay on first request
            required_delay = self.config.request_delay

            if elapsed < required_delay:
                sleep_time = required_delay - elapsed
                time.sleep(sleep_time)
                return sleep_time

        return 0.0

    def fetch(self, url: str, use_cache: bool = True, refresh: bool = False) -> str:
        """
        Fetch HTML from URL with rate limiting and caching.

        Args:
            url: Full URL to fetch
            use_cache: Whether to use cached content if available
            refresh: Force refresh even if cache is valid

        Returns:
            HTML content as string

        Raises:
            FetchError: On HTTP errors or network issues
            HaltError: On 3+ consecutive 5xx errors (Article 3.3)
        """
        # Check robots.txt (Article 2.1)
        if not self.is_allowed(url):
            self.logger.log_disallow(url)
            raise FetchError(f"URL disallowed by robots.txt: {url}", url=url, status_code=403)

        # Try cache first (Article 3.5)
        if use_cache and not refresh:
            cached_content = self._read_cache(url)
            if cached_content:
                self.logger.log_request(url=url, status_code=200, cache_hit=True)
                return cached_content

        self._cache_misses += 1

        # Enforce rate limiting (Article 3.1)
        delay = self._enforce_rate_limit()

        # Attempt fetch with retry logic
        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                response = self.session.get(url, timeout=30)
                self._last_request_time = time.time()

                # Log request
                self.logger.log_request(
                    url=url, status_code=response.status_code, delay_seconds=delay, cache_hit=False
                )

                # Handle 5xx errors (Article 3.3)
                if 500 <= response.status_code < 600:
                    self._consecutive_5xx_count += 1

                    if self._consecutive_5xx_count >= self.config.halt_on_consecutive_5xx:
                        halt_reason = f"{self._consecutive_5xx_count} consecutive 5xx errors"
                        self.logger.log_halt(halt_reason)
                        raise HaltError(f"Halting due to {halt_reason}", reason=halt_reason)

                    # Retry with exponential backoff
                    if attempt < self.config.max_retries - 1:
                        backoff = self.config.retry_backoff[
                            min(attempt, len(self.config.retry_backoff) - 1)
                        ]
                        self.logger.warning(
                            f"5xx error, retrying in {backoff}s (attempt {attempt + 1})"
                        )
                        time.sleep(backoff)
                        continue

                    raise FetchError(
                        f"HTTP {response.status_code} after {attempt + 1} retries",
                        url=url,
                        status_code=response.status_code,
                    )

                # Reset 5xx counter on success
                if response.status_code < 500:
                    self._consecutive_5xx_count = 0

                # Raise for other HTTP errors
                response.raise_for_status()

                # Success - cache and return
                content = response.text
                self._write_cache(url, content)

                return content

            except requests.RequestException as e:
                last_error = e

                if attempt < self.config.max_retries - 1:
                    backoff = self.config.retry_backoff[
                        min(attempt, len(self.config.retry_backoff) - 1)
                    ]
                    self.logger.warning(f"Request failed: {e}, retrying in {backoff}s")
                    time.sleep(backoff)
                else:
                    self.logger.log_request(url=url, error=str(e))
                    raise FetchError(f"Request failed after {attempt + 1} retries: {e}", url=url)

        # Should not reach here, but handle gracefully
        raise FetchError(f"Failed to fetch {url}: {last_error}", url=url)

    def clear_cache(self):
        """Delete all cached files (Article 3.5)."""
        count = 0
        for cache_file in self.cache_dir.glob("*.html"):
            cache_file.unlink()
            count += 1

        self.logger.info(f"Cleared {count} cached files")
        self._cache_hits = 0
        self._cache_misses = 0

    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        total = self._cache_hits + self._cache_misses

        # Calculate total bytes cached
        bytes_cached = sum(f.stat().st_size for f in self.cache_dir.glob("*.html"))

        return {
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "total": total,
            "hit_rate": self._cache_hits / total if total > 0 else 0.0,
            "bytes_cached": bytes_cached,
        }

    def close(self):
        """Close HTTP session."""
        self.session.close()
