"""
Unit test: Storage layer region CRUD operations.
Tests Region insert, get, update, and FK validation.
"""

import pytest
from src.storage import Storage
from src.exceptions import StorageError


def test_insert_region(test_storage):
    """
    Test basic region insertion.
    """
    region_id = test_storage.insert_region(
        name="Test Region",
        slug="test-region",
        canonical_url="http://example.com/region/test",
        source_url="http://example.com/index",
        raw_html="<html>test</html>",
        description="A test region",
        crawl_timestamp="2024-01-15T12:00:00Z",
    )

    assert region_id is not None
    assert region_id > 0


def test_get_region(test_storage):
    """
    Test retrieving region by ID.
    """
    # Insert region
    region_id = test_storage.insert_region(
        name="Test Region",
        slug="test-region",
        canonical_url="http://example.com/region/test",
        source_url="http://example.com/index",
        raw_html="<html>test</html>",
        description="A test region",
        crawl_timestamp="2024-01-15T12:00:00Z",
    )

    # Retrieve region
    region = test_storage.get_region(region_id)

    assert region is not None
    assert region["id"] == region_id
    assert region["name"] == "Test Region"
    assert region["slug"] == "test-region"
    assert region["canonical_url"] == "http://example.com/region/test"
    assert region["description"] == "A test region"


def test_get_region_not_found(test_storage):
    """
    Test retrieving non-existent region returns None.
    """
    region = test_storage.get_region(9999)
    assert region is None


def test_get_regions(test_storage):
    """
    Test retrieving all regions.
    """
    # Insert multiple regions
    test_storage.insert_region(
        name="Region 1",
        slug="region-1",
        canonical_url="http://example.com/region/1",
        source_url="http://example.com/index",
        raw_html="<html>1</html>",
        description="",
        crawl_timestamp="2024-01-15T12:00:00Z",
    )

    test_storage.insert_region(
        name="Region 2",
        slug="region-2",
        canonical_url="http://example.com/region/2",
        source_url="http://example.com/index",
        raw_html="<html>2</html>",
        description="",
        crawl_timestamp="2024-01-15T12:00:00Z",
    )

    # Retrieve all
    regions = test_storage.get_regions()

    assert len(regions) == 2
    names = {r["name"] for r in regions}
    assert names == {"Region 1", "Region 2"}


def test_insert_region_duplicate_canonical_url(test_storage):
    """
    Test that inserting region with duplicate canonical_url updates, not duplicates.

    Article 6.4: Upsert pattern for immutability.
    """
    # First insert
    region_id_1 = test_storage.insert_region(
        name="Original Name",
        slug="original-slug",
        canonical_url="http://example.com/region/test",
        source_url="http://example.com/index",
        raw_html="<html>original</html>",
        description="Original description",
        crawl_timestamp="2024-01-15T12:00:00Z",
    )

    # Second insert with same canonical_url
    region_id_2 = test_storage.insert_region(
        name="Updated Name",
        slug="updated-slug",
        canonical_url="http://example.com/region/test",  # Same URL
        source_url="http://example.com/index",
        raw_html="<html>updated</html>",
        description="Updated description",
        crawl_timestamp="2024-01-15T13:00:00Z",
    )

    # Should return same ID (upsert)
    assert region_id_1 == region_id_2

    # Verify only 1 region exists
    regions = test_storage.get_regions()
    assert len(regions) == 1

    # Verify updated fields (name, description can change)
    region = regions[0]
    assert region["name"] == "Updated Name"
    assert region["description"] == "Updated description"


def test_insert_region_duplicate_slug_different_url(test_storage):
    """
    Test that same slug with different canonical_url creates separate records.

    Slug is not globally unique, canonical_url is.
    """
    # Insert region 1
    region_id_1 = test_storage.insert_region(
        name="Test Region 1",
        slug="test",  # Same slug
        canonical_url="http://example.com/region/test-1",  # Different URL
        source_url="http://example.com/index",
        raw_html="<html>1</html>",
        description="",
        crawl_timestamp="2024-01-15T12:00:00Z",
    )

    # Insert region 2 with same slug
    region_id_2 = test_storage.insert_region(
        name="Test Region 2",
        slug="test",  # Same slug
        canonical_url="http://example.com/region/test-2",  # Different URL
        source_url="http://example.com/index",
        raw_html="<html>2</html>",
        description="",
        crawl_timestamp="2024-01-15T12:00:00Z",
    )

    # Should create separate regions
    assert region_id_1 != region_id_2

    # Verify 2 regions exist
    regions = test_storage.get_regions()
    assert len(regions) == 2


