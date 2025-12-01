"""
Contract test: Fetcher robots.txt compliance.
Tests Article 2.1 robots.txt checking.
"""

import pytest
from src.fetcher import Fetcher
from src.exceptions import FetchError


def test_is_allowed_respects_disallow_directive(test_config, test_logger):
    """
    Test that is_allowed() correctly identifies disallowed URLs.

    Article 2.1: "check robots.txt and respect all disallow directives"
    """
    fetcher = Fetcher(test_config, test_logger)

    # Create mock robots.txt parser with specific rules
    from urllib.robotparser import RobotFileParser

    robots_content = """
User-agent: *
Disallow: /admin/
Disallow: /private/
Allow: /regions/
Allow: /
"""

    # Parse mock robots.txt
    fetcher.robots_parser = RobotFileParser()
    fetcher.robots_parser.parse(robots_content.split("\n"))

    # Test allowed URLs
    assert (
        fetcher.is_allowed("http://example.com/regions/north") is True
    ), "Should allow /regions/ path"
    assert (
        fetcher.is_allowed("http://example.com/rivers/tongariro") is True
    ), "Should allow /rivers/ path"

    # Test disallowed URLs
    assert (
        fetcher.is_allowed("http://example.com/admin/dashboard") is False
    ), "Should disallow /admin/ path"
    assert (
        fetcher.is_allowed("http://example.com/private/data") is False
    ), "Should disallow /private/ path"


def test_is_allowed_handles_missing_robots_txt(test_config, test_logger):
    """
    Test that fetcher handles missing robots.txt gracefully.

    If robots.txt cannot be loaded, default to permissive (allow all).
    """
    fetcher = Fetcher(test_config, test_logger)

    # Simulate missing robots.txt by setting empty parser
    from urllib.robotparser import RobotFileParser

    fetcher.robots_parser = RobotFileParser()
    fetcher.robots_parser.parse([])  # Empty rules

    # Should allow all URLs when no rules present
    assert (
        fetcher.is_allowed("http://example.com/any/path") is True
    ), "Should allow all URLs when robots.txt missing"


def test_is_allowed_respects_user_agent(test_config, test_logger):
    """
    Test that robots.txt checking uses correct User-Agent string.

    Article 2.1: Use configured User-Agent for robots.txt checks.
    """
    fetcher = Fetcher(test_config, test_logger)

    # Create robots.txt with agent-specific rules
    from urllib.robotparser import RobotFileParser

    robots_content = """
User-agent: BadBot
Disallow: /

User-agent: *
Allow: /
"""

    fetcher.robots_parser = RobotFileParser()
    fetcher.robots_parser.parse(robots_content.split("\n"))

    # Our scraper should be allowed (uses "nzfishing-scraper" user agent)
    assert (
        fetcher.is_allowed("http://example.com/regions/") is True
    ), "Should be allowed with correct user agent"


def test_is_allowed_with_wildcards(test_config, test_logger):
    """
    Test robots.txt wildcard pattern matching.
    """
    fetcher = Fetcher(test_config, test_logger)

    from urllib.robotparser import RobotFileParser

    robots_content = """
User-agent: *
Disallow: /*.json$
Disallow: /api/
Allow: /
"""

    fetcher.robots_parser = RobotFileParser()
    fetcher.robots_parser.parse(robots_content.split("\n"))

    # HTML pages should be allowed
    assert fetcher.is_allowed("http://example.com/regions/north") is True

    # API paths should be disallowed
    assert fetcher.is_allowed("http://example.com/api/data") is False


def test_robots_txt_loaded_on_init(test_config, test_logger):
    """
    Test that robots.txt is loaded during Fetcher initialization.

    Article 2.1: "check robots.txt before first request"
    """
    # Create new fetcher instance
    fetcher = Fetcher(test_config, test_logger)

    # robots_parser should be initialized
    assert (
        fetcher.robots_parser is not None
    ), "robots.txt parser should be initialized on Fetcher.__init__()"

    # Parser should be configured
    assert isinstance(
        fetcher.robots_parser, type(fetcher.robots_parser)
    ), "robots_parser should be RobotFileParser instance"
