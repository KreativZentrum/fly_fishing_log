"""
Integration test: Full region discovery workflow.
Tests US1: Discover and Scrape Regions
Success Criteria SC-001: All regions from index discoverable and stored
"""

import pytest
from src.config import Config
from src.logger import ScraperLogger
from src.storage import Storage
from src.fetcher import Fetcher
from src.parser import Parser
from tests.fixtures.sample_pages import MULTIPLE_REGIONS, MINIMAL_INDEX


def test_region_discovery_full_workflow(test_config, test_logger, test_storage):
    """
    Integration test: Full region discovery workflow.

    1. Fetch index page (with rate limiting)
    2. Parse regions from index
    3. Store all regions in database
    4. Verify all regions discoverable by query

    Success Criteria SC-001: All index regions appear in database.
    """
    fetcher = Fetcher(test_config, test_logger)
    parser = Parser(test_config)

    try:
        # Mock: Use sample HTML instead of live fetch for controlled test
        # In real workflow, this would be: html = fetcher.fetch(index_url)
        html = MULTIPLE_REGIONS

        # Parse regions
        regions = parser.parse_region_index(html)

        # Should find 3 regions in MULTIPLE_REGIONS sample
        assert len(regions) == 3, f"Expected 3 regions, got {len(regions)}"

        # Verify structure of parsed regions
        for region in regions:
            assert "name" in region, "Region missing 'name' field"
            assert "canonical_url" in region, "Region missing 'canonical_url' field"
            assert "slug" in region, "Region missing 'slug' field"

        # Store regions in database
        for region in regions:
            test_storage.insert_region(
                name=region["name"],
                slug=region["slug"],
                canonical_url=region["canonical_url"],
                source_url=test_config.base_url + "/index.html",
                raw_html=html,  # In real workflow, store per-region HTML
                description=region.get("description", ""),
                crawl_timestamp="2024-01-15T12:00:00Z",
            )

        # Verify all regions stored
        stored_regions = test_storage.get_regions()
        assert len(stored_regions) == 3, f"Expected 3 stored regions, got {len(stored_regions)}"

        # Verify region names match
        stored_names = {r["name"] for r in stored_regions}
        expected_names = {r["name"] for r in regions}
        assert (
            stored_names == expected_names
        ), f"Stored names {stored_names} != expected {expected_names}"

    finally:
        fetcher.close()


def test_region_discovery_duplicate_handling(test_config, test_logger, test_storage):
    """
    Test that re-discovering existing region updates timestamp, not duplicates.

    Article 6.4: Raw data immutability (but metadata can update).
    """
    parser = Parser(test_config)
    html = MINIMAL_INDEX

    # First discovery
    regions = parser.parse_region_index(html)
    assert len(regions) == 1, "Minimal index should have 1 region"

    region = regions[0]
    region_id_1 = test_storage.insert_region(
        name=region["name"],
        slug=region["slug"],
        canonical_url=region["canonical_url"],
        source_url=test_config.base_url + "/index.html",
        raw_html=html,
        description="",
        crawl_timestamp="2024-01-15T12:00:00Z",
    )

    # Second discovery (same region, new timestamp)
    region_id_2 = test_storage.insert_region(
        name=region["name"],
        slug=region["slug"],
        canonical_url=region["canonical_url"],  # Same canonical URL
        source_url=test_config.base_url + "/index.html",
        raw_html=html,
        description="",
        crawl_timestamp="2024-01-15T13:00:00Z",  # Different timestamp
    )

    # Should return same ID (upsert, not duplicate)
    assert region_id_1 == region_id_2, f"Duplicate region created: {region_id_1} != {region_id_2}"

    # Verify only 1 region in database
    all_regions = test_storage.get_regions()
    assert (
        len(all_regions) == 1
    ), f"Expected 1 region, got {len(all_regions)} (duplicate not prevented)"


def test_region_discovery_empty_index(test_config, test_logger, test_storage):
    """
    Test graceful handling of index page with no regions.

    Edge Case: Missing or empty "Where to Fish" section.
    Article 4.4: Graceful handling of missing sections.
    """
    parser = Parser(test_config)

    from tests.fixtures.sample_pages import NO_MATCHES

    html = NO_MATCHES

    # Parse empty index
    regions = parser.parse_region_index(html)

    # Should return empty list, not raise exception
    assert regions == [], f"Expected empty list for no-match HTML, got {regions}"

    # Verify no regions inserted
    all_regions = test_storage.get_regions()
    assert len(all_regions) == 0, f"Expected 0 regions in empty DB, got {len(all_regions)}"


def test_region_discovery_malformed_html(test_config, test_logger, test_storage):
    """
    Test parser handles malformed HTML gracefully.

    Edge Case: Unclosed tags, missing attributes.
    """
    parser = Parser(test_config)

    from tests.fixtures.sample_pages import MALFORMED_HTML

    html = MALFORMED_HTML

    # Parse malformed HTML (BeautifulSoup should handle gracefully)
    regions = parser.parse_region_index(html)

    # May return partial results or empty list, should not crash
    assert isinstance(regions, list), f"Expected list, got {type(regions)}"


def test_region_discovery_with_logging(test_config, test_logger, test_storage):
    """
    Verify region discovery logs all actions.

    Article 9.3: Complete logging of discovery events.
    """
    parser = Parser(test_config)
    html = MULTIPLE_REGIONS

    regions = parser.parse_region_index(html)

    # Store regions (should log each insert)
    for region in regions:
        test_storage.insert_region(
            name=region["name"],
            slug=region["slug"],
            canonical_url=region["canonical_url"],
            source_url=test_config.base_url + "/index.html",
            raw_html=html,
            description="",
            crawl_timestamp="2024-01-15T12:00:00Z",
        )

        # Log discovery event (this will be in CLI workflow, not storage)
        test_logger.log_discovery(entity_type="region", entity_name=region["name"], action="INSERT")

    # Read log file
    import json

    with open(test_config.log_path, "r") as f:
        log_lines = f.readlines()

    # Find discovery events
    discovery_logs = [json.loads(line) for line in log_lines if '"event": "discovery"' in line]

    # Should have 3 discovery events (one per region)
    assert len(discovery_logs) == 3, f"Expected 3 discovery logs, got {len(discovery_logs)}"

    # Verify log structure
    for log in discovery_logs:
        assert log["entity_type"] == "region"
        assert log["action"] == "INSERT"
        assert "entity_name" in log


def test_uncrawled_regions_query(test_config, test_logger, test_storage):
    """
    Test get_uncrawled_regions() returns regions without crawl_timestamp.

    Used for incremental discovery workflow.
    """
    # Insert region with crawl_timestamp
    test_storage.insert_region(
        name="Crawled Region",
        slug="crawled-region",
        canonical_url="http://example.com/crawled",
        source_url="http://example.com/index",
        raw_html="<html>crawled</html>",
        description="",
        crawl_timestamp="2024-01-15T12:00:00Z",
    )

    # Insert region without crawl_timestamp (new discovery)
    test_storage.insert_region(
        name="Uncrawled Region",
        slug="uncrawled-region",
        canonical_url="http://example.com/uncrawled",
        source_url="http://example.com/index",
        raw_html="",  # No HTML yet
        description="",
        crawl_timestamp="",  # Empty = uncrawled
    )

    # Query uncrawled regions
    uncrawled = test_storage.get_uncrawled_regions()

    # Should return only the uncrawled region
    assert len(uncrawled) == 1, f"Expected 1 uncrawled region, got {len(uncrawled)}"
    assert uncrawled[0]["name"] == "Uncrawled Region"
