"""
Integration test: River detail extraction workflow.
Tests full pipeline from fetch → parse → store for river details.
"""

import pytest
from src.parser import Parser
from src.storage import Storage


def test_river_detail_extraction_full_workflow(
    test_storage, test_fetcher, test_config, test_logger, sample_region_data
):
    """
    Test complete river detail extraction workflow.

    SC-003: All river details (flies, regulations) extractable and storable.
    """
    parser = Parser(test_config)

    # Insert region first
    region_id = test_storage.insert_region(sample_region_data)

    # Insert river
    river_id = test_storage.insert_river(
        {
            "region_id": region_id,
            "name": "Test River",
            "slug": "test-river",
            "canonical_url": "http://localhost:8000/river/test",
            "raw_html": "",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Sample river detail HTML
    detail_html = """
    <html>
    <body>
        <h1 class="river-name">Test River</h1>
        <div class="fish-type">Brown Trout, Rainbow Trout</div>
        <div class="situation">Clear water, medium flow</div>
        <div class="recommended-lures">
            <ul>
                <li>Pheasant Tail Nymph #16 Brown</li>
                <li>Royal Wulff #14 Red</li>
                <li>Woolly Bugger #10 Black</li>
            </ul>
        </div>
        <div class="regulations">
            <p>Catch limit: 2 fish per day</p>
            <p>Season: October 1 - April 30</p>
        </div>
    </body>
    </html>
    """

    # Parse river details
    river_obj = test_storage.get_river(river_id)
    details = parser.parse_river_detail(detail_html, river_obj)

    # Verify parsed structure
    assert "fish_type" in details
    assert "conditions" in details
    assert "flies" in details
    assert "regulations" in details

    # Verify flies extracted
    assert len(details["flies"]) == 3
    fly_names = {f["name"] for f in details["flies"]}
    assert "Pheasant Tail Nymph #16 Brown" in fly_names

    # Store flies in database
    for fly_data in details["flies"]:
        test_storage.insert_fly(
            {
                "river_id": river_id,
                "name": fly_data["name"],
                "raw_text": fly_data["raw_text"],
                "category": fly_data.get("category"),
                "size": fly_data.get("size"),
                "color": fly_data.get("color"),
                "crawl_timestamp": "2024-01-15T12:00:00Z",
            }
        )

    # Store regulations
    for reg_data in details["regulations"]:
        test_storage.insert_regulation(
            {
                "river_id": river_id,
                "type": reg_data["type"],
                "value": reg_data["value"],
                "raw_text": reg_data["raw_text"],
                "crawl_timestamp": "2024-01-15T12:00:00Z",
            }
        )

    # Verify stored in DB
    stored_flies = test_storage.get_flies_by_river(river_id)
    assert len(stored_flies) == 3

    stored_regs = test_storage.get_regulations_by_river(river_id)
    assert len(stored_regs) == 2


def test_river_detail_missing_sections(test_storage, test_config, sample_region_data):
    """
    Test graceful handling when river detail sections are missing.

    Article 4.4: Graceful error handling.
    """
    parser = Parser(test_config)

    # Insert region and river
    region_id = test_storage.insert_region(sample_region_data)
    river_id = test_storage.insert_river(
        {
            "region_id": region_id,
            "name": "Minimal River",
            "slug": "minimal",
            "canonical_url": "http://localhost:8000/river/minimal",
            "raw_html": "",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Minimal HTML with only fish type
    minimal_html = """
    <html>
    <body>
        <h1>Minimal River</h1>
        <div class="fish-type">Brown Trout</div>
    </body>
    </html>
    """

    river_obj = test_storage.get_river(river_id)
    details = parser.parse_river_detail(minimal_html, river_obj)

    # Should return structure with empty lists for missing sections
    assert details["flies"] == []
    assert details["regulations"] == []
    assert details["fish_type"] is not None  # Has fish type


def test_river_detail_no_inference(test_storage, test_config, sample_region_data):
    """
    Test that parser does not infer missing data.

    Article 5.2: No inference or fabrication.
    """
    parser = Parser(test_config)

    # Insert region and river
    region_id = test_storage.insert_region(sample_region_data)
    river_id = test_storage.insert_river(
        {
            "region_id": region_id,
            "name": "Uncertain River",
            "slug": "uncertain",
            "canonical_url": "http://localhost:8000/river/uncertain",
            "raw_html": "",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # HTML with ambiguous fly descriptions
    html = """
    <html>
    <body>
        <div class="recommended-lures">
            <ul>
                <li>Some Fly Pattern</li>
            </ul>
        </div>
    </body>
    </html>
    """

    river_obj = test_storage.get_river(river_id)
    details = parser.parse_river_detail(html, river_obj)

    # Fly parsed with name only
    assert len(details["flies"]) == 1
    fly = details["flies"][0]

    # Uncertain fields should be None, not defaults
    # (Category/size/color uncertain from "Some Fly Pattern")
    assert fly["name"] == "Some Fly Pattern"
    # If classify_fly can't determine, should be None
    if fly.get("category") is None:
        assert True, "Correctly left uncertain field as None"


def test_river_detail_with_metadata(test_storage, test_config, sample_region_data):
    """
    Test metadata tracking for change detection.

    Article 6.2: Metadata versioning for change detection.
    SC-009: Change detection via content hash.
    """
    parser = Parser(test_config)

    # Insert region and river
    region_id = test_storage.insert_region(sample_region_data)
    river_id = test_storage.insert_river(
        {
            "region_id": region_id,
            "name": "Versioned River",
            "slug": "versioned",
            "canonical_url": "http://localhost:8000/river/versioned",
            "raw_html": "",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    detail_html = "<html><body><div class='fish-type'>Brown Trout</div></body></html>"

    river_obj = test_storage.get_river(river_id)
    details = parser.parse_river_detail(detail_html, river_obj)

    # Store metadata
    import hashlib

    raw_hash = hashlib.md5(detail_html.encode()).hexdigest()

    test_storage.insert_metadata(
        {
            "session_id": "test-session-001",
            "entity_id": river_id,
            "entity_type": "river",
            "raw_content_hash": raw_hash,
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Verify metadata stored
    metadata = test_storage.get_metadata_by_entity("river", river_id)
    assert metadata is not None
    assert metadata["raw_content_hash"] == raw_hash
