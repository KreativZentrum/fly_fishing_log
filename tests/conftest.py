"""
Pytest fixtures for NZ Flyfishing Web Scraper tests.
"""

import pytest
import tempfile
import sqlite3
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

from src.config import Config
from src.logger import ScraperLogger
from src.storage import Storage
from src.fetcher import Fetcher


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_config(temp_dir):
    """
    Create test configuration with temporary paths.

    Returns:
        Config instance with temp database, logs, cache
    """
    config_path = temp_dir / "test_config.yaml"
    config_content = f"""
base_url: "http://localhost:8000"
user_agent: "test-scraper/1.0"

request_delay: 3.0
jitter_max: 0.0

cache_dir: "{temp_dir / 'cache'}/"
cache_ttl: 86400

max_retries: 2
retry_backoff: [1, 2]
halt_on_consecutive_5xx: 3

database_path: "{temp_dir / 'test.db'}"
log_path: "{temp_dir / 'test.log'}"
output_dir: "{temp_dir / 'pdfs'}/"

discovery_rules:
  index_path: "/index.html"
  region_selector: "div.region-list a"
  river_selector: ".fishing-waters a"
  detail_selectors:
    name: "h1.river-name"
    description: "div.description"

pdf_config:
  template_dir: "templates/"
  page_size: "A4"
  orientation: "portrait"
"""
    config_path.write_text(config_content)
    return Config(str(config_path))


@pytest.fixture
def test_logger(temp_dir):
    """
    Create test logger instance.

    Returns:
        ScraperLogger instance writing to temp log file
    """
    log_path = temp_dir / "test.log"
    return ScraperLogger(str(log_path))


@pytest.fixture
def test_storage(test_config, test_logger):
    """
    Create test storage with initialized schema.

    Returns:
        Storage instance with empty database
    """
    storage = Storage(test_config.database_path, test_logger)
    storage.initialize_schema()
    yield storage
    storage.close()


@pytest.fixture
def test_fetcher(test_config, test_logger):
    """
    Create test fetcher instance.

    Returns:
        Fetcher instance configured for testing
    """
    fetcher = Fetcher(test_config, test_logger)
    yield fetcher
    fetcher.close()


@pytest.fixture
def sample_region_data():
    """Sample region data for testing."""
    return {
        "name": "Test Region",
        "slug": "test-region",
        "canonical_url": "http://example.com/region/test-region",
        "source_url": "http://example.com/regions",
        "raw_html": "<html><body>Test Region Page</body></html>",
        "description": "A test region for unit tests",
        "crawl_timestamp": "2024-01-15T12:00:00Z",
    }


@pytest.fixture
def sample_river_data():
    """Sample river data for testing."""
    return {
        "region_id": 1,
        "name": "Test River",
        "slug": "test-river",
        "canonical_url": "http://example.com/river/test-river",
        "raw_html": "<html><body>Test River Page</body></html>",
        "crawl_timestamp": "2024-01-15T12:00:00Z",
    }


@pytest.fixture
def sample_section_data():
    """Sample section data for testing."""
    return {
        "river_id": 1,
        "name": "Upper Section",
        "slug": "upper-section",
        "canonical_url": "http://example.com/river/test-river#upper-section",
        "raw_html": "<div>Upper section details</div>",
    }


@pytest.fixture
def sample_fly_data():
    """Sample fly data for testing."""
    return {
        "river_id": 1,
        "section_id": None,
        "name": "Royal Wulff",
        "raw_text": "Royal Wulff size 12-16",
        "category": None,  # Per Article 5.2
        "size": None,
        "color": None,
        "notes": None,
        "crawl_timestamp": "2024-01-15T12:00:00Z",
    }


@pytest.fixture
def sample_regulation_data():
    """Sample regulation data for testing."""
    return {
        "river_id": 1,
        "section_id": None,
        "type": "Bag Limit",
        "value": "2 fish per day",
        "raw_text": "Daily limit: 2 trout",
        "source_section": "Regulations",
        "crawl_timestamp": "2024-01-15T12:00:00Z",
    }


@pytest.fixture
def populated_storage(test_storage, sample_region_data, sample_river_data):
    """
    Storage instance with sample data.

    Returns:
        Storage instance with 1 region and 1 river
    """
    region_id = test_storage.insert_region(**sample_region_data)
    sample_river_data["region_id"] = region_id
    river_id = test_storage.insert_river(**sample_river_data)

    yield test_storage


@pytest.fixture(autouse=True)
def reset_rate_limiter(test_fetcher):
    """Reset fetcher rate limiter before each test."""
    test_fetcher._last_request_time = 0
    test_fetcher._consecutive_5xx_count = 0
    yield


class MockHTTPHandler(BaseHTTPRequestHandler):
    """Mock HTTP request handler for testing."""

    def log_message(self, format, *args):
        """Suppress request logging."""
        pass

    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/robots.txt":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            robots_txt = b"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /private/
"""
            self.wfile.write(robots_txt)

        elif self.path.startswith("/always-500") or self.path.startswith("/error-500"):
            self.send_response(500)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body>Internal Server Error</body></html>")

        elif self.path.startswith("/slow"):
            # Simulate slow response
            import time

            time.sleep(0.5)
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body>Slow response</body></html>")

        elif "/success" in self.path or self.path.startswith("/page"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            page_num = self.path.split("/")[-1]
            self.wfile.write(f"<html><body>Page {page_num}</body></html>".encode())

        elif "/cacheable" in self.path:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Cache-Control", "max-age=3600")
            self.end_headers()
            self.wfile.write(b"<html><body>Cacheable content</body></html>")

        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body>Not Found</body></html>")


@pytest.fixture(scope="function")
def mock_http_server():
    """
    Start mock HTTP server for testing.

    Returns:
        Base URL of mock server (e.g., "http://localhost:8888")
    """
    server = HTTPServer(("localhost", 0), MockHTTPHandler)
    port = server.server_port

    # Start server in background thread
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    yield f"http://localhost:{port}"

    # Shutdown server
    server.shutdown()
    server_thread.join(timeout=1.0)
