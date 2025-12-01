"""
Unit test: Cache TTL (Time-To-Live) validation.
Tests cache expiration and invalidation logic.
"""

import pytest
import time
from pathlib import Path
from datetime import datetime, timedelta
from src.fetcher import Fetcher


def test_cache_ttl_fresh_entry_returned(test_config, test_logger, tmp_path):
    """
    Test that fresh cache entries (within TTL) are returned.

    Article 3.5: Cache with TTL-based invalidation.
    """
    cache_dir = tmp_path / "cache"
    test_config.data["cache_dir"] = str(cache_dir)
    test_config.data["cache_ttl"] = 3600  # 1 hour

    fetcher = Fetcher(test_config, test_logger)

    # Create a cache file manually
    cache_key = fetcher._get_cache_key("http://example.com/test")
    cache_path = cache_dir / f"{cache_key}.html"
    cache_dir.mkdir(parents=True, exist_ok=True)

    test_content = "<html>Test Content</html>"
    cache_path.write_text(test_content)

    # Verify cache is valid (fresh)
    assert fetcher._is_cache_valid(cache_path) is True, "Freshly created cache should be valid"


def test_cache_ttl_expired_entry_invalidated(test_config, test_logger, tmp_path):
    """
    Test that expired cache entries (older than TTL) are invalidated.
    """
    cache_dir = tmp_path / "cache"
    test_config.data["cache_dir"] = str(cache_dir)
    test_config.data["cache_ttl"] = 1  # 1 second TTL for testing

    fetcher = Fetcher(test_config, test_logger)

    # Create a cache file
    cache_key = fetcher._get_cache_key("http://example.com/test")
    cache_path = cache_dir / f"{cache_key}.html"
    cache_dir.mkdir(parents=True, exist_ok=True)

    test_content = "<html>Test Content</html>"
    cache_path.write_text(test_content)

    # Immediately should be valid
    assert fetcher._is_cache_valid(cache_path) is True

    # Wait for TTL to expire
    time.sleep(1.5)

    # Should now be invalid
    assert (
        fetcher._is_cache_valid(cache_path) is False
    ), "Cache should be invalid after TTL expiration"


def test_cache_ttl_missing_file_invalid(test_config, test_logger, tmp_path):
    """
    Test that non-existent cache files are invalid.
    """
    cache_dir = tmp_path / "cache"
    test_config.data["cache_dir"] = str(cache_dir)

    fetcher = Fetcher(test_config, test_logger)

    # Non-existent file
    cache_path = cache_dir / "nonexistent.html"

    assert fetcher._is_cache_valid(cache_path) is False, "Non-existent cache file should be invalid"


def test_cache_read_returns_content(test_config, test_logger, tmp_path):
    """
    Test that _read_cache returns content for valid cache.
    """
    cache_dir = tmp_path / "cache"
    test_config.data["cache_dir"] = str(cache_dir)
    test_config.data["cache_ttl"] = 3600

    fetcher = Fetcher(test_config, test_logger)

    # Create cache file
    url = "http://example.com/test"
    test_content = "<html>Cached Test Content</html>"

    cache_path = fetcher._get_cache_path(url)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(test_content)

    # Read cache
    cached_content = fetcher._read_cache(url)

    assert cached_content == test_content, "Cached content should match what was written"


def test_cache_read_returns_none_for_expired(test_config, test_logger, tmp_path):
    """
    Test that _read_cache returns None for expired cache.
    """
    cache_dir = tmp_path / "cache"
    test_config.data["cache_dir"] = str(cache_dir)
    test_config.data["cache_ttl"] = 1  # 1 second

    fetcher = Fetcher(test_config, test_logger)

    # Create cache file
    url = "http://example.com/test"
    test_content = "<html>Expired Content</html>"

    cache_path = fetcher._get_cache_path(url)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(test_content)

    # Wait for expiration
    time.sleep(1.5)

    # Read cache
    cached_content = fetcher._read_cache(url)

    assert cached_content is None, "Expired cache should return None"


def test_cache_write_creates_file(test_config, test_logger, tmp_path):
    """
    Test that _write_cache creates cache file with content.
    """
    cache_dir = tmp_path / "cache"
    test_config.data["cache_dir"] = str(cache_dir)

    fetcher = Fetcher(test_config, test_logger)

    url = "http://example.com/test"
    test_content = "<html>Write Test</html>"

    # Write to cache
    fetcher._write_cache(url, test_content)

    # Verify file exists
    cache_path = fetcher._get_cache_path(url)
    assert cache_path.exists(), "Cache file should be created"

    # Verify content
    assert cache_path.read_text() == test_content, "Cache file should contain correct content"


def test_cache_key_generation_deterministic(test_config, test_logger, tmp_path):
    """
    Test that cache keys are deterministic (same URL = same key).
    """
    cache_dir = tmp_path / "cache"
    test_config.data["cache_dir"] = str(cache_dir)

    fetcher = Fetcher(test_config, test_logger)

    url = "http://example.com/test?param=value"

    # Generate key twice
    key1 = fetcher._get_cache_key(url)
    key2 = fetcher._get_cache_key(url)

    assert key1 == key2, "Cache keys should be deterministic"

    # Verify it's an MD5 hash (32 hex characters)
    assert len(key1) == 32, "Cache key should be MD5 hash (32 chars)"
    assert all(c in "0123456789abcdef" for c in key1), "Cache key should be hexadecimal"


def test_cache_key_unique_per_url(test_config, test_logger, tmp_path):
    """
    Test that different URLs generate different cache keys.
    """
    cache_dir = tmp_path / "cache"
    test_config.data["cache_dir"] = str(cache_dir)

    fetcher = Fetcher(test_config, test_logger)

    url1 = "http://example.com/page1"
    url2 = "http://example.com/page2"

    key1 = fetcher._get_cache_key(url1)
    key2 = fetcher._get_cache_key(url2)

    assert key1 != key2, "Different URLs should have different cache keys"


def test_cache_path_structure(test_config, test_logger, tmp_path):
    """
    Test that cache paths are correctly structured.
    """
    cache_dir = tmp_path / "cache"
    test_config.data["cache_dir"] = str(cache_dir)

    fetcher = Fetcher(test_config, test_logger)

    url = "http://example.com/test"
    cache_path = fetcher._get_cache_path(url)

    # Verify path is in cache directory
    assert cache_path.parent == cache_dir, f"Cache file should be in {cache_dir}"

    # Verify filename format
    assert cache_path.suffix == ".html", "Cache file should have .html extension"

    # Verify filename is MD5 hash
    assert len(cache_path.stem) == 32, "Cache filename should be MD5 hash"


def test_cache_ttl_default_24_hours(test_config, test_logger, tmp_path):
    """
    Test that default cache TTL is 24 hours (86400 seconds).

    Article 3.5: Default TTL should be 24 hours.
    """
    # Default config should have 24-hour TTL
    assert test_config.cache_ttl == 86400, "Default cache TTL should be 86400 seconds (24 hours)"