def test_count_regions(test_storage):
    """
    Test counting total regions.
    """
    # Initially empty
    assert test_storage.count_regions() == 0

    # Insert 3 regions
    for i in range(3):
        test_storage.insert_region(
            name=f"Region {i}",
            slug=f"region-{i}",
            canonical_url=f"http://example.com/region/{i}",
            source_url="http://example.com/index",
            raw_html=f"<html>{i}</html>",
            description="",
            crawl_timestamp="2024-01-15T12:00:00Z",
        )

    assert test_storage.count_regions() == 3


def test_batch_insert_regions(test_storage):
    """
    Test batch insert with transaction.
    """
    regions_data = [
        {
            "name": "Batch Region 1",
            "slug": "batch-1",
            "canonical_url": "http://example.com/batch/1",
            "source_url": "http://example.com/index",
            "raw_html": "<html>1</html>",
            "description": "",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        },
        {
            "name": "Batch Region 2",
            "slug": "batch-2",
            "canonical_url": "http://example.com/batch/2",
            "source_url": "http://example.com/index",
            "raw_html": "<html>2</html>",
            "description": "",
            "crawl_timestamp": "2024-01-15T12:00:00Z",
        },
    ]

    test_storage.batch_insert_regions(regions_data)

    # Verify both inserted
    assert test_storage.count_regions() == 2


def test_get_uncrawled_regions(test_storage):
    """
    Test querying regions without crawl timestamps.
    """
    # Insert crawled region
    test_storage.insert_region(
        name="Crawled",
        slug="crawled",
        canonical_url="http://example.com/crawled",
        source_url="http://example.com/index",
        raw_html="<html>crawled</html>",
        description="",
        crawl_timestamp="2024-01-15T12:00:00Z",  # Has timestamp
    )

    # Insert uncrawled region
    test_storage.insert_region(
        name="Uncrawled",
        slug="uncrawled",
        canonical_url="http://example.com/uncrawled",
        source_url="http://example.com/index",
        raw_html="",
        description="",
        crawl_timestamp="",  # Empty = uncrawled
    )

    # Query uncrawled
    uncrawled = test_storage.get_uncrawled_regions()

    assert len(uncrawled) == 1
    assert uncrawled[0]["name"] == "Uncrawled"


def test_insert_region_empty_name_raises_error(test_storage):
    """
    Test that inserting region with empty name raises ValueError.

    Article 6.3: Required fields must be non-empty.
    """
    with pytest.raises(ValueError, match="name"):
        test_storage.insert_region(
            name="",  # Empty name
            slug="test",
            canonical_url="http://example.com/test",
            source_url="http://example.com/index",
            raw_html="<html>test</html>",
            description="",
            crawl_timestamp="2024-01-15T12:00:00Z",
        )


def test_insert_region_empty_canonical_url_raises_error(test_storage):
    """
    Test that inserting region with empty canonical_url raises ValueError.
    """
    with pytest.raises(ValueError, match="canonical_url"):
        test_storage.insert_region(
            name="Test",
            slug="test",
            canonical_url="",  # Empty URL
            source_url="http://example.com/index",
            raw_html="<html>test</html>",
            description="",
            crawl_timestamp="2024-01-15T12:00:00Z",
        )


def test_region_timestamps(test_storage):
    """
    Test that created_at and updated_at timestamps are set automatically.
    """
    region_id = test_storage.insert_region(
        name="Test",
        slug="test",
        canonical_url="http://example.com/test",
        source_url="http://example.com/index",
        raw_html="<html>test</html>",
        description="",
        crawl_timestamp="2024-01-15T12:00:00Z",
    )

    region = test_storage.get_region(region_id)

    # Verify timestamps exist
    assert "created_at" in region
    assert "updated_at" in region
    assert region["created_at"] is not None
    assert region["updated_at"] is not None
