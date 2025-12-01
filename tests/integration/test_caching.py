"""
Integration test: HTTP caching behavior.
Tests US5 — Cache HTML to Avoid Redundant Requests.

Article 3.5: Cache HTML locally to avoid redundant requests
Success Criteria SC-008: Verify second run uses cached pages
"""

import pytest
import time
from pathlib import Path
from src.fetcher import Fetcher


def test_caching_avoids_redundant_requests(test_config, test_logger, mock_http_server, tmp_path):
    """
    Test that second scraper run uses cached HTML without making HTTP requests.

    Success Criteria SC-008: "Second run uses cached pages, no redundant HTTP requests"
    Article 3.5: "cache HTML locally with TTL"
    """
    # Use temporary cache directory
    cache_dir = tmp_path / "cache"
    test_config.data["cache_dir"] = str(cache_dir)

    # First run - should fetch from network
    fetcher1 = Fetcher(test_config, test_logger)
    url = f"{mock_http_server}/page1"

    content1 = fetcher1.fetch(url)
    stats1 = fetcher1.get_cache_stats()

    # Verify content fetched
    assert content1, "Content should be fetched"
    assert stats1["misses"] == 1, "First fetch should be cache miss"
    assert stats1["hits"] == 0, "First fetch should have no cache hits"

    # Verify cache file created
    cache_files = list(cache_dir.glob("*.html"))
    assert len(cache_files) == 1, f"Expected 1 cache file, found {len(cache_files)}"

    # Second run - should use cache
    fetcher2 = Fetcher(test_config, test_logger)
    content2 = fetcher2.fetch(url)
    stats2 = fetcher2.get_cache_stats()

    # Verify content matches
    assert content2 == content1, "Cached content should match original"

    # Verify cache hit
    assert stats2["hits"] == 1, "Second fetch should be cache hit"
    assert stats2["misses"] == 0, "Second fetch should have no new misses"


def test_cache_stats_tracking(test_config, test_logger, mock_http_server, tmp_path):
    """
    Test that cache statistics are tracked correctly.
    """
    cache_dir = tmp_path / "cache"
    test_config.data["cache_dir"] = str(cache_dir)

    fetcher = Fetcher(test_config, test_logger)

    # Initial stats
    stats = fetcher.get_cache_stats()
    assert stats["hits"] == 0
    assert stats["misses"] == 0
    assert stats["total"] == 0

    # Fetch multiple pages
    urls = [f"{mock_http_server}/page1", f"{mock_http_server}/page2", f"{mock_http_server}/page3"]

    for url in urls:
        fetcher.fetch(url)

    stats = fetcher.get_cache_stats()
    assert stats["misses"] == 3, "Should have 3 cache misses"
    assert stats["total"] == 3

    # Fetch same pages again (cache hits)
    for url in urls:
        fetcher.fetch(url)

    stats = fetcher.get_cache_stats()
    assert stats["hits"] == 3, "Should have 3 cache hits"
    assert stats["total"] == 6


def test_cache_hit_no_delay(test_config, test_logger, mock_http_server, tmp_path):
    """
    Test that cache hits do not incur rate limiting delay.

    Article 3.5: Cache hits should be fast (no 3-second delay)
    """
    cache_dir = tmp_path / "cache"
    test_config.data["cache_dir"] = str(cache_dir)

    fetcher = Fetcher(test_config, test_logger)
    url = f"{mock_http_server}/cacheable"

    # First fetch (network)
    start1 = time.time()
    fetcher.fetch(url)
    duration1 = time.time() - start1

    # Second fetch (cache hit)
    start2 = time.time()
    fetcher.fetch(url)
    duration2 = time.time() - start2

    # Cache hit should be much faster (no network delay)
    assert duration2 < 1.0, f"Cache hit took {duration2:.2f}s, expected <1s"

    # First fetch includes network time
    # (May be fast on localhost, but cache hit should be faster)
    assert duration2 < duration1 or duration2 < 0.5, "Cache hit should be faster than network fetch"


def test_cache_clear(test_config, test_logger, mock_http_server, tmp_path):
    """
    Test that cache can be cleared.

    Article 3.5: "cache clearing supported"
    """
    cache_dir = tmp_path / "cache"
    test_config.data["cache_dir"] = str(cache_dir)

    fetcher = Fetcher(test_config, test_logger)

    # Fetch some pages
    urls = [f"{mock_http_server}/page1", f"{mock_http_server}/page2"]

    for url in urls:
        fetcher.fetch(url)

    # Verify cache files exist
    cache_files = list(cache_dir.glob("*.html"))
    assert len(cache_files) == 2, f"Expected 2 cache files, found {len(cache_files)}"

    # Clear cache
    fetcher.clear_cache()

    # Verify cache cleared
    cache_files = list(cache_dir.glob("*.html"))
    assert len(cache_files) == 0, f"Expected 0 cache files after clear, found {len(cache_files)}"

    # Verify stats reset
    stats = fetcher.get_cache_stats()
    assert stats["hits"] == 0, "Cache hits should be reset"
    assert stats["misses"] == 0, "Cache misses should be reset"


def test_cache_refresh_flag(test_config, test_logger, mock_http_server, tmp_path):
    """
    Test that refresh=True forces re-fetch even with valid cache.
    """
    cache_dir = tmp_path / "cache"
    test_config.data["cache_dir"] = str(cache_dir)

    fetcher = Fetcher(test_config, test_logger)
    url = f"{mock_http_server}/page1"

    # First fetch
    content1 = fetcher.fetch(url)

    # Second fetch with refresh=True should re-fetch
    content2 = fetcher.fetch(url, refresh=True)

    # Content should match (same source)
    assert content2 == content1

    # Stats should show miss for refresh
    stats = fetcher.get_cache_stats()
    assert stats["misses"] == 2, "Refresh should count as cache miss"


def test_cache_with_use_cache_false(test_config, test_logger, mock_http_server, tmp_path):
    """
    Test that use_cache=False bypasses cache.
    """
    cache_dir = tmp_path / "cache"
    test_config.data["cache_dir"] = str(cache_dir)

    fetcher = Fetcher(test_config, test_logger)
    url = f"{mock_http_server}/page1"

    # First fetch
    fetcher.fetch(url)

    # Second fetch with use_cache=False
    fetcher.fetch(url, use_cache=False)

    # Should have 2 misses (both network fetches)
    stats = fetcher.get_cache_stats()
    assert stats["misses"] == 2
    assert stats["hits"] == 0


def test_cache_bytes_tracked(test_config, test_logger, mock_http_server, tmp_path):
    """
    Test that cache statistics include bytes_cached.
    """
    cache_dir = tmp_path / "cache"
    test_config.data["cache_dir"] = str(cache_dir)

    fetcher = Fetcher(test_config, test_logger)

    # Fetch a page
    fetcher.fetch(f"{mock_http_server}/page1")

    # Check stats
    stats = fetcher.get_cache_stats()

    assert "bytes_cached" in stats, "Stats should include bytes_cached"
    assert stats["bytes_cached"] > 0, "bytes_cached should be > 0 after caching content"
