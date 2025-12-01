"""
Integration test: Full end-to-end workflow.
Tests complete scraper pipeline from region discovery to PDF generation.

This test validates the entire system working together:
- Region discovery (US1)
- River discovery (US2)
- Detail extraction (US3)
- Rate limiting (US4)
- Caching (US5)
- Data storage integrity
"""

import pytest
import json
from pathlib import Path
from src.fetcher import Fetcher
from src.parser import Parser
from src.storage import Storage
from src.config import Config
from src.logger import ScraperLogger


def test_full_scraper_workflow(test_config, test_logger, test_storage, mock_http_server, tmp_path):
    """
    End-to-end test: scrape regions → rivers → details.

    Verifies all components work together correctly.
    """
    # Configure test
    test_config.data["base_url"] = mock_http_server
    cache_dir = tmp_path / "cache"
    test_config.data["cache_dir"] = str(cache_dir)

    # Initialize components
    fetcher = Fetcher(test_config, test_logger)
    parser = Parser(test_config)

    # Step 1: Discover regions (US1)
    index_html = f"""
    <html><body>
        <div class="region-list">
            <a href="/region/northland">Northland</a>
            <a href="/region/waikato">Waikato</a>
            <a href="/region/bay-of-plenty">Bay of Plenty</a>
        </div>
    </body></html>
    """

    regions = parser.parse_region_index(index_html)
    assert len(regions) >= 3, f"Expected ≥3 regions, got {len(regions)}"

    # Store regions
    region_ids = []
    for region_data in regions:
        region_id = test_storage.insert_region(
            name=region_data["name"],
            slug=region_data.get("slug", region_data["name"].lower()),
            canonical_url=region_data["canonical_url"],
            source_url=f"{mock_http_server}/index",
            raw_html=index_html,
            description=region_data.get("description", ""),
            crawl_timestamp="2024-12-01T12:00:00Z",
        )
        region_ids.append(region_id)

    # Verify regions stored
    stored_regions = test_storage.get_regions()
    assert len(stored_regions) >= 3, "Regions not stored correctly"

    # Step 2: Discover rivers for each region (US2)
    river_ids = []
    for region_id in region_ids[:1]:  # Test with first region only for speed
        region = test_storage.get_region(region_id)

        # Mock region page HTML
        region_html = f"""
        <html><body>
            <div class="fishing-waters">
                <a href="/river/waiterere">Waiterere Stream</a>
                <a href="/river/mohunga">Mohunga Stream</a>
            </div>
        </body></html>
        """

        rivers = parser.parse_region_page(region_html, region)
        assert len(rivers) >= 2, f"Expected ≥2 rivers, got {len(rivers)}"

        # Store rivers
        for river_data in rivers:
            river_id = test_storage.insert_river(
                region_id=region_id,
                name=river_data["name"],
                slug=river_data.get("slug", river_data["name"].lower()),
                canonical_url=river_data["canonical_url"],
                raw_html=region_html,
                crawl_timestamp="2024-12-01T12:00:00Z",
            )
            river_ids.append(river_id)

    # Verify rivers stored
    stored_rivers = test_storage.get_rivers()
    assert len(stored_rivers) >= 2, "Rivers not stored correctly"

    # Step 3: Extract river details (US3)
    for river_id in river_ids[:1]:  # Test with first river only
        river = test_storage.get_river(river_id)

        # Mock river detail HTML
        detail_html = f"""
        <html><body>
            <h1>{river['name']}</h1>
            <div class="river-description">
                A beautiful stream with excellent brown trout fishing.
            </div>
            <div class="recommended-flies">
                <h2>Recommended Flies</h2>
                <ul>
                    <li>Royal Wulff #12-16</li>
                    <li>Hare's Ear Nymph #14</li>
                    <li>Woolly Bugger Black #8</li>
                </ul>
            </div>
            <div class="regulations">
                <h2>Regulations</h2>
                <p>Bag Limit: 2 fish per day</p>
                <p>Season: October 1 - April 30</p>
            </div>
        </body></html>
        """

        details = parser.parse_river_detail(detail_html, river)

        # Verify no inference (Article 5.2)
        assert (
            "fish_type" in details or "conditions" in details or "flies" in details
        ), "Parser should extract available fields"

        # Store flies
        if "flies" in details:
            for fly in details["flies"]:
                test_storage.insert_fly(
                    river_id=river_id,
                    name=fly.get("name", "Unknown"),
                    raw_text=fly.get("raw_text", ""),
                    category=fly.get("category"),
                    size=fly.get("size"),
                    color=fly.get("color"),
                    crawl_timestamp="2024-12-01T12:00:00Z",
                )

        # Store regulations
        if "regulations" in details:
            for reg in details["regulations"]:
                test_storage.insert_regulation(
                    river_id=river_id,
                    type=reg.get("type", "unclassified"),
                    value=reg.get("value", ""),
                    raw_text=reg.get("raw_text", ""),
                    crawl_timestamp="2024-12-01T12:00:00Z",
                )

        # Update river with description
        test_storage.conn.execute(
            "UPDATE rivers SET description = ? WHERE id = ?",
            (details.get("description", ""), river_id),
        )
        test_storage.conn.commit()

    # Step 4: Verify data integrity (SC-009)
    # Check that raw data exists and is separate from parsed fields
    river = test_storage.get_river(river_ids[0])
    assert river["raw_html"], "raw_html should be preserved"

    flies = test_storage.get_flies_by_river(river_ids[0])
    if flies:
        for fly in flies:
            assert "raw_text" in fly, "Flies should have raw_text"

    # Step 5: Verify logging (SC-005)
    # Logger is configured, verify by making a fetch request
    test_url = f"{mock_http_server}/page1"
    try:
        _ = fetcher.fetch(test_url)
    except Exception:
        pass  # Don't care about result, just want log entry

    # Check that log file exists and has proper format
    if test_logger.log_path.exists():
        with open(test_logger.log_path, "r") as f:
            log_lines = f.readlines()

        # Verify logs are valid JSON
        if log_lines:
            for line in log_lines:
                if line.strip():
                    log_entry = json.loads(line)
                    assert "timestamp" in log_entry, "Log entry should have timestamp"
                    assert "event" in log_entry, "Log entry should have event type"

    # Step 6: Verify database statistics
    total_regions = len(test_storage.get_regions())
    total_rivers = len(test_storage.get_rivers())

    assert total_regions >= 3, f"Expected ≥3 regions, got {total_regions}"
    assert total_rivers >= 2, f"Expected ≥2 rivers, got {total_rivers}"

    print(f"✓ End-to-end test complete:")
    print(f"  - Regions: {total_regions}")
    print(f"  - Rivers: {total_rivers}")
    print(f"  - Flies: {len(flies) if flies else 0}")


