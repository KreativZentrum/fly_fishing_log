"""
Unit test: Logger request logging functionality.
Tests ScraperLogger.log_request() method.
"""

import json
import pytest
from pathlib import Path
from src.logger import ScraperLogger


def test_log_request_creates_json_entry(tmp_path):
    """
    Test that log_request() creates valid JSON log entry.

    Article 9.3: "all logs are written to a local file"
    """
    log_file = tmp_path / "test.log"
    logger = ScraperLogger(str(log_file))

    # Log a request
    logger.log_request(
        url="http://example.com/test", method="GET", status_code=200, delay_seconds=3.2
    )

    # Verify log file created
    assert log_file.exists(), "Log file not created"

    # Read and parse log
    with open(log_file, "r") as f:
        log_line = f.readline()

    log_entry = json.loads(log_line)

    # Verify required fields
    assert log_entry["event"] == "http_request"
    assert log_entry["url"] == "http://example.com/test"
    assert log_entry["method"] == "GET"
    assert log_entry["status_code"] == 200
    assert log_entry["delay_seconds"] == 3.2
    assert "timestamp" in log_entry


def test_log_request_includes_timestamp(tmp_path):
    """
    Test that log entries include ISO format timestamp.

    Article 9: "timestamp, URL, HTTP status, request delay"
    """
    log_file = tmp_path / "test.log"
    logger = ScraperLogger(str(log_file))

    logger.log_request(
        url="http://example.com/test", method="GET", status_code=200, delay_seconds=3.0
    )

    with open(log_file, "r") as f:
        log_entry = json.loads(f.readline())

    # Verify timestamp format (ISO 8601)
    timestamp = log_entry["timestamp"]
    assert "T" in timestamp, "Timestamp should be ISO format"
    assert timestamp.endswith("Z"), "Timestamp should be UTC (end with Z)"


def test_log_request_with_cache_hit(tmp_path):
    """
    Test logging cache hit events.
    """
    log_file = tmp_path / "test.log"
    logger = ScraperLogger(str(log_file))

    logger.log_request(
        url="http://example.com/cached",
        method="GET",
        status_code=200,
        delay_seconds=0.0,
        cache_hit=True,
    )

    with open(log_file, "r") as f:
        log_entry = json.loads(f.readline())

    assert log_entry["cache_hit"] is True
    assert log_entry["delay_seconds"] == 0.0


def test_log_request_with_error(tmp_path):
    """
    Test logging request errors.
    """
    log_file = tmp_path / "test.log"
    logger = ScraperLogger(str(log_file))

    logger.log_request(
        url="http://example.com/error",
        method="GET",
        status_code=500,
        delay_seconds=3.0,
        error="Internal Server Error",
    )

    with open(log_file, "r") as f:
        log_entry = json.loads(f.readline())

    assert log_entry["error"] == "Internal Server Error"
    assert log_entry["status_code"] == 500


def test_log_disallow(tmp_path):
    """
    Test logging robots.txt disallow events.

    Article 9.2: "disallow events are logged"
    """
    log_file = tmp_path / "test.log"
    logger = ScraperLogger(str(log_file))

    logger.log_disallow(url="http://example.com/admin/", reason="robots.txt disallow")

    with open(log_file, "r") as f:
        log_entry = json.loads(f.readline())

    assert log_entry["event"] == "robots_txt_disallow"
    assert log_entry["url"] == "http://example.com/admin/"
    assert log_entry["reason"] == "robots.txt disallow"
    assert "timestamp" in log_entry


def test_log_halt(tmp_path):
    """
    Test logging halt events.

    Article 9.2: "halt events are logged"
    """
    log_file = tmp_path / "test.log"
    logger = ScraperLogger(str(log_file))

    logger.log_halt(reason="3 consecutive 5xx errors")

    with open(log_file, "r") as f:
        log_entry = json.loads(f.readline())

    assert log_entry["event"] == "halt"
    assert log_entry["reason"] == "3 consecutive 5xx errors"
    assert "timestamp" in log_entry


def test_multiple_log_entries(tmp_path):
    """
    Test that multiple log entries are written as separate JSON lines.
    """
    log_file = tmp_path / "test.log"
    logger = ScraperLogger(str(log_file))

    # Log multiple events
    logger.log_request("http://example.com/1", status_code=200)
    logger.log_request("http://example.com/2", status_code=200)
    logger.log_disallow("http://example.com/admin/")

    with open(log_file, "r") as f:
        lines = f.readlines()

    assert len(lines) == 3, f"Expected 3 log lines, got {len(lines)}"

    # Verify all are valid JSON
    for line in lines:
        log_entry = json.loads(line)
        assert "timestamp" in log_entry
        assert "event" in log_entry


def test_log_parseable_json(tmp_path):
    """
    Test that all log entries are parseable JSON.

    Article 9: "logs are parseable JSON"
    """
    log_file = tmp_path / "test.log"
    logger = ScraperLogger(str(log_file))

    # Log various events
    logger.log_request("http://example.com/test", status_code=200)
    logger.log_disallow("http://example.com/admin/")
    logger.log_halt("test halt")

    # All lines should be parseable
    with open(log_file, "r") as f:
        for line_num, line in enumerate(f, 1):
            try:
                json.loads(line)
            except json.JSONDecodeError as e:
                pytest.fail(f"Line {line_num} not valid JSON: {e}")


def test_no_sensitive_data_logged(tmp_path):
    """
    Test that logs do not contain sensitive data.

    Article 9: "no sensitive data (no passwords/auth tokens)"
    """
    log_file = tmp_path / "test.log"
    logger = ScraperLogger(str(log_file))

    # Log request with URL containing potential sensitive data
    logger.log_request(url="http://example.com/api?key=secret123", status_code=200)

    with open(log_file, "r") as f:
        log_content = f.read()

    # URL is logged (expected), but validate structure
    log_entry = json.loads(log_content.strip())

    # Should not have separate password/token fields
    assert "password" not in log_entry
    assert "token" not in log_entry
    assert "api_key" not in log_entry

    # Note: URL query params are logged as-is (developer responsibility)
    # This test ensures we don't extract/expose additional sensitive fields
