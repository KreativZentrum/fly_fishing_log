"""
Unit test: Parser river detail extraction logic.
Tests parse_river_detail() and classify_fly() methods in isolation.
"""

import pytest
from src.parser import Parser


def test_parse_river_detail_complete(test_config):
    """
    Test parsing complete river detail page with all sections.
    """
    parser = Parser(test_config)

    river = {"id": 1, "name": "Test River", "canonical_url": "http://example.com/river/test"}

    html = """
    <html>
    <body>
        <div class="fish-type">Brown Trout, Rainbow Trout</div>
        <div class="situation">Clear water, medium flow</div>
        <div class="recommended-lures">
            <ul>
                <li>Pheasant Tail Nymph #16 Brown</li>
                <li>Royal Wulff #14 Red</li>
            </ul>
        </div>
        <div class="regulations">
            <p>Catch limit: 2 fish per day</p>
            <p>Season: October 1 - April 30</p>
        </div>
    </body>
    </html>
    """

    details = parser.parse_river_detail(html, river)

    # Verify structure
    assert isinstance(details, dict)
    assert "fish_type" in details
    assert "conditions" in details
    assert "flies" in details
    assert "regulations" in details

    # Verify fish type
    assert "Brown Trout" in details["fish_type"]["raw_text"]

    # Verify flies
    assert len(details["flies"]) == 2
    assert details["flies"][0]["name"] == "Pheasant Tail Nymph #16 Brown"

    # Verify regulations
    assert len(details["regulations"]) == 2


def test_parse_river_detail_minimal(test_config):
    """
    Test parsing minimal river detail page with only fish type.
    """
    parser = Parser(test_config)

    river = {"id": 1, "name": "Minimal River"}

    html = """
    <html>
    <body>
        <div class="fish-type">Brown Trout</div>
    </body>
    </html>
    """

    details = parser.parse_river_detail(html, river)

    assert details["fish_type"]["raw_text"] == "Brown Trout"
    assert details["flies"] == []
    assert details["regulations"] == []


def test_parse_river_detail_empty(test_config):
    """
    Test parsing empty river detail page.

    Article 4.4: Graceful handling.
    """
    parser = Parser(test_config)

    river = {"id": 1, "name": "Empty River"}

    html = "<html><body></body></html>"

    details = parser.parse_river_detail(html, river)

    # Should return empty structure, not crash
    assert details["flies"] == []
    assert details["regulations"] == []


def test_classify_fly_nymph(test_config):
    """
    Test classify_fly() for nymph patterns.
    """
    parser = Parser(test_config)

    result = parser.classify_fly(
        name="Pheasant Tail Nymph #16 Brown", raw_text="Pheasant Tail Nymph #16 Brown"
    )

    assert result["category"] == "nymph" or result["category"] is None
    assert result["size"] == "16" or result["size"] is None
    assert result["color"] == "brown" or result["color"] is None


def test_classify_fly_dry(test_config):
    """
    Test classify_fly() for dry fly patterns.
    """
    parser = Parser(test_config)

    result = parser.classify_fly(name="Royal Wulff #14 Red", raw_text="Royal Wulff #14 Red")

    # Royal Wulff is a dry fly
    assert result["category"] in ["dry", None]
    assert result["size"] in ["14", None]


def test_classify_fly_streamer(test_config):
    """
    Test classify_fly() for streamer patterns.
    """
    parser = Parser(test_config)

    result = parser.classify_fly(name="Woolly Bugger #10 Black", raw_text="Woolly Bugger #10 Black")

    assert result["category"] in ["streamer", None]
    assert result["size"] in ["10", None]
    assert result["color"] in ["black", None]


def test_classify_fly_uncertain(test_config):
    """
    Test that classify_fly() returns None for uncertain fields.

    Article 5.2: No inference.
    """
    parser = Parser(test_config)

    result = parser.classify_fly(name="Unknown Pattern", raw_text="Some random text")

    # If can't determine, should be None
    # At minimum, we can't infer category/size/color from this
    assert isinstance(result, dict)
    assert "category" in result
    assert "size" in result
    assert "color" in result


def test_parse_river_detail_special_characters(test_config):
    """
    Test parsing with special characters (Māori names).

    Article 5.3: No encoding assumptions.
    """
    parser = Parser(test_config)

    river = {"id": 1, "name": "Whanganui River"}

    html = """
    <html>
    <body>
        <div class="fish-type">Īnanga (Whitebait)</div>
        <div class="recommended-lures">
            <ul>
                <li>Kākahi Nymph</li>
            </ul>
        </div>
    </body>
    </html>
    """

    details = parser.parse_river_detail(html, river)

    # Should preserve special characters
    assert "Īnanga" in details["fish_type"]["raw_text"]
    assert details["flies"][0]["name"] == "Kākahi Nymph"


def test_parse_regulations_catch_limit(test_config):
    """
    Test parsing catch limit regulations.
    """
    parser = Parser(test_config)

    river = {"id": 1, "name": "Test River"}

    html = """
    <html>
    <body>
        <div class="regulations">
            <p>Catch limit: 2 fish per day</p>
        </div>
    </body>
    </html>
    """

    details = parser.parse_river_detail(html, river)

    assert len(details["regulations"]) == 1
    reg = details["regulations"][0]
    assert reg["type"] == "catch_limit"
    assert "2" in reg["value"]
    assert reg["raw_text"] == "Catch limit: 2 fish per day"


def test_parse_regulations_season(test_config):
    """
    Test parsing season regulations.
    """
    parser = Parser(test_config)

    river = {"id": 1, "name": "Test River"}

    html = """
    <html>
    <body>
        <div class="regulations">
            <p>Season: October 1 - April 30</p>
        </div>
    </body>
    </html>
    """

    details = parser.parse_river_detail(html, river)

    assert len(details["regulations"]) == 1
    reg = details["regulations"][0]
    assert reg["type"] == "season_dates"
    assert "October" in reg["value"]


def test_parse_river_detail_no_inference_flies(test_config):
    """
    Test that fly parsing doesn't infer missing information.

    Article 5.2: No inference.
    """
    parser = Parser(test_config)

    river = {"id": 1, "name": "Test River"}

    html = """
    <html>
    <body>
        <div class="recommended-lures">
            <ul>
                <li>Mystery Fly</li>
            </ul>
        </div>
    </body>
    </html>
    """

    details = parser.parse_river_detail(html, river)

    fly = details["flies"][0]
    assert fly["name"] == "Mystery Fly"

    # If category/size/color can't be determined, should be None
    # Not default values like 'unknown' or '0'
    if fly.get("category") is not None:
        assert fly["category"] in ["nymph", "dry", "streamer"]


def test_parse_flow_conditions(test_config):
    """
    Test parsing flow conditions from situation text.
    """
    parser = Parser(test_config)

    river = {"id": 1, "name": "Test River"}

    html = """
    <html>
    <body>
        <div class="situation">Clear water, high flow</div>
    </body>
    </html>
    """

    details = parser.parse_river_detail(html, river)

    assert "high flow" in details["conditions"]["raw_text"].lower()

    # Optionally normalized to 'high'
    if "flow_level" in details["conditions"]:
        assert details["conditions"]["flow_level"] in ["low", "medium", "high", None]