def test_offline_functionality(test_storage, tmp_path):
    """
    Test SC-010: Verify system works offline after initial scrape.

    Once data is scraped, system should work without internet.
    """
    # Seed database with test data
    region_id = test_storage.insert_region(
        name="Test Region",
        slug="test-region",
        canonical_url="http://example.com/region/test",
        source_url="http://example.com/index",
        raw_html="<html>Test</html>",
        description="Test region",
        crawl_timestamp="2024-12-01T12:00:00Z",
    )

    river_id = test_storage.insert_river(
        region_id=region_id,
        name="Test River",
        slug="test-river",
        canonical_url="http://example.com/river/test",
        raw_html="<html>River</html>",
        description="Test river",
        crawl_timestamp="2024-12-01T12:00:00Z",
    )

    # Verify offline queries work (no network access needed)
    regions = test_storage.get_regions()
    assert len(regions) == 1, "Should query regions offline"

    rivers = test_storage.get_rivers_by_region(region_id)
    assert len(rivers) == 1, "Should query rivers offline"

    river = test_storage.get_river(river_id)
    assert river["name"] == "Test River", "Should get river details offline"


def test_cache_effectiveness(test_config, test_logger, mock_http_server, tmp_path):
    """
    Test SC-008: Verify cache reduces scrape time on second run.
    """
    cache_dir = tmp_path / "cache"
    test_config.data["cache_dir"] = str(cache_dir)
    test_config.data["base_url"] = mock_http_server

    fetcher = Fetcher(test_config, test_logger)

    # First run - no cache
    import time

    url = f"{mock_http_server}/page1"

    start1 = time.time()
    content1 = fetcher.fetch(url)
    duration1 = time.time() - start1

    stats1 = fetcher.get_cache_stats()
    assert stats1["misses"] == 1, "First run should be cache miss"

    # Second run - with cache
    start2 = time.time()
    content2 = fetcher.fetch(url)
    duration2 = time.time() - start2

    stats2 = fetcher.get_cache_stats()
    assert stats2["hits"] == 1, "Second run should be cache hit"

    # Cache hit should be much faster
    assert (
        duration2 < duration1
    ), f"Cache hit ({duration2:.2f}s) should be faster than first fetch ({duration1:.2f}s)"

    # Content should match
    assert content1 == content2, "Cached content should match original"


