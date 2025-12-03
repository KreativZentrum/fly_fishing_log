#!/usr/bin/env python3
"""
Test script to scrape Auckland-Waikato region page.
Tests parsing of https://nzfishing.com/auckland-waikato/where-to-fish/
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.fetcher import Fetcher
from src.logger import ScraperLogger
from src.parser import Parser

# Test URL
TEST_URL = "https://nzfishing.com/auckland-waikato/where-to-fish/"


def main():
    """Run test scrape of Auckland-Waikato region page."""
    # Initialize components
    config = Config()
    logger = ScraperLogger(config.log_path)
    fetcher = Fetcher(config, logger)
    parser = Parser(config)

    print(f"\n{'='*80}")
    print(f"Testing Regional Page Scrape")
    print(f"URL: {TEST_URL}")
    print(f"{'='*80}\n")

    # Step 1: Fetch HTML
    print("Step 1: Fetching HTML...")
    try:
        html = fetcher.fetch(TEST_URL)
        print(f"✓ Fetched {len(html)} bytes")
        
        # Save raw HTML for inspection
        test_cache_path = Path("test_output")
        test_cache_path.mkdir(exist_ok=True)
        output_file = test_cache_path / "auckland_waikato_raw.html"
        output_file.write_text(html)
        print(f"✓ Saved raw HTML to: {output_file}")
        
    except Exception as e:
        print(f"✗ Fetch failed: {e}")
        return 1

    # Step 2: Try to parse rivers from the page
    print("\nStep 2: Attempting to parse rivers...")
    try:
        # Try the standard river parsing method
        rivers = parser.parse_river_index(html, region_name="Auckland-Waikato")
        
        if rivers:
            print(f"✓ Found {len(rivers)} rivers:")
            for river in rivers[:10]:  # Show first 10
                print(f"  - {river.get('name', 'Unknown')} -> {river.get('canonical_url', 'No URL')}")
            if len(rivers) > 10:
                print(f"  ... and {len(rivers) - 10} more")
        else:
            print("✗ No rivers found with standard parser")
            
    except Exception as e:
        print(f"✗ Parse failed: {e}")
        print("\nThis is expected - the page structure may be different.")

    # Step 3: Inspect HTML structure
    print("\nStep 3: Analyzing HTML structure...")
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html, 'lxml')
    
    # Look for common link patterns
    print("\nSearching for potential river links...")
    
    # Check for various link patterns
    patterns = [
        ("Links in article tags", soup.select("article a")),
        ("Links with href containing 'river'", soup.find_all('a', href=lambda h: h and 'river' in h.lower())),
        ("Links with text containing 'River'", soup.find_all('a', string=lambda s: s and 'River' in str(s))),
        ("Links in list items", soup.select("li a")),
        ("Links in divs with class containing 'river'", soup.select("div[class*='river'] a")),
        ("Links in divs with class containing 'location'", soup.select("div[class*='location'] a")),
        ("All links on page", soup.find_all('a', href=True)),
    ]
    
    for pattern_name, links in patterns:
        # Filter to only nzfishing.com links (exclude external)
        nz_links = [l for l in links if l.get('href') and 'nzfishing.com' in l.get('href', '')]
        if nz_links:
            print(f"\n{pattern_name}: {len(nz_links)} links")
            # Show first 5
            for link in nz_links[:5]:
                href = link.get('href', '')
                text = link.get_text().strip()[:50]
                print(f"  - {text} -> {href}")
            if len(nz_links) > 5:
                print(f"  ... and {len(nz_links) - 5} more")

    # Step 4: Look for specific content patterns
    print("\n\nStep 4: Looking for content structure...")
    
    # Check page title
    title = soup.find('title')
    if title:
        print(f"Page Title: {title.get_text()}")
    
    # Check for main content areas
    main_areas = [
        ('Main content', soup.find('main')),
        ('Article content', soup.find('article')),
        ('Content div', soup.find('div', class_=lambda c: c and 'content' in c.lower())),
        ('Builder content', soup.find('div', class_=lambda c: c and 'builder' in c.lower())),
    ]
    
    for area_name, area in main_areas:
        if area:
            links_in_area = area.find_all('a', href=True)
            print(f"\n{area_name}: {len(links_in_area)} links found")
            if links_in_area:
                print("  Sample links:")
                for link in links_in_area[:3]:
                    print(f"    - {link.get_text().strip()[:40]} -> {link.get('href', '')[:60]}")

    print("\n" + "="*80)
    print("Test Complete!")
    print("="*80)
    print("\nNext Steps:")
    print("1. Review test_output/auckland_waikato_raw.html")
    print("2. Inspect HTML structure to identify river link patterns")
    print("3. Update parser.py with correct selectors if needed")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
