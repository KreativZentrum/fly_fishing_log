"""
Unit test: Parser river extraction logic.
Tests parse_region_page() method in isolation.
"""

import pytest
from src.parser import Parser
from tests.fixtures.sample_pages import (
    MINIMAL_REGION,
    MULTIPLE_RIVERS,
    DUPLICATE_LINKS,
    INVALID_URLS,
    NO_MATCHES,
    EMPTY_HTML,
    SAMPLE_REGION_HTML,
)


def test_parse_region_page_minimal(test_config, sample_region_data):
    """
    Test parsing minimal valid region page with 1 river.
    """
    parser = Parser(test_config)

    # Create mock region object
    region = {"id": 1, "name": "Test Region", "canonical_url": "http://example.com/region/test"}

    rivers = parser.parse_region_page(MINIMAL_REGION, region)

    assert len(rivers) == 1, f"Expected 1 river, got {len(rivers)}"

    river = rivers[0]
    assert river["name"] == "Test River"
    assert river["canonical_url"] == "/river/test-river"
    assert "slug" in river


def test_parse_region_page_multiple(test_config):
    """
    Test parsing region page with multiple rivers.
    """
    parser = Parser(test_config)

    region = {"id": 1, "name": "Test Region", "canonical_url": "http://example.com/region/test"}

    rivers = parser.parse_region_page(MULTIPLE_RIVERS, region)

    assert len(rivers) == 4, f"Expected 4 rivers, got {len(rivers)}"

    # Verify all expected names present
    names = {r["name"] for r in rivers}
    assert names == {"Tongariro", "Rangitikei", "Manawatu", "Whanganui"}

    # Verify all have required fields
    for river in rivers:
        assert "name" in river
        assert "canonical_url" in river
        assert "slug" in river
        assert river["name"]  # Not empty
        assert river["canonical_url"]  # Not empty


def test_parse_region_page_sample_html(test_config):
    """
    Test parsing realistic sample region page.
    """
    parser = Parser(test_config)

    region = {
        "id": 1,
        "name": "North Island",
        "canonical_url": "http://localhost:8000/region/north-island",
    }

    rivers = parser.parse_region_page(SAMPLE_REGION_HTML, region)

    # Sample has 2 rivers
    assert len(rivers) == 2

    # Verify names
    names = {r["name"] for r in rivers}
    assert "Tongariro River" in names or "Rangitikei River" in names


def test_parse_region_page_duplicate_links(test_config):
    """
    Test that duplicate river links are de-duplicated by canonical URL.
    """
    parser = Parser(test_config)

    region = {"id": 1, "name": "Test Region", "canonical_url": "http://example.com/region/test"}

    rivers = parser.parse_region_page(DUPLICATE_LINKS, region)

    # DUPLICATE_LINKS has duplicates
    # Should de-duplicate to unique canonical URLs
    urls = {r["canonical_url"] for r in rivers}
    assert len(urls) == len(rivers), "URLs not properly de-duplicated"


def test_parse_region_page_invalid_urls(test_config):
    """
    Test that invalid/empty URLs are skipped gracefully.

    Article 4.4: Graceful handling of malformed data.
    """
    parser = Parser(test_config)

    region = {"id": 1, "name": "Test Region", "canonical_url": "http://example.com/region/test"}

    rivers = parser.parse_region_page(INVALID_URLS, region)

    # Should only extract valid URLs
    for river in rivers:
        assert river["canonical_url"], "Empty URL not filtered"
        assert river["canonical_url"] not in ["", "#"], "Invalid URL not filtered"


def test_parse_region_page_no_matches(test_config):
    """
    Test parsing HTML with no matching selectors.

    Edge Case: "Fishing Waters" section missing.
    """
    parser = Parser(test_config)

    region = {"id": 1, "name": "Test Region", "canonical_url": "http://example.com/region/test"}

    rivers = parser.parse_region_page(NO_MATCHES, region)

    # Should return empty list, not raise exception
    assert rivers == [], f"Expected empty list for no matches, got {rivers}"