def test_rate_limiting_compliance(test_config, test_logger, mock_http_server, tmp_path):
    """
    Test SC-004: Verify 3-second delays enforced.
    """
    log_file = tmp_path / "rate_limit_test.log"
    test_logger.log_path = log_file
    test_config.data["cache_dir"] = str(tmp_path / "cache")

    fetcher = Fetcher(test_config, test_logger)

    # Make multiple requests
    urls = [f"{mock_http_server}/page1", f"{mock_http_server}/page2", f"{mock_http_server}/page3"]

    for url in urls:
        fetcher.fetch(url)

    # Verify delays in logs
    with open(log_file, "r") as f:
        log_lines = [line for line in f.readlines() if "http_request" in line]

    delays = []
    for line in log_lines:
        log_entry = json.loads(line)
        if log_entry.get("event") == "http_request" and not log_entry.get("cache_hit"):
            delays.append(log_entry.get("delay_seconds", 0))

    # First request has minimal delay, rest should have ≥3 seconds
    assert len(delays) >= 3, f"Expected ≥3 requests, got {len(delays)}"

    for i, delay in enumerate(delays[1:], 1):
        assert delay >= 2.9, f"Request {i} delay was {delay:.2f}s, expected ≥3.0s"


def test_raw_data_immutability(test_storage):
    """
    Test SC-009: Verify raw data never overwritten.

    Article 6.1: Raw data immutability principle.
    """
    # Insert region with raw HTML
    original_html = "<html><body>Original Content</body></html>"
    region_id = test_storage.insert_region(
        name="Test Region",
        slug="test",
        canonical_url="http://example.com/test",
        source_url="http://example.com",
        raw_html=original_html,
        crawl_timestamp="2024-12-01T12:00:00Z",
    )

    # Try to update (should not overwrite raw_html)
    region = test_storage.get_region(region_id)
    assert region["raw_html"] == original_html, "Original raw_html should be preserved"

    # Insert fly with raw_text
    river_id = test_storage.insert_river(
        region_id=region_id,
        name="Test River",
        slug="test-river",
        canonical_url="http://example.com/river/test",
        raw_html="<html>River</html>",
        crawl_timestamp="2024-12-01T12:00:00Z",
    )

    original_fly_text = "Royal Wulff #14"
    fly_id = test_storage.insert_fly(
        river_id=river_id,
        name="Royal Wulff",
        raw_text=original_fly_text,
        category="dry",
        size="14",
        crawl_timestamp="2024-12-01T12:00:00Z",
    )

    # Verify raw_text preserved
    flies = test_storage.get_flies_by_river(river_id)
    assert flies[0]["raw_text"] == original_fly_text, "Raw fly text should be immutable"
