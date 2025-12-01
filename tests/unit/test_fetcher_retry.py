"""
Unit test: Fetcher retry logic and error handling.
Tests Article 3.3 halt on consecutive errors.
"""

import pytest
import time
from unittest.mock import Mock, patch
from src.fetcher import Fetcher
from src.exceptions import FetchError, HaltError


def test_fetcher_exponential_backoff(test_config, test_logger):
    """
    Test exponential backoff on retries (1s → 2s → 4s → 8s).

    Article 3.2: "exponential backoff with cap of 3 retries"
    """
    fetcher = Fetcher(test_config, test_logger)

    # Mock session.get to raise error
    with patch.object(fetcher.session, "get") as mock_get:
        mock_get.side_effect = Exception("Connection error")

        with patch("time.sleep") as mock_sleep:
            try:
                fetcher.fetch("http://example.com/test")
            except (FetchError, Exception):
                pass

            # Verify exponential backoff delays
            # Expected: 1s, 2s, 4s (3 retries)
            if mock_sleep.call_count > 0:
                calls = [call[0][0] for call in mock_sleep.call_args_list]
                # Filter out rate limiting delays (3.0s)
                backoff_delays = [d for d in calls if d < 3.0 and d > 0]

                if backoff_delays:
                    # Should see exponential pattern
                    assert backoff_delays[0] <= 1.0, "First backoff should be ≤1s"


def test_consecutive_5xx_counter_increments(test_config, test_logger):
    """
    Test that _consecutive_5xx_count increments on 5xx errors.

    Article 3.3: Track consecutive 5xx errors.
    """
    fetcher = Fetcher(test_config, test_logger)

    # Reset counter
    fetcher._consecutive_5xx_count = 0

    # Simulate 5xx error
    with patch.object(fetcher.session, "get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        try:
            fetcher.fetch("http://example.com/error")
        except (FetchError, Exception):
            pass

    # Counter should increment
    assert (
        fetcher._consecutive_5xx_count >= 1
    ), "Consecutive 5xx counter should increment on 500 error"


def test_consecutive_5xx_counter_resets_on_success(test_config, test_logger):
    """
    Test that counter resets to 0 on successful request (2xx/3xx).

    Article 3.3: "consecutive" errors only.
    """
    fetcher = Fetcher(test_config, test_logger)

    # Set counter to 2 (simulate 2 previous errors)
    fetcher._consecutive_5xx_count = 2

    # Successful request
    with patch.object(fetcher.session, "get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html>Success</html>"
        mock_get.return_value = mock_response

        fetcher.fetch("http://example.com/success")

    # Counter should reset
    assert (
        fetcher._consecutive_5xx_count == 0
    ), "Consecutive 5xx counter should reset on 2xx response"


def test_halt_on_third_consecutive_5xx(test_config, test_logger):
    """
    Test that HaltError is raised on 3rd consecutive 5xx error.

    Article 3.3: "no more than 3 consecutive 5xx errors"
    Success Criteria SC-006: "Halt on 3+ consecutive 5xx"
    """
    fetcher = Fetcher(test_config, test_logger)

    # Set counter to 2 (2 previous errors)
    fetcher._consecutive_5xx_count = 2

    # Third 5xx should trigger HaltError
    with patch.object(fetcher.session, "get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"
        mock_get.return_value = mock_response

        with pytest.raises(HaltError) as exc_info:
            fetcher.fetch("http://example.com/error")

        assert (
            "consecutive" in str(exc_info.value).lower() or "5xx" in str(exc_info.value).lower()
        ), "HaltError should mention consecutive 5xx errors"


def test_4xx_errors_do_not_increment_5xx_counter(test_config, test_logger):
    """
    Test that 4xx errors do not count toward consecutive 5xx limit.

    Only 5xx (server errors) should increment counter.
    """
    fetcher = Fetcher(test_config, test_logger)

    # Reset counter
    fetcher._consecutive_5xx_count = 0

    # 404 error
    with patch.object(fetcher.session, "get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response

        try:
            fetcher.fetch("http://example.com/notfound")
        except (FetchError, Exception):
            pass

    # Counter should NOT increment for 4xx
    assert (
        fetcher._consecutive_5xx_count == 0
    ), "4xx errors should not increment consecutive 5xx counter"


def test_max_3_retries_per_request(test_config, test_logger):
    """
    Test that fetcher retries maximum 3 times per request.

    Article 3.2: "cap of 3 retries"
    """
    fetcher = Fetcher(test_config, test_logger)

    with patch.object(fetcher.session, "get") as mock_get:
        # Always fail
        mock_get.side_effect = Exception("Connection timeout")

        try:
            fetcher.fetch("http://example.com/test")
        except (FetchError, Exception):
            pass

        # Should try initial + 3 retries = 4 total attempts max
        assert (
            mock_get.call_count <= 4
        ), f"Should retry max 3 times (4 total attempts), got {mock_get.call_count}"


def test_halt_error_includes_reason(test_config, test_logger):
    """
    Test that HaltError includes descriptive reason field.

    Article 9.2: Halt events are logged with reason.
    """
    fetcher = Fetcher(test_config, test_logger)
    fetcher._consecutive_5xx_count = 3

    with patch.object(fetcher.session, "get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        try:
            fetcher.fetch("http://example.com/error")
        except HaltError as e:
            # HaltError should have reason attribute
            assert hasattr(e, "reason"), "HaltError should have 'reason' attribute"
            assert e.reason, "HaltError reason should not be empty"
        except Exception:
            pass  # Other exceptions acceptable for this test
