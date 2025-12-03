#!/usr/bin/env python3
"""
Example: Interactive CLI mode for regional URL input.

This demonstrates how the CLI could prompt for regional page URLs
instead of trying to discover them from the broken main index.

Usage:
    python cli_regional_mode.py
    
Then enter URLs when prompted:
    https://nzfishing.com/auckland-waikato/where-to-fish/
    https://nzfishing.com/northland/where-to-fish/
    (leave blank to finish)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.fetcher import Fetcher
from src.logger import ScraperLogger
from src.regional_parser import RegionalParser
from src.storage import Storage


def extract_region_name_from_url(url: str) -> str:
    """
    Extract region name from URL.
    
    Example:
        https://nzfishing.com/auckland-waikato/where-to-fish/
        -> Auckland-Waikato
    """
    # Remove trailing slash and split
    parts = url.rstrip('/').split('/')
    
    # Get the part before 'where-to-fish'
    try:
        idx = parts.index('where-to-fish')
        if idx > 0:
            slug = parts[idx - 1]
            # Convert slug to name: auckland-waikato -> Auckland-Waikato
            return slug.replace('-', ' ').title()
    except ValueError:
        pass
    
    # Fallback: use domain-relative path
    if len(parts) > 3:
        return parts[3].replace('-', ' ').title()
    
    return "Unknown Region"


def scrape_regional_urls_interactive():
    """
    Interactive mode: prompt user for regional URLs and scrape them.
    """
    print("\n" + "=" * 80)
    print("NZ Flyfishing Regional Scraper - Interactive Mode")
    print("=" * 80)
    print("\nThis mode allows you to scrape regional 'where-to-fish' pages directly.")
    print("Useful when the main index page is not working correctly.\n")
    
    # Initialize components
    config = Config()
    logger = ScraperLogger(config.log_path)
    fetcher = Fetcher(config, logger)
    regional_parser = RegionalParser(config)
    storage = Storage(config.database_path, logger)
    
    print("✓ Components initialized\n")
    
    # Collect URLs
    print("Enter regional page URLs (one per line).")
    print("Examples:")
    print("  https://nzfishing.com/auckland-waikato/where-to-fish/")
    print("  https://nzfishing.com/northland/where-to-fish/")
    print("\nPress Enter with no input to start scraping.\n")
    
    urls = []
    while True:
        url = input(f"URL {len(urls) + 1} (or Enter to finish): ").strip()
        if not url:
            break
        
        # Basic validation
        if not url.startswith('http'):
            print("  ⚠ Warning: URL should start with http:// or https://")
            confirm = input("  Use anyway? (y/n): ").lower()
            if confirm != 'y':
                continue
        
        urls.append(url)
    
    if not urls:
        print("\nNo URLs provided. Exiting.")
        return
    
    print(f"\n{'=' * 80}")
    print(f"Starting scrape of {len(urls)} regional page(s)")
    print(f"{'=' * 80}\n")
    
    total_regions = 0
    total_rivers = 0
    
    # Process each URL
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] Processing: {url}")
        
        # Extract region name from URL
        region_name = extract_region_name_from_url(url)
        region_slug = url.rstrip('/').split('/')[-2]  # e.g., 'auckland-waikato'
        
        print(f"  Region: {region_name} (slug: {region_slug})")
        
        # Fetch page
        try:
            html = fetcher.fetch(url)
            print(f"  ✓ Fetched {len(html):,} bytes")
        except Exception as e:
            print(f"  ✗ Fetch failed: {e}")
            continue
        
        # Parse rivers
        try:
            rivers = regional_parser.parse_regional_page(html, url, region_name)
            print(f"  ✓ Parsed {len(rivers)} rivers")
        except Exception as e:
            print(f"  ✗ Parse failed: {e}")
            continue
        
        # Save to database
        try:
            conn = storage.conn
            
            # Insert/update region
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO regions (name, canonical_url, slug, description)
                VALUES (?, ?, ?, ?)
                """,
                (region_name, url, region_slug, f"{region_name} region")
            )
            
            region_id = cursor.lastrowid
            if region_id == 0:  # Already existed
                cursor = conn.execute(
                    "SELECT id FROM regions WHERE slug = ?", (region_slug,)
                )
                row = cursor.fetchone()
                region_id = row[0] if row else None
            
            if not region_id:
                print(f"  ✗ Could not save region")
                continue
            
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
            print(f"  ✓ Saved region + {inserted} new rivers to database\n")
            
            total_regions += 1
            total_rivers += inserted
            
        except Exception as e:
            print(f"  ✗ Database save failed: {e}\n")
            continue
    
    # Summary
    print(f"{'=' * 80}")
    print("Scraping Complete!")
    print(f"{'=' * 80}")
    print(f"\nResults:")
    print(f"  - Processed: {len(urls)} URLs")
    print(f"  - Regions saved: {total_regions}")
    print(f"  - Rivers saved: {total_rivers}")
    print(f"  - Database: {config.database_path}")
    print()


def scrape_regional_urls_from_file(filepath: str):
    """
    Batch mode: read URLs from file and scrape them.
    
    File format (one URL per line):
        https://nzfishing.com/auckland-waikato/where-to-fish/
        https://nzfishing.com/northland/where-to-fish/
        # comments ignored
    """
    print(f"\nReading URLs from: {filepath}")
    
    urls = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                urls.append(line)
    
    print(f"Found {len(urls)} URLs\n")
    
    if not urls:
        print("No valid URLs in file. Exiting.")
        return
    
    # Use same scraping logic as interactive mode
    # (implementation would be similar to above)
    print("Batch scraping not yet implemented - use interactive mode for now.")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # File mode
        scrape_regional_urls_from_file(sys.argv[1])
    else:
        # Interactive mode
        scrape_regional_urls_interactive()
