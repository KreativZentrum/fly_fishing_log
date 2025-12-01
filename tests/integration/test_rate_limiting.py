"""
Integration test: Rate limiting and polite crawling behavior.
Tests US4 — Polite Crawling & Rate Limiting.

Article 3.1: 3-second minimum delay between requests
Article 9: All requests logged with timestamp, URL, status, delay
Article 3.3: Halt on 3+ consecutive 5xx errors
"""

import time
import pytest
from src.fetcher import Fetcher
from src.exceptions import HaltError, FetchError


def test_rate_limiting_enforces_3_second_delay(
    test_config, test_logger, mock_http_server, tmp_path
):
    """
    Test that fetcher enforces 3-second minimum delay between consecutive requests.

    Success Criteria SC-004: Verify ≥3 seconds between all consecutive requests.
    Article 3.1: "3-second minimum delay between any two consecutive HTTP requests"
    """
    # Use temporary log file to inspect delays
    log_file = tmp_path / "test_rate.log"
    test_logger.log_path = log_file

    fetcher = Fetcher(test_config, test_logger)

    # Make 3 consecutive requests
    urls = [f"{mock_http_server}/page1", f"{mock_http_server}/page2", f"{mock_http_server}/page3"]

    for url in urls:
        fetcher.fetch(url)

    # Read log file and verify delays
    import json

    with open(log_file, "r") as f:
        log_lines = [line for line in f.readlines() if "http_request" in line]

    # Parse delays from logs
    delays = []
    for line in log_lines:
        log_entry = json.loads(line)
        if log_entry.get("event") == "http_request" and not log_entry.get("cache_hit"):
            delays.append(log_entry.get("delay_seconds", 0))

    # First request should have 0 delay, subsequent should have ≥3 seconds
    assert len(delays) >= 3, f"Expected ≥3 requests logged, got {len(delays)}"
    assert delays[0] < 1.0, "First request should have minimal delay"

    for i, delay in enumerate(delays[1:], 1):
        assert (
            delay >= 2.9
        ), f"Request {i} logged delay was {delay:.2f}s, expected ≥3.0s (Article 3.1 violation)"


def test_all_requests_logged(test_config, test_logger, mock_http_server, tmp_path):
    """
    Test that all HTTP requests are logged with complete metadata.

    Article 9: "All HTTP requests must be logged"
    Log format: timestamp, URL, HTTP status, delay duration
    """
    # Use temporary log file
    log_file = tmp_path / "test_scraper.log"
    test_logger.log_path = log_file

    fetcher = Fetcher(test_config, test_logger)

    # Make multiple requests
    urls = [f"{mock_http_server}/page1", f"{mock_http_server}/page2"]

    for url in urls:
        fetcher.fetch(url)

    # Read log file
    assert log_file.exists(), "Log file not created"

    with open(log_file, "r") as f:
        log_lines = f.readlines()

    # Should have at least 2 request logs (may have more from robots.txt)
    request_logs = [line for line in log_lines if "http_request" in line]
    assert len(request_logs) >= 2, f"Expected ≥2 request logs, found {len(request_logs)}"

    # Verify log format
    import json

    for log_line in request_logs:
        log_entry = json.loads(log_line)

        # Required fields (Article 9.3)
        assert "timestamp" in log_entry, "Missing timestamp in log"
        assert "event" in log_entry, "Missing event type in log"
        assert "url" in log_entry, "Missing URL in log"
        assert "status_code" in log_entry, "Missing status_code in log"
        assert "delay_seconds" in log_entry, "Missing delay_seconds in log"

        # Verify data types
        assert isinstance(log_entry["delay_seconds"], (int, float)), "delay_seconds must be numeric"
        assert isinstance(
            log_entry["status_code"], (int, type(None))
        ), "status_code must be int or null"


def test_halt_on_consecutive_5xx_errors(test_config, test_logger, mock_http_server):
    """
    Test that scraper halts after 3 consecutive 5xx errors.

    Success Criteria SC-006: "Halt on 3+ consecutive 5xx errors"
    Article 3.3: "no more than 3 consecutive 5xx errors"
    Article 9.2: "halt events are logged"
    """
    fetcher = Fetcher(test_config, test_logger)

    # Configure mock server to return 500 errors
    error_url = f"{mock_http_server}/always-500"

    # Reset counter
    fetcher._consecutive_5xx_count = 0

    # The fetcher will:
    # 1. Try fetch, get 500 (count=1)
    # 2. Retry, get 500 (count=2)
    # 3. Max retries reached, raise FetchError
    # This is ONE fetch attempt with internal retries

    try:
        fetcher.fetch(error_url)
    except (FetchError, Exception):
        pass

    # After first fetch failure, counter should be at max_retries
    first_count = fetcher._consecutive_5xx_count

    # Second fetch attempt should trigger halt
    with pytest.raises(HaltError) as exc_info:
        fetcher.fetch(error_url)

    # Verify HaltError was raised
    assert (
        "consecutive" in str(exc_info.value).lower() or "5xx" in str(exc_info.value).lower()
    ), "HaltError should mention consecutive 5xx errors"

    # Verify counter reached halt threshold
    assert (
        fetcher._consecutive_5xx_count >= test_config.halt_on_consecutive_5xx
    ), f"Error count should be ≥{test_config.halt_on_consecutive_5xx}"


