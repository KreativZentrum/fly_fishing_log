"""
Integration test: Full river discovery workflow.
Tests US2: Discover and Scrape Rivers for a Region
Success Criteria SC-002: All rivers in region's "Fishing Waters" discoverable
"""

import pytest
from src.config import Config
from src.logger import ScraperLogger
from src.storage import Storage
from src.fetcher import Fetcher
from src.parser import Parser
from tests.fixtures.sample_pages import SAMPLE_REGION_HTML, MULTIPLE_RIVERS


def test_river_discovery_full_workflow(test_config, test_logger, test_storage):
    """
    Integration test: Full river discovery workflow for one region.

    1. Insert test region
    2. Fetch region page (with rate limiting)
    3. Parse rivers from "Fishing Waters" section
    4. Store all rivers with region FK
    5. Verify all rivers discoverable by query

    Success Criteria SC-002: All rivers from region page stored.
    """
    fetcher = Fetcher(test_config, test_logger)
    parser = Parser(test_config)

    try:
        # Insert test region first
        region_id = test_storage.insert_region(
            {
                "name": "North Island",
                "slug": "north-island",
                "canonical_url": "http://localhost:8000/region/north-island",
                "source_url": "http://localhost:8000/index.html",
                "raw_html": "<html>index</html>",
                "description": "Test region",
                "crawl_timestamp": "2024-01-15T12:00:00Z",
            }
        )

        # Mock: Use sample HTML instead of live fetch
        html = MULTIPLE_RIVERS

        # Get region for context
        region = test_storage.get_region(region_id)

        # Parse rivers from region page
        rivers = parser.parse_region_page(html, region)

        # Should find 4 rivers in MULTIPLE_RIVERS sample
        assert len(rivers) == 4, f"Expected 4 rivers, got {len(rivers)}"

        # Verify structure of parsed rivers
        for river in rivers:
            assert "name" in river, "River missing 'name' field"
            assert "canonical_url" in river, "River missing 'canonical_url' field"
            assert "slug" in river, "River missing 'slug' field"

        # Store rivers in database
        for river in rivers:
            test_storage.insert_river(
                {
                    "region_id": region_id,
                    "name": river["name"],
                    "slug": river["slug"],
                    "canonical_url": river["canonical_url"],
                    "raw_html": html,  # In real workflow, would be river detail page HTML
                    "crawl_timestamp": "2024-01-15T12:00:00Z",
                }
            )

        # Verify all rivers stored
        stored_rivers = test_storage.get_rivers_by_region(region_id)
        assert len(stored_rivers) == 4, f"Expected 4 stored rivers, got {len(stored_rivers)}"

        # Verify river names match
        stored_names = {r["name"] for r in stored_rivers}
        expected_names = {r["name"] for r in rivers}
        assert (
            stored_names == expected_names
        ), f"Stored names {stored_names} != expected {expected_names}"

        # Verify all have correct region FK
        for river in stored_rivers:
            assert river["region_id"] == region_id, f"River {river['name']} has wrong region_id"

    finally:
        fetcher.close()


