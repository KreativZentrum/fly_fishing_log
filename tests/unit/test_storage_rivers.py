"""
Unit test: Storage layer river CRUD operations.
Tests River insert, get, update, FK validation, and cascade delete.
"""

import pytest
from src.storage import Storage
from src.exceptions import StorageError


def test_insert_river(test_storage, sample_region_data):
    """
    Test basic river insertion with valid region FK.
    """
    # Insert region first
    region_id = test_storage.insert_region(sample_region_data)

    # Insert river
    river_id = test_storage.insert_river(
        {
            "region_id": region_id,
            "name": "Test River",
            "slug": "test-river",
            "canonical_url": "http://example.com/river/test",
            "raw_html": "<html>river</html>",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    assert river_id is not None
    assert river_id > 0


def test_get_river(test_storage, sample_region_data):
    """
    Test retrieving river by ID.
    """
    # Insert region and river
    region_id = test_storage.insert_region(sample_region_data)

    river_id = test_storage.insert_river(
        {
            "region_id": region_id,
            "name": "Test River",
            "slug": "test-river",
            "canonical_url": "http://example.com/river/test",
            "raw_html": "<html>river</html>",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Retrieve river
    river = test_storage.get_river(river_id)

    assert river is not None
    assert river["id"] == river_id
    assert river["region_id"] == region_id
    assert river["name"] == "Test River"
    assert river["slug"] == "test-river"
    assert river["canonical_url"] == "http://example.com/river/test"


def test_get_river_not_found(test_storage):
    """
    Test retrieving non-existent river returns None.
    """
    river = test_storage.get_river(9999)
    assert river is None


def test_get_rivers(test_storage, sample_region_data):
    """
    Test retrieving all rivers.
    """
    # Insert region
    region_id = test_storage.insert_region(sample_region_data)

    # Insert multiple rivers
    test_storage.insert_river(
        {
            "region_id": region_id,
            "name": "River 1",
            "slug": "river-1",
            "canonical_url": "http://example.com/river/1",
            "raw_html": "<html>1</html>",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    test_storage.insert_river(
        {
            "region_id": region_id,
            "name": "River 2",
            "slug": "river-2",
            "canonical_url": "http://example.com/river/2",
            "raw_html": "<html>2</html>",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Retrieve all
    rivers = test_storage.get_rivers()

    assert len(rivers) == 2
    names = {r["name"] for r in rivers}
    assert names == {"River 1", "River 2"}


def test_get_rivers_by_region(test_storage, sample_region_data):
    """
    Test retrieving rivers for specific region.
    """
    # Insert two regions
    region_id_1 = test_storage.insert_region(sample_region_data)

    region_data_2 = sample_region_data.copy()
    region_data_2["name"] = "Region 2"
    region_data_2["slug"] = "region-2"
    region_data_2["canonical_url"] = "http://example.com/region/2"
    region_id_2 = test_storage.insert_region(region_data_2)

    # Insert rivers in region 1
    test_storage.insert_river(
        {
            "region_id": region_id_1,
            "name": "River 1A",
            "slug": "river-1a",
            "canonical_url": "http://example.com/river/1a",
            "raw_html": "<html>1a</html>",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    test_storage.insert_river(
        {
            "region_id": region_id_1,
            "name": "River 1B",
            "slug": "river-1b",
            "canonical_url": "http://example.com/river/1b",
            "raw_html": "<html>1b</html>",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Insert river in region 2
    test_storage.insert_river(
        {
            "region_id": region_id_2,
            "name": "River 2A",
            "slug": "river-2a",
            "canonical_url": "http://example.com/river/2a",
            "raw_html": "<html>2a</html>",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Query rivers by region
    rivers_region_1 = test_storage.get_rivers_by_region(region_id_1)
    rivers_region_2 = test_storage.get_rivers_by_region(region_id_2)

    assert len(rivers_region_1) == 2
    assert len(rivers_region_2) == 1

    names_1 = {r["name"] for r in rivers_region_1}
    assert names_1 == {"River 1A", "River 1B"}


def test_insert_river_duplicate_canonical_url(test_storage, sample_region_data):
    """
    Test that inserting river with duplicate canonical_url updates, not duplicates.

    Article 6.4: Upsert pattern for immutability.
    """
    # Insert region
    region_id = test_storage.insert_region(sample_region_data)

    # First insert
    river_id_1 = test_storage.insert_river(
        {
            "region_id": region_id,
            "name": "Original Name",
            "slug": "original-slug",
            "canonical_url": "http://example.com/river/test",
            "raw_html": "<html>original</html>",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Second insert with same canonical_url
    river_id_2 = test_storage.insert_river(
        {
            "region_id": region_id,
            "name": "Updated Name",
            "slug": "updated-slug",
            "canonical_url": "http://example.com/river/test",  # Same URL
            "raw_html": "<html>updated</html>",
            "crawl_timestamp": "2024-01-15T13:00:00Z",
        }
    )

    # Should return same ID (upsert)
    assert river_id_1 == river_id_2

    # Verify only 1 river exists
    rivers = test_storage.get_rivers()
    assert len(rivers) == 1

    # Verify updated fields
    river = rivers[0]
    assert river["name"] == "Updated Name"


def test_insert_river_invalid_region_fk(test_storage):
    """
    Test that inserting river with invalid region_id raises error.

    Foreign key constraint enforcement.
    """
    with pytest.raises(Exception):  # SQLite raises IntegrityError
        test_storage.insert_river(
            {
                "region_id": 9999,  # Non-existent region
                "name": "Orphan River",
                "slug": "orphan",
                "canonical_url": "http://example.com/river/orphan",
                "raw_html": "<html>orphan</html>",
                "crawl_timestamp": "2024-01-15T12:00:00Z",
            }
        )


def test_insert_river_unique_slug_within_region(test_storage, sample_region_data):
    """
    Test that same slug with different canonical_url in same region fails.

    UNIQUE(region_id, slug) constraint.
    """
    # Insert region
    region_id = test_storage.insert_region(sample_region_data)

    # Insert first river
    test_storage.insert_river(
        {
            "region_id": region_id,
            "name": "River 1",
            "slug": "test",  # Same slug
            "canonical_url": "http://example.com/river/test-1",
            "raw_html": "<html>1</html>",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Insert second river with same slug in same region
    with pytest.raises(Exception):  # SQLite raises IntegrityError
        test_storage.insert_river(
            {
                "region_id": region_id,
                "name": "River 2",
                "slug": "test",  # Same slug
                "canonical_url": "http://example.com/river/test-2",  # Different URL
                "raw_html": "<html>2</html>",
                "crawl_timestamp": "2024-01-15T12:00:00Z",
            }
        )


def test_insert_river_same_slug_different_regions(test_storage, sample_region_data):
    """
    Test that same slug in different regions is allowed.

    Slug uniqueness is per-region, not global.
    """
    # Insert two regions
    region_id_1 = test_storage.insert_region(sample_region_data)

    region_data_2 = sample_region_data.copy()
    region_data_2["name"] = "Region 2"
    region_data_2["slug"] = "region-2"
    region_data_2["canonical_url"] = "http://example.com/region/2"
    region_id_2 = test_storage.insert_region(region_data_2)

    # Insert river with same slug in region 1
    river_id_1 = test_storage.insert_river(
        {
            "region_id": region_id_1,
            "name": "River in Region 1",
            "slug": "test",  # Same slug
            "canonical_url": "http://example.com/river/1/test",
            "raw_html": "<html>1</html>",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Insert river with same slug in region 2 (should succeed)
    river_id_2 = test_storage.insert_river(
        {
            "region_id": region_id_2,
            "name": "River in Region 2",
            "slug": "test",  # Same slug
            "canonical_url": "http://example.com/river/2/test",
            "raw_html": "<html>2</html>",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Should create separate rivers
    assert river_id_1 != river_id_2

    # Verify 2 rivers exist
    rivers = test_storage.get_rivers()
    assert len(rivers) == 2


def test_count_rivers(test_storage, sample_region_data):
    """
    Test counting total rivers.
    """
    # Initially empty
    assert test_storage.count_rivers() == 0

    # Insert region
    region_id = test_storage.insert_region(sample_region_data)

    # Insert 3 rivers
    for i in range(3):
        test_storage.insert_river(
            {
                "region_id": region_id,
                "name": f"River {i}",
                "slug": f"river-{i}",
                "canonical_url": f"http://example.com/river/{i}",
                "raw_html": f"<html>{i}</html>",
                "crawl_timestamp": "2024-01-15T12:00:00Z",
            }
        )

    assert test_storage.count_rivers() == 3


def test_batch_insert_rivers(test_storage, sample_region_data):
    """
    Test batch insert with transaction.
    """
    # Insert region
    region_id = test_storage.insert_region(sample_region_data)

    rivers_data = [
        {
            "region_id": region_id,
            "name": "Batch River 1",
            "slug": "batch-1",
            "canonical_url": "http://example.com/river/batch/1",
            "raw_html": "<html>1</html>",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        },
        {
            "region_id": region_id,
            "name": "Batch River 2",
            "slug": "batch-2",
            "canonical_url": "http://example.com/river/batch/2",
            "raw_html": "<html>2</html>",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        },
    ]

    test_storage.batch_insert_rivers(rivers_data)

    # Verify both inserted
    assert test_storage.count_rivers() == 2


def test_river_timestamps(test_storage, sample_region_data):
    """
    Test that created_at and updated_at timestamps are set automatically.
    """
    # Insert region
    region_id = test_storage.insert_region(sample_region_data)

    # Insert river
    river_id = test_storage.insert_river(
        {
            "region_id": region_id,
            "name": "Test River",
            "slug": "test",
            "canonical_url": "http://example.com/river/test",
            "raw_html": "<html>test</html>",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    river = test_storage.get_river(river_id)

    # Verify timestamps exist
    assert "created_at" in river
    assert "updated_at" in river
    assert river["created_at"] is not None
    assert river["updated_at"] is not None


def test_river_cascade_delete_on_region_delete(test_storage, sample_region_data):
    """
    Test that deleting region cascades to rivers.

    ON DELETE CASCADE enforcement.
    """
    # Insert region
    region_id = test_storage.insert_region(sample_region_data)

    # Insert rivers
    river_id_1 = test_storage.insert_river(
        {
            "region_id": region_id,
            "name": "River 1",
            "slug": "river-1",
            "canonical_url": "http://example.com/river/1",
            "raw_html": "<html>1</html>",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    river_id_2 = test_storage.insert_river(
        {
            "region_id": region_id,
            "name": "River 2",
            "slug": "river-2",
            "canonical_url": "http://example.com/river/2",
            "raw_html": "<html>2</html>",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        }
    )

    # Verify rivers exist
    assert test_storage.get_river(river_id_1) is not None
    assert test_storage.get_river(river_id_2) is not None

    # Delete region
    import sqlite3

    conn = sqlite3.connect(test_storage.db_path)
    conn.execute("DELETE FROM regions WHERE id = ?", (region_id,))
    conn.commit()
    conn.close()

    # Verify rivers deleted (CASCADE)
    assert test_storage.get_river(river_id_1) is None
    assert test_storage.get_river(river_id_2) is None