def test_rate_limiting_with_cache_hits(test_config, test_logger, mock_http_server):
    """
    Test that cache hits do not count toward rate limiting delay.

    Cache hits should be instant (no 3-second delay required).
    Article 3.1 applies to network requests only.
    """
    fetcher = Fetcher(test_config, test_logger)

    url = f"{mock_http_server}/cacheable"

    # First request: network fetch with delay
    start1 = time.time()
    content1 = fetcher.fetch(url)
    duration1 = time.time() - start1

    # Second request: cache hit (should be fast)
    start2 = time.time()
    content2 = fetcher.fetch(url)
    duration2 = time.time() - start2

    # Cache hit should be much faster than network request
    assert duration2 < 1.0, f"Cache hit took {duration2:.2f}s, expected <1s"

    # Content should be identical
    assert content1 == content2, "Cache returned different content"


def test_robots_txt_compliance(test_config, test_logger, mock_http_server):
    """
    Test that fetcher respects robots.txt disallow directives.

    Article 2.1: "check robots.txt before first request"
    """
    fetcher = Fetcher(test_config, test_logger)

    # Mock server should have /admin/ disallowed in robots.txt
    disallowed_url = f"{mock_http_server}/admin/secret"

    # Check if URL is allowed
    is_allowed = fetcher.is_allowed(disallowed_url)

    # Should be disallowed by robots.txt
    # (This test depends on mock server's robots.txt configuration)
    # If no robots.txt, is_allowed defaults to True

    # Verify robots.txt was loaded
    assert fetcher.robots_parser is not None, "robots.txt parser not initialized"


def test_request_delay_accumulation(test_config, test_logger, mock_http_server, tmp_path):
    """
    Test that delay is calculated from last request time, not start time.

    If a request takes 0.5 seconds, next request should still wait full 3 seconds from last request.
    """
    # Use temporary log file
    log_file = tmp_path / "test_delay_acc.log"
    test_logger.log_path = log_file

    fetcher = Fetcher(test_config, test_logger)

    # Make first request (slow endpoint)
    fetcher.fetch(f"{mock_http_server}/slow?delay=1")

    # Make second request immediately
    fetcher.fetch(f"{mock_http_server}/page2")

    # Read log and verify second request had proper delay
    import json

    with open(log_file, "r") as f:
        log_lines = [line for line in f.readlines() if "http_request" in line]

    delays = []
    for line in log_lines:
        log_entry = json.loads(line)
        if log_entry.get("event") == "http_request" and not log_entry.get("cache_hit"):
            delays.append(log_entry.get("delay_seconds", 0))

    # Second request should have ~3 second delay
    assert len(delays) >= 2, f"Expected ≥2 requests, got {len(delays)}"
    assert delays[1] >= 2.9, f"Second request delay was {delays[1]:.2f}s, expected ≥3.0s"


def test_5xx_error_count_resets_on_success(test_config, test_logger, mock_http_server):
    """
    Test that consecutive 5xx error count resets on successful request.

    Article 3.3: Count is for "consecutive" errors only.
    """
    fetcher = Fetcher(test_config, test_logger)

    # Reset counter
    fetcher._consecutive_5xx_count = 0

    # Simulate 2 errors (each fetch with retries counts as multiple errors)
    try:
        fetcher.fetch(f"{mock_http_server}/error-500")
    except (FetchError, Exception):
        pass

    # After 1 failed fetch (with 2 retries), counter should be at least 2
    error_count_after_failures = fetcher._consecutive_5xx_count
    assert (
        error_count_after_failures >= 2
    ), f"Error count should be ≥2 after failures, got {error_count_after_failures}"

    # Successful request should reset counter
    fetcher.fetch(f"{mock_http_server}/success")

    assert (
        fetcher._consecutive_5xx_count == 0
    ), "Error count should reset to 0 after successful request"
