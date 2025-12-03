"""
Example: Enhanced CLI with --regional-urls option

This shows how to add regional URL support to the existing CLI.py
without breaking existing functionality.

Key additions:
1. --regional-urls flag to enable regional mode
2. --url-file option to read URLs from file
3. Interactive URL input if no file provided
"""

# ADD TO src/cli.py:

def add_regional_arguments(parser):
    """Add regional scraping arguments to CLI parser."""
    regional_group = parser.add_argument_group('regional scraping')
    
    regional_group.add_argument(
        '--regional-urls',
        action='store_true',
        help='Scrape regional where-to-fish pages directly (bypasses main index)'
    )
    
    regional_group.add_argument(
        '--url-file',
        type=str,
        metavar='FILE',
        help='File containing regional URLs (one per line)'
    )
    
    regional_group.add_argument(
        '--urls',
        type=str,
        nargs='+',
        metavar='URL',
        help='Regional URLs to scrape (space-separated)'
    )


# USAGE EXAMPLES:

# Example 1: Interactive mode
# python -m src.cli scrape --regional-urls
# (then enter URLs when prompted)

# Example 2: From file
# python -m src.cli scrape --regional-urls --url-file regions.txt

# Example 3: Command line args
# python -m src.cli scrape --regional-urls --urls \
#   https://nzfishing.com/auckland-waikato/where-to-fish/ \
#   https://nzfishing.com/northland/where-to-fish/


# IMPLEMENTATION IN scrape_command():

def scrape_command_regional_mode(args, config, logger):
    """
    Enhanced scrape command with regional URL support.
    """
    from .regional_parser import RegionalParser
    
    storage = Storage(config.database_path, logger)
    fetcher = Fetcher(config, logger)
    parser = Parser(config)
    regional_parser = RegionalParser(config)
    
    # NEW: Regional URLs mode
    if args.regional_urls:
        logger.info("Regional URLs mode activated")
        
        # Collect URLs from various sources
        urls = []
        
        # Source 1: Command line --urls
        if args.urls:
            urls.extend(args.urls)
            print(f"Using {len(args.urls)} URLs from command line")
        
        # Source 2: File --url-file
        elif args.url_file:
            with open(args.url_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        urls.append(line)
            print(f"Loaded {len(urls)} URLs from {args.url_file}")
        
        # Source 3: Interactive input
        else:
            print("\nEnter regional page URLs (one per line).")
            print("Press Enter with no input to start scraping.\n")
            
            while True:
                url = input(f"URL {len(urls) + 1} (or Enter to finish): ").strip()
                if not url:
                    break
                urls.append(url)
        
        if not urls:
            print("No URLs provided. Exiting.")
            return
        
        # Process each regional URL
        total_rivers = 0
        
        for url in urls:
            print(f"\nProcessing: {url}")
            
            # Extract region info from URL
            region_name = extract_region_name_from_url(url)
            region_slug = extract_region_slug_from_url(url)
            
            # Fetch page
            try:
                html = fetcher.fetch(url, use_cache=not args.refresh)
                print(f"  ✓ Fetched {len(html):,} bytes")
            except Exception as e:
                logger.error(f"Failed to fetch {url}: {e}")
                print(f"  ✗ Fetch failed: {e}")
                continue
            
            # Parse rivers
            try:
                rivers = regional_parser.parse_regional_page(html, url, region_name)
                print(f"  ✓ Found {len(rivers)} rivers")
            except Exception as e:
                logger.error(f"Failed to parse {url}: {e}")
                print(f"  ✗ Parse failed: {e}")
                continue
            
            # Save to database
            try:
                # Insert region
                region_id = storage.insert_region(
                    name=region_name,
                    canonical_url=url,
                    slug=region_slug,
                    description=f"{region_name} region"
                )
                
                # Insert rivers
                inserted = 0
                for river in rivers:
                    river_id = storage.insert_river(
                        name=river['name'],
                        canonical_url=river['canonical_url'],
                        slug=river['slug'],
                        region_id=region_id
                    )
                    if river_id:
                        inserted += 1
                
                print(f"  ✓ Saved {inserted} rivers")
                total_rivers += inserted
                
            except Exception as e:
                logger.error(f"Failed to save data: {e}")
                print(f"  ✗ Database error: {e}")
                continue
        
        print(f"\n{'=' * 60}")
        print(f"Regional scraping complete: {total_rivers} total rivers")
        print(f"{'=' * 60}")
        
        return  # Skip normal scraping flow
    
    # EXISTING: Normal scraping flow (main index, etc.)
    # ... existing code continues here ...


# HELPER FUNCTIONS:

def extract_region_name_from_url(url: str) -> str:
    """
    Extract region name from regional URL.
    
    https://nzfishing.com/auckland-waikato/where-to-fish/
    -> Auckland-Waikato
    """
    parts = url.rstrip('/').split('/')
    try:
        idx = parts.index('where-to-fish')
        if idx > 0:
            slug = parts[idx - 1]
            return slug.replace('-', ' ').title()
    except ValueError:
        pass
    
    return "Unknown Region"


def extract_region_slug_from_url(url: str) -> str:
    """
    Extract region slug from regional URL.
    
    https://nzfishing.com/auckland-waikato/where-to-fish/
    -> auckland-waikato
    """
    parts = url.rstrip('/').split('/')
    try:
        idx = parts.index('where-to-fish')
        if idx > 0:
            return parts[idx - 1]
    except ValueError:
        pass
    
    if len(parts) > 3:
        return parts[3]
    
    return "unknown"


# FILE FORMAT for --url-file option:
"""
# regions.txt - Regional page URLs for NZ Flyfishing scraper

# North Island
https://nzfishing.com/northland/where-to-fish/
https://nzfishing.com/auckland-waikato/where-to-fish/
https://nzfishing.com/eastern-rotorua/where-to-fish/
https://nzfishing.com/taupo-turangi/where-to-fish/
https://nzfishing.com/hawkes-bay/where-to-fish/
https://nzfishing.com/taranaki/where-to-fish/
https://nzfishing.com/wellington/where-to-fish/

# South Island
https://nzfishing.com/nelson-marlborough/where-to-fish/
https://nzfishing.com/west-coast/where-to-fish/
https://nzfishing.com/north-canterbury/where-to-fish/
https://nzfishing.com/central-south-island/where-to-fish/
https://nzfishing.com/otago/where-to-fish/
https://nzfishing.com/southland/where-to-fish/
"""
