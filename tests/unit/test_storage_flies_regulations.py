"""
Unit test: Storage layer flies and regulations CRUD operations.
Tests fly and regulation insert, get, FK validation, and raw data immutability.
"""

import pytest
from src.storage import Storage


def test_insert_fly(test_storage, sample_region_data):
    """
    Test basic fly insertion with river FK.
    """
    # Insert region and river first
    region_id = test_storage.insert_region(sample_region_data)
    river_id = test_storage.insert_river(
        {
            "region_id": region_id,
            "name": "Test River",
            "slug": "test-river",
            "canonical_url": "http://example.com/river/test",
            "raw_html": "",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Insert fly
    fly_id = test_storage.insert_fly(
        {
            "river_id": river_id,
            "name": "Pheasant Tail Nymph",
            "raw_text": "Pheasant Tail Nymph #16 Brown",
            "category": "nymph",
            "size": "16",
            "color": "brown",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    assert fly_id is not None
    assert fly_id > 0


def test_get_flies_by_river(test_storage, sample_region_data):
    """
    Test retrieving flies by river ID.
    """
    # Insert region and river
    region_id = test_storage.insert_region(sample_region_data)
    river_id = test_storage.insert_river(
        {
            "region_id": region_id,
            "name": "Test River",
            "slug": "test",
            "canonical_url": "http://example.com/river/test",
            "raw_html": "",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Insert multiple flies
    test_storage.insert_fly(
        {
            "river_id": river_id,
            "name": "Fly 1",
            "raw_text": "Fly 1 description",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    test_storage.insert_fly(
        {
            "river_id": river_id,
            "name": "Fly 2",
            "raw_text": "Fly 2 description",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Retrieve flies
    flies = test_storage.get_flies_by_river(river_id)

    assert len(flies) == 2
    names = {f["name"] for f in flies}
    assert names == {"Fly 1", "Fly 2"}


def test_insert_fly_with_null_fields(test_storage, sample_region_data):
    """
    Test that uncertain fly fields can be null (no inference).

    Article 5.2: No inference.
    """
    # Insert region and river
    region_id = test_storage.insert_region(sample_region_data)
    river_id = test_storage.insert_river(
        {
            "region_id": region_id,
            "name": "Test River",
            "slug": "test",
            "canonical_url": "http://example.com/river/test",
            "raw_html": "",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Insert fly with null category/size/color
    fly_id = test_storage.insert_fly(
        {
            "river_id": river_id,
            "name": "Mystery Fly",
            "raw_text": "Some fly description",
            "category": None,
            "size": None,
            "color": None,
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Retrieve and verify nulls preserved
    flies = test_storage.get_flies_by_river(river_id)
    fly = flies[0]

    assert fly["category"] is None
    assert fly["size"] is None
    assert fly["color"] is None


def test_insert_regulation(test_storage, sample_region_data):
    """
    Test basic regulation insertion with river FK.
    """
    # Insert region and river
    region_id = test_storage.insert_region(sample_region_data)
    river_id = test_storage.insert_river(
        {
            "region_id": region_id,
            "name": "Test River",
            "slug": "test",
            "canonical_url": "http://example.com/river/test",
            "raw_html": "",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Insert regulation
    reg_id = test_storage.insert_regulation(
        {
            "river_id": river_id,
            "type": "catch_limit",
            "value": "2 fish per day",
            "raw_text": "Catch limit: 2 fish per day",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    assert reg_id is not None
    assert reg_id > 0


def test_get_regulations_by_river(test_storage, sample_region_data):
    """
    Test retrieving regulations by river ID.
    """
    # Insert region and river
    region_id = test_storage.insert_region(sample_region_data)
    river_id = test_storage.insert_river(
        {
            "region_id": region_id,
            "name": "Test River",
            "slug": "test",
            "canonical_url": "http://example.com/river/test",
            "raw_html": "",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Insert multiple regulations
    test_storage.insert_regulation(
        {
            "river_id": river_id,
            "type": "catch_limit",
            "value": "2 fish",
            "raw_text": "Catch limit: 2 fish per day",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    test_storage.insert_regulation(
        {
            "river_id": river_id,
            "type": "season_dates",
            "value": "October 1 - April 30",
            "raw_text": "Season: October 1 - April 30",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Retrieve regulations
    regs = test_storage.get_regulations_by_river(river_id)

    assert len(regs) == 2
    types = {r["type"] for r in regs}
    assert types == {"catch_limit", "season_dates"}


def test_fly_cascade_delete_on_river_delete(test_storage, sample_region_data):
    """
    Test that deleting river cascades to flies.

    ON DELETE CASCADE enforcement.
    """
    # Insert region and river
    region_id = test_storage.insert_region(sample_region_data)
    river_id = test_storage.insert_river(
        {
            "region_id": region_id,
            "name": "Test River",
            "slug": "test",
            "canonical_url": "http://example.com/river/test",
            "raw_html": "",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Insert fly
    fly_id = test_storage.insert_fly(
        {
            "river_id": river_id,
            "name": "Test Fly",
            "raw_text": "Test fly description",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Verify fly exists
    flies_before = test_storage.get_flies_by_river(river_id)
    assert len(flies_before) == 1

    # Delete river using the same connection
    cursor = test_storage.conn.execute("DELETE FROM rivers WHERE id = ?", (river_id,))
    test_storage.conn.commit()

    # Verify flies deleted (CASCADE)
    flies_after = test_storage.get_flies_by_river(river_id)
    assert len(flies_after) == 0


def test_regulation_cascade_delete_on_river_delete(test_storage, sample_region_data):
    """
    Test that deleting river cascades to regulations.
    """
    # Insert region and river
    region_id = test_storage.insert_region(sample_region_data)
    river_id = test_storage.insert_river(
        {
            "region_id": region_id,
            "name": "Test River",
            "slug": "test",
            "canonical_url": "http://example.com/river/test",
            "raw_html": "",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Insert regulation
    reg_id = test_storage.insert_regulation(
        {
            "river_id": river_id,
            "type": "catch_limit",
            "value": "2 fish",
            "raw_text": "Catch limit: 2 fish per day",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Verify regulation exists
    regs_before = test_storage.get_regulations_by_river(river_id)
    assert len(regs_before) == 1

    # Delete river using the same connection
    cursor = test_storage.conn.execute("DELETE FROM rivers WHERE id = ?", (river_id,))
    test_storage.conn.commit()

    # Verify regulations deleted (CASCADE)
    regs_after = test_storage.get_regulations_by_river(river_id)
    assert len(regs_after) == 0


def test_insert_metadata(test_storage, sample_region_data):
    """
    Test metadata insertion for change detection.

    Article 6.2: Metadata versioning.
    """
    # Insert region and river
    region_id = test_storage.insert_region(sample_region_data)
    river_id = test_storage.insert_river(
        {
            "region_id": region_id,
            "name": "Test River",
            "slug": "test",
            "canonical_url": "http://example.com/river/test",
            "raw_html": "",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Insert metadata
    metadata_id = test_storage.insert_metadata(
        {
            "session_id": "test-session-001",
            "entity_id": river_id,
            "entity_type": "river",
            "raw_content_hash": "abc123",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    assert metadata_id is not None


def test_get_metadata_by_entity(test_storage, sample_region_data):
    """
    Test retrieving metadata by entity.
    """
    # Insert region and river
    region_id = test_storage.insert_region(sample_region_data)
    river_id = test_storage.insert_river(
        {
            "region_id": region_id,
            "name": "Test River",
            "slug": "test",
            "canonical_url": "http://example.com/river/test",
            "raw_html": "",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Insert metadata
    test_storage.insert_metadata(
        {
            "session_id": "test-session-001",
            "entity_id": river_id,
            "entity_type": "river",
            "raw_content_hash": "abc123",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Retrieve metadata
    metadata = test_storage.get_metadata_by_entity("river", river_id)

    assert metadata is not None
    assert metadata["raw_content_hash"] == "abc123"


def test_fly_raw_text_immutability(test_storage, sample_region_data):
    """
    Test that raw_text is preserved (immutability).

    Article 6.1: Raw data immutability.
    """
    # Insert region and river
    region_id = test_storage.insert_region(sample_region_data)
    river_id = test_storage.insert_river(
        {
            "region_id": region_id,
            "name": "Test River",
            "slug": "test",
            "canonical_url": "http://example.com/river/test",
            "raw_html": "",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Insert fly with raw_text
    original_raw = "Pheasant Tail Nymph #16 Brown"
    fly_id = test_storage.insert_fly(
        {
            "river_id": river_id,
            "name": "Pheasant Tail Nymph",
            "raw_text": original_raw,
            "category": "nymph",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Retrieve and verify raw_text unchanged
    flies = test_storage.get_flies_by_river(river_id)
    assert flies[0]["raw_text"] == original_raw
