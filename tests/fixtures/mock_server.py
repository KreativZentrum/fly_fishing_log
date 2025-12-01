"""
Mock HTTP server for integration tests.
Provides controlled test endpoints for scraper validation.
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import time
from pathlib import Path


class MockNZFishingHandler(SimpleHTTPRequestHandler):
    """
    Mock HTTP handler simulating nzfishing.com structure.
    """

    # Class variable to control error injection
    inject_5xx = False
    inject_5xx_count = 0

    def do_GET(self):
        """Handle GET requests."""

        # robots.txt (Article 2.1 compliance testing)
        if self.path == "/robots.txt":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(
                b"""User-agent: *
Disallow: /admin/
Disallow: /private/
Crawl-delay: 3
"""
            )
            return

        # Inject 5xx errors for testing halt behavior
        if self.inject_5xx and self.inject_5xx_count < 3:
            self.inject_5xx_count += 1
            self.send_response(503)
            self.send_header("Retry-After", "5")
            self.end_headers()
            self.wfile.write(b"Service Temporarily Unavailable")
            return

        # Index page (region discovery)
        if self.path == "/index.html" or self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(SAMPLE_INDEX_HTML.encode())
            return

        # Region page (river discovery)
        if self.path.startswith("/region/"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(SAMPLE_REGION_HTML.encode())
            return

        # River detail page
        if self.path.startswith("/river/"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(SAMPLE_RIVER_HTML.encode())
            return

        # Disallowed path (robots.txt testing)
        if self.path.startswith("/admin/") or self.path.startswith("/private/"):
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"Forbidden")
            return

        # 404 for everything else
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not Found")

    def log_message(self, format, *args):
        """Suppress request logging during tests."""
        pass


# Sample HTML content for testing
SAMPLE_INDEX_HTML = """
<!DOCTYPE html>
<html>
<head><title>NZ Fishing - Regions</title></head>
<body>
    <h1>New Zealand Fishing Regions</h1>
    <div class="region-list">
        <a href="/region/north-island" data-slug="north-island">North Island</a>
        <a href="/region/south-island" data-slug="south-island">South Island</a>
    </div>
</body>
</html>
"""

SAMPLE_REGION_HTML = """
<!DOCTYPE html>
<html>
<head><title>North Island Rivers</title></head>
<body>
    <h1>North Island Rivers</h1>
    <div class="river-list">
        <a href="/river/tongariro" data-slug="tongariro">Tongariro River</a>
        <a href="/river/rangitikei" data-slug="rangitikei">Rangitikei River</a>
    </div>
</body>
</html>
"""

SAMPLE_RIVER_HTML = """
<!DOCTYPE html>
<html>
<head><title>Tongariro River</title></head>
<body>
    <h1 class="river-name">Tongariro River</h1>
    <div class="description">
        <p>The Tongariro River is world-renowned for its trout fishing.</p>
    </div>
    
    <h2>Sections</h2>
    <div class="sections">
        <div class="section" data-slug="red-hut-pool">
            <h3>Red Hut Pool</h3>
            <p>Upper section with excellent brown trout fishing.</p>
        </div>
        <div class="section" data-slug="major-jones">
            <h3>Major Jones Pool</h3>
            <p>Popular pool with good access.</p>
        </div>
    </div>
    
    <h2>Recommended Flies</h2>
    <div class="flies">
        <ul>
            <li>Glo-bug - Red or pink, size 8-10</li>
            <li>Hare's Ear Nymph - Natural, size 12-14</li>
            <li>Royal Wulff - Dry fly, size 12-16</li>
        </ul>
    </div>
    
    <h2>Regulations</h2>
    <div class="regulations">
        <p><strong>Bag Limit:</strong> 3 trout per day</p>
        <p><strong>Size Limit:</strong> Minimum 35cm</p>
        <p><strong>Season:</strong> Year-round fishing</p>
        <p><strong>Methods:</strong> Fly fishing only in certain sections</p>
    </div>
</body>
</html>
"""


class MockServer:
    """
    Threaded mock HTTP server for testing.
    """

    def __init__(self, port=8000):
        """
        Initialize mock server.

        Args:
            port: Port to listen on (default 8000)
        """
        self.port = port
        self.server = HTTPServer(("localhost", port), MockNZFishingHandler)
        self.thread = None

    def start(self):
        """Start server in background thread."""
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        time.sleep(0.1)  # Give server time to start

    def stop(self):
        """Stop server."""
        self.server.shutdown()
        if self.thread:
            self.thread.join(timeout=1)

    def reset_error_injection(self):
        """Reset 5xx error injection counters."""
        MockNZFishingHandler.inject_5xx = False
        MockNZFishingHandler.inject_5xx_count = 0

    def enable_5xx_errors(self):
        """Enable 5xx error injection for next 3 requests."""
        MockNZFishingHandler.inject_5xx = True
        MockNZFishingHandler.inject_5xx_count = 0


# Pytest fixture (imported by conftest.py if needed)
def mock_server_fixture():
    """Pytest fixture for mock server."""
    server = MockServer(port=8000)
    server.start()
    yield server
    server.stop()
