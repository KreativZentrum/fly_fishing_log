#!/usr/bin/env python3
"""
Quick demo of regional scraping with pre-configured URLs.

This demonstrates the regional scraping functionality without
requiring interactive input.

Usage:
    python demo_regional_scrape.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.fetcher import Fetcher
from src.logger import ScraperLogger
from src.regional_parser import RegionalParser
from src.storage import Storage


def extract_region_info(url: str):
    """Extract region name and slug from URL."""
    parts = url.rstrip('/').split('/')
    try:
        idx = parts.index('where-to-fish')
        if idx > 0:
            slug = parts[idx - 1]
            name = slug.replace('-', ' ').title()
            return name, slug
    except ValueError:
        pass
    return "Unknown", "unknown"


def demo_scrape():
    """Demo scraping with two regional URLs."""
    
    # Demo URLs (you can change these)
    DEMO_URLS = [
        "https://nzfishing.com/northland/where-to-fish/",
        # Add more here if you want
    ]
    
    print("\n" + "=" * 80)
    print("Regional Scraper Demo")
    print("=" * 80)
    print(f"\nScraping {len(DEMO_URLS)} regional page(s):")
    for url in DEMO_URLS:
        print(f"  - {url}")
    print()
    
    # Initialize
    config = Config()
    logger = ScraperLogger(config.log_path)
    fetcher = Fetcher(config, logger)
    parser = RegionalParser(config)
    storage = Storage(config.database_path, logger)
    
    total_rivers = 0
    
    # Process each URL
    for i, url in enumerate(DEMO_URLS, 1):
        print(f"\n[{i}/{len(DEMO_URLS)}] {url}")
        
        # Extract region info
        region_name, region_slug = extract_region_info(url)
        print(f"  Region: {region_name} ({region_slug})")
        
        # Fetch
        try:
            html = fetcher.fetch(url)
            print(f"  ✓ Fetched {len(html):,} bytes")
        except Exception as e:
            print(f"  ✗ Fetch failed: {e}")
            continue
        
        # Parse
        try:
            rivers = parser.parse_regional_page(html, url, region_name)
            print(f"  ✓ Parsed {len(rivers)} rivers")
            
            # Show first 5 rivers
            if rivers:
                print(f"  Sample rivers:")
                for river in rivers[:5]:
                    print(f"    - {river['name']}")
                if len(rivers) > 5:
                    print(f"    ... and {len(rivers) - 5} more")
        except Exception as e:
            print(f"  ✗ Parse failed: {e}")
            continue
        
        # Save
        try:
            conn = storage.conn
            
            # Insert region
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO regions (name, canonical_url, slug, description)
                VALUES (?, ?, ?, ?)
                """,
                (region_name, url, region_slug, f"{region_name} region")
            )
            
            region_id = cursor.lastrowid
            if region_id == 0:
                cursor = conn.execute(
                    "SELECT id FROM regions WHERE slug = ?", (region_slug,)
                )
                row = cursor.fetchone()
                region_id = row[0] if row else None
            
            # Insert rivers
            inserted = 0
            for river in rivers:
                cursor = conn.execute(
                    """
                    INSERT OR IGNORE INTO rivers 
                    (name, canonical_url, slug, region_id)
                    VALUES (?, ?, ?, ?)
                    """,
                    (river['name'], river['canonical_url'], river['slug'], region_id)
                )
                if cursor.rowcount > 0:
                    inserted += 1
            
            conn.commit()
            print(f"  ✓ Saved to database ({inserted} new rivers)")
            total_rivers += inserted
            
        except Exception as e:
            print(f"  ✗ Database save failed: {e}")
            continue
    
    # Summary
    print(f"\n{'=' * 80}")
    print("Demo Complete!")
    print(f"{'=' * 80}")
    print(f"\nResults:")
    print(f"  - URLs processed: {len(DEMO_URLS)}")
    print(f"  - New rivers saved: {total_rivers}")
    print(f"  - Database: {config.database_path}")
    
    # Query current totals
    cursor = storage.conn.execute("SELECT COUNT(*) FROM regions")
    total_regions = cursor.fetchone()[0]
    
    cursor = storage.conn.execute("SELECT COUNT(*) FROM rivers")
    total_rivers_db = cursor.fetchone()[0]
    
    print(f"\nDatabase totals:")
    print(f"  - Total regions: {total_regions}")
    print(f"  - Total rivers: {total_rivers_db}")
    print()


if __name__ == "__main__":
    demo_scrape()