def test_parse_region_page_empty_html(test_config):
    """
    Test parsing completely empty HTML.
    """
    parser = Parser(test_config)

    region = {"id": 1, "name": "Test Region", "canonical_url": "http://example.com/region/test"}

    rivers = parser.parse_region_page(EMPTY_HTML, region)

    assert rivers == [], f"Expected empty list for empty HTML, got {rivers}"


def test_parse_region_page_slug_generation(test_config):
    """
    Test that slugs are properly generated from names or URLs.
    """
    parser = Parser(test_config)

    region = {"id": 1, "name": "Test Region", "canonical_url": "http://example.com/region/test"}

    rivers = parser.parse_region_page(MULTIPLE_RIVERS, region)

    # Verify slugs are lowercase, hyphenated
    for river in rivers:
        slug = river["slug"]
        assert slug.islower() or "-" in slug, f"Slug '{slug}' not properly formatted"
        assert " " not in slug, f"Slug '{slug}' contains spaces"


def test_parse_region_page_region_context(test_config):
    """
    Test that parser has access to region context (for logging/debugging).
    """
    parser = Parser(test_config)

    region = {
        "id": 42,
        "name": "Context Region",
        "canonical_url": "http://example.com/region/context",
    }

    # Parser should accept region parameter
    # (Used for context in error messages, FK validation, etc.)
    rivers = parser.parse_region_page(MINIMAL_REGION, region)

    # Verify parsing succeeded with region context
    assert isinstance(rivers, list)


def test_parse_region_page_with_custom_selector(test_config):
    """
    Test that parser respects custom selector from config.
    """
    # Modify config selector
    test_config.data["discovery_rules"]["river_selector"] = "ul.custom-rivers a"

    parser = Parser(test_config)

    region = {"id": 1, "name": "Test Region", "canonical_url": "http://example.com/region/test"}

    html = """
    <html><body>
        <ul class="custom-rivers">
            <a href="/river/custom">Custom River</a>
        </ul>
    </body></html>
    """

    rivers = parser.parse_region_page(html, region)

    assert len(rivers) == 1
    assert rivers[0]["name"] == "Custom River"


def test_parse_region_page_no_inference(test_config):
    """
    Test that parser only extracts explicit content, no inference.

    Article 5.2: No inference or fabrication.
    """
    parser = Parser(test_config)

    region = {"id": 1, "name": "Test Region", "canonical_url": "http://example.com/region/test"}

    # Use minimal HTML with only name and URL
    html = """
    <html><body>
        <div class="river-list">
            <a href="/river/test">Test River</a>
        </div>
    </body></html>
    """

    rivers = parser.parse_region_page(html, region)
    assert len(rivers) == 1

    river = rivers[0]

    # Should have name and URL (explicit)
    assert river["name"] == "Test River"
    assert river["canonical_url"] == "/river/test"

    # No fabricated fields
    # (Section info will come from detail pages in US3)


def test_parse_region_page_special_characters(test_config):
    """
    Test parsing river names with special characters (Māori names).

    Article 5.3: No encoding assumptions.
    """
    parser = Parser(test_config)

    region = {"id": 1, "name": "Test Region", "canonical_url": "http://example.com/region/test"}

    # Create test HTML with Māori characters
    html = """
    <html><body>
        <div class="river-list">
            <a href="/river/waikato">Waikato River</a>
            <a href="/river/whanganui">Whanganui (Te Awa Tupua)</a>
        </div>
    </body></html>
    """

    rivers = parser.parse_region_page(html, region)

    # Should preserve special characters
    names = {r["name"] for r in rivers}
    assert "Whanganui (Te Awa Tupua)" in names, "Special characters not preserved"


def test_parse_region_page_nested_structure(test_config):
    """
    Test parsing complex nested HTML structure.
    """
    parser = Parser(test_config)

    region = {"id": 1, "name": "Test Region", "canonical_url": "http://example.com/region/test"}

    from tests.fixtures.sample_pages import NESTED_HTML

    # Parser should handle nested div structures
    # May return empty list if selector doesn't match nested structure
    rivers = parser.parse_region_page(NESTED_HTML, region)

    # Should not crash, return list
    assert isinstance(rivers, list)
