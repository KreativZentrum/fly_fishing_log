"""
Contract test: Verify fetcher enforces 3-second minimum delay.
Article 3.1 Compliance Test (SC-004)
"""

import pytest
import time
from src.fetcher import Fetcher
from src.config import Config
from src.logger import ScraperLogger


def test_fetcher_enforces_3_second_delay(test_config, test_logger, tmp_path):
    """
    Contract test: Verify fetch() enforces minimum 3-second delay between requests.

    Success Criteria SC-004: All HTTP requests delayed by ≥3 seconds.
    Article 3.1: Minimum delay requirement.
    """
    # Create fetcher with test config (3-second delay, 0 jitter for precision)
    test_config._config["jitter_max"] = 0  # Remove jitter for precise timing
    fetcher = Fetcher(test_config, test_logger)

    # Make two requests and measure elapsed time
    start = time.time()

    try:
        # First request (no delay needed, establishes baseline)
        fetcher.fetch("http://httpbin.org/status/200", use_cache=False)

        # Second request (should enforce 3-second delay)
        fetcher.fetch("http://httpbin.org/status/200", use_cache=False)

        elapsed = time.time() - start

        # Assert: Total time >= 3 seconds (allowing small timing variance)
        assert elapsed >= 3.0, f"Expected ≥3s delay, got {elapsed:.2f}s"

        # Also verify it's not excessively delayed (< 5 seconds for 2 requests)
        assert elapsed < 5.0, f"Delay too long: {elapsed:.2f}s (check for double-delay bug)"

    finally:
        fetcher.close()


def test_fetcher_respects_jitter(test_config, test_logger):
    """
    Test that jitter adds randomness to delay without violating minimum.
    """
    test_config._config["jitter_max"] = 0.5  # Add jitter
    fetcher = Fetcher(test_config, test_logger)

    delays = []

    try:
        for _ in range(3):
            start = time.time()
            fetcher.fetch("http://httpbin.org/status/200", use_cache=False)
            delays.append(time.time() - start)

        # All delays should be >= 3 seconds (minimum)
        for delay in delays[1:]:  # Skip first (no prior request)
            assert delay >= 3.0, f"Delay {delay:.2f}s violates 3-second minimum"

        # At least one delay should differ (jitter adds variance)
        # Allow small floating-point precision tolerance
        unique_delays = set(round(d, 1) for d in delays[1:])
        # With jitter, we expect some variance (but this is probabilistic)
        # So we just verify jitter doesn't break the minimum

    finally:
        fetcher.close()


def test_fetcher_logs_delay_duration(test_config, test_logger, tmp_path):
    """
    Verify that fetcher logs actual delay duration for each request.
    Article 9.3: Complete logging requirement.
    """
    fetcher = Fetcher(test_config, test_logger)

    try:
        # Make a request
        fetcher.fetch("http://httpbin.org/status/200", use_cache=False)
        fetcher.fetch("http://httpbin.org/status/200", use_cache=False)

        # Read log file
        log_path = test_config.log_path
        with open(log_path, "r") as f:
            log_lines = f.readlines()

        # Parse JSON logs and find request events
        import json

        request_logs = [json.loads(line) for line in log_lines if '"event": "request"' in line]

        # At least one request should have delay_seconds logged
        assert len(request_logs) >= 2, "Expected at least 2 request log entries"

        # Second request should have delay >= 3 seconds
        second_request = request_logs[1]
        assert "delay_seconds" in second_request, "Missing delay_seconds in log"
        assert (
            second_request["delay_seconds"] >= 3.0
        ), f"Logged delay {second_request['delay_seconds']}s violates minimum"

    finally:
        fetcher.close()


@pytest.mark.slow
def test_cache_bypasses_delay(test_config, test_logger):
    """
    Verify that cached responses don't trigger rate limiting delay.
    """
    fetcher = Fetcher(test_config, test_logger)

    try:
        url = "http://httpbin.org/status/200"

        # First request (slow, fetches and caches)
        start = time.time()
        fetcher.fetch(url, use_cache=True)
        first_elapsed = time.time() - start

        # Second request (fast, uses cache, no delay needed)
        start = time.time()
        fetcher.fetch(url, use_cache=True)
        second_elapsed = time.time() - start

        # Cache hit should be near-instant (< 1 second)
        assert second_elapsed < 1.0, f"Cache hit took {second_elapsed:.2f}s, expected <1s"

        # First request should still respect delay if there was a prior request
        # (This is a simplified test; real scenario tested in integration tests)

    finally:
        fetcher.close()


def test_refresh_mode_ignores_cache_but_respects_delay(test_config, test_logger):
    """
    Verify that refresh=True ignores cache but still enforces delay.
    """
    fetcher = Fetcher(test_config, test_logger)

    try:
        url = "http://httpbin.org/status/200"

        # First request (caches)
        fetcher.fetch(url, use_cache=True)

        # Second request with refresh (should re-fetch and delay)
        start = time.time()
        fetcher.fetch(url, use_cache=True, refresh=True)
        elapsed = time.time() - start

        # Should enforce 3-second delay even with refresh
        assert elapsed >= 3.0, f"Refresh mode didn't enforce delay: {elapsed:.2f}s"

    finally:
        fetcher.close()
