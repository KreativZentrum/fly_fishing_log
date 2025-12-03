#!/usr/bin/env python3
"""
Complete test script for scraping Auckland-Waikato regional page.

This demonstrates:
1. Fetching the regional 'where-to-fish' page
2. Parsing river links using the new RegionalParser
3. Optionally fetching a sample river detail page
4. Saving results to database

Usage:
    python test_auckland_waikato.py              # Just parse and display
    python test_auckland_waikato.py --save       # Save to database
    python test_auckland_waikato.py --fetch-one  # Fetch one river detail page
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.fetcher import Fetcher
from src.logger import ScraperLogger
from src.regional_parser import RegionalParser
from src.storage import Storage


def main():
    """Run complete test of regional page scraping."""
    parser = argparse.ArgumentParser(description="Test Auckland-Waikato scraper")
    parser.add_argument(
        "--save", action="store_true", help="Save results to database"
    )
    parser.add_argument(
        "--fetch-one",
        action="store_true",
        help="Fetch and display one river detail page",
    )
    args = parser.parse_args()

    # Configuration
    TEST_URL = "https://nzfishing.com/auckland-waikato/where-to-fish/"
    REGION_NAME = "Auckland-Waikato"
    REGION_SLUG = "auckland-waikato"

    # Initialize components
    config = Config()
    logger = ScraperLogger(config.log_path)
    fetcher = Fetcher(config, logger)
    regional_parser = RegionalParser(config)

    print("\n" + "=" * 80)
    print("NZ Flyfishing Regional Scraper Test")
    print("=" * 80)
    print(f"Region: {REGION_NAME}")
    print(f"URL: {TEST_URL}")
    if args.save:
        print("Mode: SAVE TO DATABASE")
    elif args.fetch_one:
        print("Mode: FETCH ONE RIVER DETAIL")
    else:
        print("Mode: DISPLAY ONLY")
    print("=" * 80 + "\n")

    # Initialize storage if saving
    storage = None
    if args.save:
        storage = Storage(config.database_path, logger)
        # initialize_schema is called automatically in __init__
        print("✓ Database initialized\n")

    # Step 1: Fetch regional page
    print("Step 1: Fetching regional page...")
    try:
        html = fetcher.fetch(TEST_URL)
        print(f"✓ Fetched {len(html):,} bytes")
        print(f"  Cache stats: {fetcher._cache_hits} hits, {fetcher._cache_misses} misses\n")
    except Exception as e:
        print(f"✗ Fetch failed: {e}")
        return 1

    # Step 2: Parse rivers
    print("Step 2: Parsing river links...")
    try:
        rivers = regional_parser.parse_regional_page(html, TEST_URL, REGION_NAME)

        if not rivers:
            print("✗ No rivers found")
            return 1

        print(f"✓ Found {len(rivers)} rivers:\n")

        # Display rivers
        for i, river in enumerate(rivers, 1):
            print(f"{i:3}. {river['name']:<35} {river['slug']:<30}")

        print()

    except Exception as e:
        print(f"✗ Parse failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    # Step 3: Save to database (if requested)
    if args.save and storage:
        print("Step 3: Saving to database...")
        try:
            # First, ensure region exists
            region_data = {
                "name": REGION_NAME,
                "canonical_url": "https://nzfishing.com/auckland-waikato/",
                "slug": REGION_SLUG,
                "description": "Auckland-Waikato region",
            }

            # Use direct conn access (Storage manages its own connection)
            conn = storage.conn

            # Insert or get region
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO regions (name, canonical_url, slug, description)
                VALUES (?, ?, ?, ?)
                """,
                (
                    region_data["name"],
                    region_data["canonical_url"],
                    region_data["slug"],
                    region_data["description"],
                ),
            )

            region_id = cursor.lastrowid
            if region_id == 0:  # Already existed
                cursor = conn.execute(
                    "SELECT id FROM regions WHERE slug = ?", (REGION_SLUG,)
                )
                region_id = cursor.fetchone()[0]

            print(f"✓ Region ID: {region_id}")

            # Insert rivers
            inserted = 0
            for river in rivers:
                cursor = conn.execute(
                    """
                    INSERT OR IGNORE INTO rivers 
                    (name, canonical_url, slug, region_id)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        river["name"],
                        river["canonical_url"],
                        river["slug"],
                        region_id,
                    ),
                )
                if cursor.rowcount > 0:
                    inserted += 1

            conn.commit()
            print(f"✓ Saved {inserted} new rivers to database\n")

        except Exception as e:
            print(f"✗ Database save failed: {e}")
            import traceback

            traceback.print_exc()
            return 1

    # Step 4: Fetch one river detail (if requested)
    if args.fetch_one and rivers:
        print("Step 4: Fetching sample river detail page...")
        sample_river = rivers[0]
        print(f"  River: {sample_river['name']}")
        print(f"  URL: {sample_river['canonical_url']}\n")

        try:
            river_html = fetcher.fetch(sample_river["canonical_url"])
            print(f"✓ Fetched {len(river_html):,} bytes")

            # Display first 500 chars of text content
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(river_html, "lxml")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            text = soup.get_text()
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            text_preview = "\n".join(lines[:20])

            print("\n--- River Page Preview ---")
            print(text_preview[:500] + "...")
            print("--- End Preview ---\n")

        except Exception as e:
            print(f"✗ Failed to fetch river detail: {e}")

    # Summary
    print("=" * 80)
    print("Test Complete!")
    print("=" * 80)
    print(f"\nResults:")
    print(f"  - Found {len(rivers)} rivers from {REGION_NAME}")
    if args.save:
        print(f"  - Saved to database: {config.database_path}")
    if args.fetch_one:
        print(f"  - Fetched sample river detail page")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
