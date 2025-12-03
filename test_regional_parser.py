#!/usr/bin/env python3
"""
Test script for parsing regional 'where-to-fish' pages.
This tests parsing pages like: https://nzfishing.com/auckland-waikato/where-to-fish/

These pages have a different structure than the main regions index.
They contain inline links to rivers within paragraph text.
"""

import sys
from pathlib import Path
from typing import List, Dict
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.fetcher import Fetcher
from src.logger import ScraperLogger


def parse_regional_rivers(html: str, base_url: str, region_name: str) -> List[Dict]:
    """
    Parse a regional 'where-to-fish' page to extract river links.
    
    These pages typically have rivers mentioned inline within paragraphs,
    like: "the <a href='/region/river'>River Name</a> river"
    
    Args:
        html: Raw HTML content
        base_url: Base URL for resolving relative links
        region_name: Name of the region (for context)
        
    Returns:
        List of dicts with keys: name, canonical_url, region
    """
    soup = BeautifulSoup(html, 'lxml')
    rivers = []
    seen_urls = set()
    
    # Strategy 1: Find all links in the main content area
    # Look for the page builder content div
    content_areas = [
        soup.find('div', class_=lambda c: c and 'builder' in c.lower()),
        soup.find('div', class_=lambda c: c and 'content' in c.lower()),
        soup.find('article'),
        soup.find('main'),
    ]
    
    content = None
    for area in content_areas:
        if area:
            content = area
            break
    
    if not content:
        content = soup  # Fall back to entire document
    
    # Find all links in content
    links = content.find_all('a', href=True)
    
    for link in links:
        href = link.get('href', '').strip()
        text = link.get_text().strip()
        
        # Skip empty or anchor-only links
        if not href or href in ['#', '']:
            continue
            
        # Convert relative URLs to absolute
        if not href.startswith('http'):
            canonical_url = urljoin(base_url, href)
        else:
            canonical_url = href
        
        # Only keep links that look like river pages
        # They typically contain the region name and look like river/stream names
        if region_name.lower().replace(' – ', '-').replace(' ', '-') not in canonical_url.lower():
            continue
            
        # Skip navigation links (where-to-fish pages)
        if '/where-to-fish/' in canonical_url:
            continue
            
        # Skip duplicates
        if canonical_url in seen_urls:
            continue
        seen_urls.add(canonical_url)
        
        # Extract river name from link text or URL
        # Link text might be "Waikato" or "Waipa river"
        name = text
        
        # If name is too short or generic, try to extract from URL
        if len(name) < 3 or name.lower() in ['river', 'stream', 'creek']:
            # Extract from URL: /auckland-waikato/waipa-river -> waipa-river
            url_parts = canonical_url.rstrip('/').split('/')
            if url_parts:
                name = url_parts[-1].replace('-', ' ').title()
        
        # Add "River" suffix if not present and looks like it should have it
        if 'river' not in name.lower() and 'stream' not in name.lower() and 'creek' not in name.lower():
            # Check context - if surrounding text mentions "river", add it
            parent_text = link.parent.get_text() if link.parent else ''
            if 'river' in parent_text.lower():
                name = name + ' River'
        
        rivers.append({
            'name': name,
            'canonical_url': canonical_url,
            'region': region_name,
            'slug': canonical_url.rstrip('/').split('/')[-1],
        })
    
    return rivers


def main():
    """Test the regional parser."""
    TEST_URL = "https://nzfishing.com/auckland-waikato/where-to-fish/"
    REGION_NAME = "Auckland-Waikato"
    
    # Initialize components
    config = Config()
    logger = ScraperLogger(config.log_path)
    fetcher = Fetcher(config, logger)
    
    print(f"\n{'='*80}")
    print(f"Testing Regional River Parser")
    print(f"URL: {TEST_URL}")
    print(f"Region: {REGION_NAME}")
    print(f"{'='*80}\n")
    
    # Fetch HTML
    print("Step 1: Fetching HTML...")
    try:
        html = fetcher.fetch(TEST_URL)
        print(f"✓ Fetched {len(html)} bytes\n")
    except Exception as e:
        print(f"✗ Fetch failed: {e}")
        return 1
    
    # Parse rivers
    print("Step 2: Parsing rivers...")
    try:
        rivers = parse_regional_rivers(html, TEST_URL, REGION_NAME)
        
        if rivers:
            print(f"✓ Found {len(rivers)} rivers:\n")
            for i, river in enumerate(rivers, 1):
                print(f"{i:2}. {river['name']:<30} -> {river['canonical_url']}")
        else:
            print("✗ No rivers found")
            return 1
            
    except Exception as e:
        print(f"✗ Parse failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print(f"\n{'='*80}")
    print("Test Complete!")
    print(f"{'='*80}\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
