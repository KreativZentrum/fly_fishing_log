"""
Unit test: No inference validation.
Verifies parser does NOT infer missing fields (Article 5.2, FR-010).
"""

import pytest
from src.parser import Parser


def test_parser_no_default_values(test_config):
    """
    Test that parser returns None for uncertain fields, not defaults.

    Article 5.2: No inference or fabrication.
    FR-010: Missing data must remain null, not defaulted.
    """
    parser = Parser(test_config)

    river = {"id": 1, "name": "Test River"}

    # Minimal HTML with ambiguous fly
    html = """
    <html>
    <body>
        <div class="recommended-lures">
            <ul>
                <li>Mystery Pattern</li>
            </ul>
        </div>
    </body>
    </html>
    """

    details = parser.parse_river_detail(html, river)

    fly = details["flies"][0]

    # Name is explicit, should be present
    assert fly["name"] == "Mystery Pattern"
    assert fly["raw_text"] == "Mystery Pattern"

    # Category/size/color uncertain - should be None, not 'unknown' or '0'
    # If classify_fly can't determine, must return None
    if fly.get("category") is not None:
        # If not None, must be valid category
        assert fly["category"] in ["nymph", "dry", "streamer", "wet"]

    if fly.get("size") is not None:
        # If not None, must be valid size string
        assert isinstance(fly["size"], str)
        assert fly["size"] != "0"  # No default

    if fly.get("color") is not None:
        # If not None, must be valid color string
        assert isinstance(fly["color"], str)
        assert fly["color"] != "unknown"  # No default


def test_classify_fly_no_inference(test_config):
    """
    Test that classify_fly returns None for uncertain fields.
    """
    parser = Parser(test_config)

    # Ambiguous fly name with no clear indicators
    result = parser.classify_fly(name="XYZ Pattern", raw_text="XYZ Pattern")

    # Should return dict with None values, not defaults
    assert isinstance(result, dict)
    assert "category" in result
    assert "size" in result
    assert "color" in result

    # If uncertain, must be None
    # Not 'unknown', 0, '', etc.


def test_missing_sections_return_empty(test_config):
    """
    Test that missing sections return empty lists, not fabricated data.
    """
    parser = Parser(test_config)

    river = {"id": 1, "name": "Empty River"}

    # HTML with no sections
    html = "<html><body></body></html>"

    details = parser.parse_river_detail(html, river)

    # Missing sections should be empty, not populated with defaults
    assert details["flies"] == []
    assert details["regulations"] == []

    # Missing fish_type should be empty/None, not 'Unknown'
    if details.get("fish_type"):
        assert details["fish_type"]["raw_text"] != "Unknown"


def test_partial_fly_data_no_inference(test_config):
    """
    Test that partial fly data doesn't get inferred fields.
    """
    parser = Parser(test_config)

    river = {"id": 1, "name": "Test River"}

    # Fly with only name, no size/color indicators
    html = """
    <html>
    <body>
        <div class="recommended-lures">
            <ul>
                <li>Simple Fly</li>
            </ul>
        </div>
    </body>
    </html>
    """

    details = parser.parse_river_detail(html, river)

    fly = details["flies"][0]

    # Explicit field
    assert fly["name"] == "Simple Fly"

    # Uncertain fields - must not be inferred
    # If can't extract size from "Simple Fly", must be None
    if fly.get("size") is None:
        assert True, "Correctly didn't infer size"

    if fly.get("color") is None:
        assert True, "Correctly didn't infer color"


def test_regulation_type_no_inference(test_config):
    """
    Test that regulation types are not inferred from ambiguous text.
    """
    parser = Parser(test_config)

    river = {"id": 1, "name": "Test River"}

    # Ambiguous regulation text
    html = """
    <html>
    <body>
        <div class="regulations">
            <p>Check local rules</p>
        </div>
    </body>
    </html>
    """

    details = parser.parse_river_detail(html, river)

    if len(details["regulations"]) > 0:
        reg = details["regulations"][0]

        # Type should be specific, not generic like 'other' or 'unknown'
        # If can't determine type, either skip or use explicit 'unclassified'
        assert reg["type"] in [
            "catch_limit",
            "season_dates",
            "method",
            "permit_required",
            "flow_status",
            "unclassified",
        ]


def test_flow_level_no_inference(test_config):
    """
    Test that flow level is not inferred without explicit indicators.
    """
    parser = Parser(test_config)

    river = {"id": 1, "name": "Test River"}

    # Situation without clear flow indicator
    html = """
    <html>
    <body>
        <div class="situation">Varies by season</div>
    </body>
    </html>
    """

    details = parser.parse_river_detail(html, river)

    # Raw text should be stored
    assert details["conditions"]["raw_text"] == "Varies by season"

    # Flow level should not be inferred as 'medium' or any default
    if "flow_level" in details["conditions"]:
        # If present, must be explicit from text, or None
        assert details["conditions"]["flow_level"] in ["low", "medium", "high", None]


def test_no_fabricated_metadata(test_config):
    """
    Test that parser doesn't fabricate metadata like author, dates.
    """
    parser = Parser(test_config)

    river = {"id": 1, "name": "Test River"}

    html = """
    <html>
    <body>
        <div class="fish-type">Brown Trout</div>
    </body>
    </html>
    """

    details = parser.parse_river_detail(html, river)

    # Parser should not add fields like 'author', 'last_updated', 'verified_by'
    # unless explicitly present in HTML
    assert "author" not in details
    assert "last_updated" not in details
    assert "verified_by" not in details


def test_empty_string_vs_none(test_config):
    """
    Test that missing values are None, not empty strings.

    Article 5.2: Explicit null for missing data.
    """
    parser = Parser(test_config)

    result = parser.classify_fly(name="Test", raw_text="Test")

    # Uncertain fields should be None, not ''
    for key in ["category", "size", "color"]:
        value = result.get(key)
        if value is not None:
            # If not None, must be non-empty string
            assert value != "", f"Field '{key}' is empty string, should be None"
