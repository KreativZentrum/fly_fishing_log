# Auckland-Waikato Regional Scraper Test

This is a test implementation for scraping regional "where-to-fish" pages from nzfishing.com, specifically targeting pages like:

**https://nzfishing.com/auckland-waikato/where-to-fish/**

## Overview

The main scraper targets the top-level regions index page at `https://nzfishing.com/where-to-fish/` which currently returns 0 regions (Issue #3). This test version demonstrates scraping at the regional level instead.

## Key Differences from Main Scraper

### 1. **HTML Structure**
- **Main Index**: Expects region links in a structured list (`.region-list .region-item`)
- **Regional Pages**: Contains inline river links within paragraph text

Example from Auckland-Waikato page:
```html
<p>The Auckland Waikato region is dominated by four major river systems:
• the <a href="/auckland-waikato/waipa-river">Waipa river</a>
• the <a href="/auckland-waikato/whanganui-river">Whanganui river</a>
...
</p>
```

### 2. **Parser Logic**
- **New Module**: `src/regional_parser.py` - Handles regional page structure
- **Inline Links**: Extracts links from within content paragraphs
- **Context-Aware**: Uses surrounding text to determine if link is "river", "stream", etc.

## Files

| File | Description |
|------|-------------|
| `src/regional_parser.py` | Parser for regional where-to-fish pages |
| `test_auckland_waikato.py` | Complete test script with multiple modes |
| `test_regional_parser.py` | Focused parser testing |
| `test_region_scrape.py` | HTML structure analysis tool |

## Usage

### 1. Display Only (No Database)
```bash
python test_auckland_waikato.py
```

**Output**: Lists all 22 rivers found on the Auckland-Waikato page

### 2. Save to Database
```bash
python test_auckland_waikato.py --save
```

**Output**: 
- Saves region record to `regions` table
- Saves 22 river records to `rivers` table with proper foreign keys
- Uses `INSERT OR IGNORE` for idempotency

### 3. Fetch Sample River Detail
```bash
python test_auckland_waikato.py --fetch-one
```

**Output**:
- Lists rivers
- Fetches first river's detail page (Waipa River)
- Displays preview of page content

## Results

When run against `https://nzfishing.com/auckland-waikato/where-to-fish/`:

```
✓ Found 22 rivers:

  1. Waipa river                         waipa-river
  2. Whanganui river                     whanganui-river
  3. Waihou river                        waihou-river
  4. Waimiha Stream                      AWWaimiha.htm
  5. Whakapapa River                     AWWhakapapa.htm
  6. Whanganui River                     AWWhanganui.htm
  7. Waihou River                        AWWaihou.htm
  8. Waimakariri Stream                  AWWaimakariri.htm
  9. Ohinemuri River                     AWOhinemuri.htm
 10. Lake Pupuke                         AWPupuke.htm
 11. Wairoa River                        wairoa-river
 12. Parkinsons Lake                     parkinsons-lake
 13. Lake Whatihua (Thomsons)            lake-whatihua
 14. Mangatangi Reservoir                mangatangi-reservoir
 15. Mangatawhiri Reservoir              mangatawhiri-reservoir
 16. Ohinmuri River                      ohinmuri-river
 17. Waitewheta River                    waitewheta-river
 18. Kauaeranga River                    kauaeranga-river
 19. Tairua River                        tairua-river
 20. Waiwawa River                       waiwawa-river
 21. Kauaeranga River                    AWKauaeranga.htm
 22. Waiwawa, River                      AWWaiwawa.htm
```

## Database Schema

The test uses the existing database schema:

```sql
-- Regions table
INSERT INTO regions (name, canonical_url, slug, description)
VALUES ('Auckland-Waikato', 'https://nzfishing.com/auckland-waikato/', 
        'auckland-waikato', 'Auckland-Waikato region');

-- Rivers table (example)
INSERT INTO rivers (name, canonical_url, slug, region_id)
VALUES ('Waipa river', 'https://nzfishing.com/auckland-waikato/waipa-river',
        'waipa-river', 1);
```

## Technical Details

### RegionalParser Class

Located in `src/regional_parser.py`:

**Methods**:
- `parse_regional_page(html, page_url, region_name)` - Main parsing method
- `_find_content_area(soup)` - Locates main content div
- `_is_river_link(url, region_name)` - Filters river/water body links
- `_extract_river_name(link, url)` - Cleans and formats river names

**Features**:
- Handles both relative and absolute URLs
- Deduplicates by canonical URL
- Adds type suffixes (River, Stream, Lake) based on context
- Extracts slugs from URLs or link attributes

### Compliance

Maintains all Article compliance from main scraper:

- **Article 2**: robots.txt checking (inherited from Fetcher)
- **Article 3**: 3-second rate limiting (inherited from Fetcher)
- **Article 5**: No inference - extracts only explicit content
- **Article 6**: Raw HTML caching (inherited from Fetcher)
- **Article 8**: Centralized configuration

## Integration with Main Scraper

To integrate this into the main scraper:

### Option 1: Fallback Strategy
```python
# Try main index first
regions = parser.parse_region_index(html)

if not regions:
    # Fall back to known regional pages
    regional_urls = [
        'https://nzfishing.com/auckland-waikato/where-to-fish/',
        'https://nzfishing.com/northland/where-to-fish/',
        # ... etc
    ]
    for url in regional_urls:
        html = fetcher.fetch(url)
        rivers = regional_parser.parse_regional_page(html, url, region_name)
```

### Option 2: Two-Stage Scraper
```python
# Stage 1: Hard-coded regional pages
regional_pages = get_known_regional_pages()

for region_name, url in regional_pages.items():
    rivers = scrape_regional_page(url, region_name)
    
# Stage 2: Try to discover additional regions
additional_regions = try_discover_from_main_index()
```

## Limitations

1. **URL Consistency**: Mix of `/river-name/` and `/AWRiver.htm` formats
2. **Duplicates**: Some rivers listed twice (different URLs, same river)
3. **Manual Region List**: Would need to maintain list of regional page URLs
4. **No Auto-Discovery**: Doesn't solve Issue #3 (main index returns 0 regions)

## Next Steps

1. **Expand to Other Regions**: Test with other regional pages (Northland, Taranaki, etc.)
2. **Deduplication Logic**: Handle rivers with multiple URLs
3. **River Detail Parser**: Add parsing for individual river detail pages
4. **CLI Integration**: Add `--regional-mode` flag to main CLI
5. **Configuration**: Add regional page URLs to config file

## Testing

Run all test modes:
```bash
# Basic test
python test_auckland_waikato.py

# With database save
python test_auckland_waikato.py --save

# With sample fetch
python test_auckland_waikato.py --fetch-one

# Analyze structure
python test_region_scrape.py

# Test parser only
python test_regional_parser.py
```

Check database contents:
```bash
sqlite3 database/nzfishing.db
sqlite> SELECT * FROM regions;
sqlite> SELECT name, slug FROM rivers WHERE region_id = 1;
sqlite> .quit
```

## Notes

- All HTTP requests respect 3-second rate limiting
- Uses caching (24hr TTL) for faster repeated runs
- Raw HTML saved to `cache/` directory
- Database saves are idempotent (safe to re-run)

## Author

Test implementation created for NZ Flyfishing Web Scraper project.
Demonstrates alternative scraping strategy for regional pages.