def test_river_discovery_duplicate_handling(test_config, test_logger, test_storage):
    """
    Test that re-discovering existing river updates timestamp, not duplicates.

    Article 6.4: Raw data immutability (but metadata can update).
    """
    parser = Parser(test_config)

    # Insert region
    region_id = test_storage.insert_region(
        {
            "name": "Empty Region",
            "slug": "empty-region",
            "canonical_url": "http://example.com/region/empty",
            "source_url": "http://example.com/index",
            "raw_html": "<html>region</html>",
            "description": "",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    region = test_storage.get_region(region_id)

    html = """
    <html><body>
        <div class="river-list">
            <a href="/river/test-river">Test River</a>
        </div>
    </body></html>
    """

    # First discovery
    rivers = parser.parse_region_page(html, region)
    assert len(rivers) == 1

    river = rivers[0]
    river_id_1 = test_storage.insert_river(
        {
            "region_id": region_id,
            "name": river["name"],
            "slug": river["slug"],
            "canonical_url": river["canonical_url"],
            "raw_html": html,
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Second discovery (same river, new timestamp)
    river_id_2 = test_storage.insert_river(
        {
            "region_id": region_id,
            "name": river["name"],
            "slug": river["slug"],
            "canonical_url": river["canonical_url"],
            "raw_html": html,
            "crawl_timestamp": "2024-01-15T13:00:00Z",  # Different timestamp
        }
    )

    # Should return same ID (upsert)
    assert river_id_1 == river_id_2, f"Duplicate river created: {river_id_1} != {river_id_2}"

    # Verify only 1 river in database for this region
    rivers_in_region = test_storage.get_rivers_by_region(region_id)
    assert len(rivers_in_region) == 1, f"Expected 1 river, got {len(rivers_in_region)}"


def test_river_discovery_empty_fishing_waters(test_config, test_logger, test_storage):
    """
    Test graceful handling of region page with no rivers.

    Edge Case: Missing "Fishing Waters" section.
    Article 4.4: Graceful handling of missing sections.
    """
    parser = Parser(test_config)

    # Insert region
    region_id = test_storage.insert_region(
        {
            "name": "Empty Region",
            "slug": "empty-region",
            "canonical_url": "http://example.com/region/empty",
            "source_url": "http://example.com/index",
            "raw_html": "<html>region</html>",
            "description": "",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    region = test_storage.get_region(region_id)

    from tests.fixtures.sample_pages import NO_MATCHES

    html = NO_MATCHES

    # Parse empty region page
    rivers = parser.parse_region_page(html, region)

    # Should return empty list, not raise exception
    assert rivers == [], f"Expected empty list for no-match HTML, got {rivers}"


def test_river_discovery_with_sections(test_config, test_logger, test_storage):
    """
    Test parsing rivers that have multiple sections (Upper/Middle/Lower).

    Edge Case: Rivers with section annotations.
    """
    parser = Parser(test_config)

    # Insert region
    region_id = test_storage.insert_region(
        {
            "name": "Test Region",
            "slug": "test-region",
            "canonical_url": "http://example.com/region/test",
            "source_url": "http://example.com/index",
            "raw_html": "<html>region</html>",
            "description": "",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    region = test_storage.get_region(region_id)

    # HTML with river sections mentioned
    html = """
    <html><body>
        <div class="river-list">
            <a href="/river/tongariro">Tongariro River</a>
            <a href="/river/tongariro-upper">Tongariro River (Upper)</a>
            <a href="/river/tongariro-lower">Tongariro River (Lower)</a>
        </div>
    </body></html>
    """

    rivers = parser.parse_region_page(html, region)

    # Should parse all 3 links as separate river entries
    # (Sections will be parsed from detail pages in US3)
    assert len(rivers) == 3

    # Store all rivers
    for river in rivers:
        test_storage.insert_river(
            {
                "region_id": region_id,
                "name": river["name"],
                "slug": river["slug"],
                "canonical_url": river["canonical_url"],
                "raw_html": html,
                "crawl_timestamp": "2024-01-15T12:00:00Z",
            }
        )

    # Verify all stored
    stored_rivers = test_storage.get_rivers_by_region(region_id)
    assert len(stored_rivers) == 3


def test_river_discovery_cascade_delete(test_config, test_logger, test_storage):
    """
    Test that deleting region cascades to rivers.

    Database integrity: ON DELETE CASCADE.
    """
    # Insert region
    region_id = test_storage.insert_region(
        {
            "name": "Test Region",
            "slug": "test-region",
            "canonical_url": "http://example.com/region/test",
            "source_url": "http://example.com/index",
            "raw_html": "<html>region</html>",
            "description": "",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Insert rivers
    river_id_1 = test_storage.insert_river(
        {
            "region_id": region_id,
            "name": "River 1",
            "slug": "river-1",
            "canonical_url": "http://example.com/river/1",
            "raw_html": "<html>river1</html>",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    river_id_2 = test_storage.insert_river(
        {
            "region_id": region_id,
            "name": "River 2",
            "slug": "river-2",
            "canonical_url": "http://example.com/river/2",
            "raw_html": "<html>river2</html>",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Verify rivers exist
    assert test_storage.get_river(river_id_1) is not None
    assert test_storage.get_river(river_id_2) is not None

    # Delete region (should cascade to rivers)
    import sqlite3

    conn = sqlite3.connect(test_config.database_path)
    conn.execute("DELETE FROM regions WHERE id = ?", (region_id,))
    conn.commit()
    conn.close()

    # Verify rivers deleted
    assert test_storage.get_river(river_id_1) is None
    assert test_storage.get_river(river_id_2) is None


def test_river_discovery_with_logging(test_config, test_logger, test_storage):
    """
    Verify river discovery logs all actions.

    Article 9.3: Complete logging of discovery events.
    """
    parser = Parser(test_config)

    # Insert region
    region_id = test_storage.insert_region(
        {
            "name": "Test Region",
            "slug": "test-region",
            "canonical_url": "http://example.com/region/test",
            "source_url": "http://example.com/index",
            "raw_html": "<html>region</html>",
            "description": "",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    region = test_storage.get_region(region_id)
    html = MULTIPLE_RIVERS

    rivers = parser.parse_region_page(html, region)

    # Store rivers and log each
    for river in rivers:
        test_storage.insert_river(
            {
                "region_id": region_id,
                "name": river["name"],
                "slug": river["slug"],
                "canonical_url": river["canonical_url"],
                "raw_html": html,
                "crawl_timestamp": "2024-01-15T12:00:00Z",
            }
        )

        # Log discovery event
        test_logger.log_discovery(entity_type="river", entity_name=river["name"], action="INSERT")

    # Read log file
    import json

    with open(test_config.log_path, "r") as f:
        log_lines = f.readlines()

    # Find discovery events
    discovery_logs = [
        json.loads(line)
        for line in log_lines
        if '"event": "discovery"' in line and '"entity_type": "river"' in line
    ]

    # Should have 4 discovery events (one per river)
    assert len(discovery_logs) == 4, f"Expected 4 discovery logs, got {len(discovery_logs)}"

    # Verify log structure
    for log in discovery_logs:
        assert log["entity_type"] == "river"
        assert log["action"] == "INSERT"
        assert "entity_name" in log
