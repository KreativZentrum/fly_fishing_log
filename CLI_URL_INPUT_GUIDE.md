# CLI Regional URL Input - Complete Guide

## Overview

This approach allows you to provide regional "where-to-fish" page URLs directly to the scraper, bypassing the broken main index (Issue #3). You have multiple input methods to choose from.

## Input Methods

### Method 1: Interactive Input (Recommended for Testing)

```bash
python cli_regional_mode.py
```

**What happens:**
1. Script prompts for URLs one at a time
2. Enter each URL and press Enter
3. Press Enter with no input to start scraping
4. Script fetches, parses, and saves to database

**Example session:**
```
Enter regional page URLs (one per line).
Press Enter with no input to start scraping.

URL 1 (or Enter to finish): https://nzfishing.com/auckland-waikato/where-to-fish/
URL 2 (or Enter to finish): https://nzfishing.com/northland/where-to-fish/
URL 3 (or Enter to finish): [Enter]

Starting scrape of 2 regional page(s)
...
```

### Method 2: From File (Recommended for Production)

```bash
python cli_regional_mode.py regions_urls.txt
```

**File format (`regions_urls.txt`):**
```
# One URL per line, comments start with #
https://nzfishing.com/auckland-waikato/where-to-fish/
https://nzfishing.com/northland/where-to-fish/
https://nzfishing.com/eastern-rotorua/where-to-fish/
```

**Advantages:**
- Reusable - save your region list
- Version control - track which regions you're scraping
- Easy to update - add/remove regions as needed
- Batch processing - scrape all regions at once

### Method 3: Enhanced Main CLI (Future Integration)

Once integrated into `src/cli.py`:

```bash
# Interactive
python -m src.cli scrape --regional-urls

# From file
python -m src.cli scrape --regional-urls --url-file regions_urls.txt

# Command line args
python -m src.cli scrape --regional-urls --urls \
  https://nzfishing.com/auckland-waikato/where-to-fish/ \
  https://nzfishing.com/northland/where-to-fish/
```

## Complete Usage Examples

### Example 1: Scrape Auckland-Waikato Only

```bash
# Create single-region file
echo "https://nzfishing.com/auckland-waikato/where-to-fish/" > test_region.txt

# Scrape it
python cli_regional_mode.py test_region.txt
```

**Expected output:**
```
Processing: https://nzfishing.com/auckland-waikato/where-to-fish/
  Region: Auckland-Waikato (slug: auckland-waikato)
  ✓ Fetched 59,310 bytes
  ✓ Parsed 22 rivers
  ✓ Saved region + 22 new rivers to database

Results:
  - Processed: 1 URLs
  - Regions saved: 1
  - Rivers saved: 22
```

### Example 2: Scrape All North Island Regions

```bash
# Create North Island file
cat > north_island.txt << EOF
https://nzfishing.com/northland/where-to-fish/
https://nzfishing.com/auckland-waikato/where-to-fish/
https://nzfishing.com/eastern-rotorua/where-to-fish/
https://nzfishing.com/taupo-turangi/where-to-fish/
https://nzfishing.com/hawkes-bay/where-to-fish/
https://nzfishing.com/taranaki/where-to-fish/
https://nzfishing.com/wellington/where-to-fish/
EOF

# Scrape all
python cli_regional_mode.py north_island.txt
```

### Example 3: Scrape All Regions

```bash
# Use provided file with all 13 regions
python cli_regional_mode.py regions_urls.txt
```

**Time estimate:** ~40-50 seconds (13 regions × 3 second delay)

### Example 4: Interactive with Validation

```bash
python cli_regional_mode.py
```

```
URL 1 (or Enter to finish): nzfishing.com/auckland-waikato/where-to-fish/
  ⚠ Warning: URL should start with http:// or https://
  Use anyway? (y/n): n

URL 1 (or Enter to finish): https://nzfishing.com/auckland-waikato/where-to-fish/
URL 2 (or Enter to finish): [Enter]
```

## URL Format

### Correct Format
```
https://nzfishing.com/{region-slug}/where-to-fish/
```

### Valid Examples
```
✓ https://nzfishing.com/auckland-waikato/where-to-fish/
✓ https://nzfishing.com/northland/where-to-fish/
✓ http://nzfishing.com/otago/where-to-fish/  (http also works)
✓ https://nzfishing.com/west-coast/where-to-fish  (trailing slash optional)
```

### Invalid Examples
```
✗ nzfishing.com/auckland-waikato/where-to-fish/  (missing protocol)
✗ https://nzfishing.com/where-to-fish/  (missing region slug)
✗ https://nzfishing.com/auckland-waikato/  (missing where-to-fish)
```

## What Gets Scraped

For each URL:

1. **Region Data:**
   - Name (extracted from URL)
   - Slug (extracted from URL)
   - Canonical URL (the provided URL)
   - Description (auto-generated)

2. **River Data (per region):**
   - River names (extracted from page links)
   - Canonical URLs (full URLs to river pages)
   - Slugs (extracted from URLs)
   - Region association (foreign key)

## Database Structure

```
regions
├── id (auto-increment)
├── name (e.g., "Auckland-Waikato")
├── slug (e.g., "auckland-waikato")
├── canonical_url (e.g., "https://...")
└── description

rivers
├── id (auto-increment)
├── name (e.g., "Waipa river")
├── slug (e.g., "waipa-river")
├── canonical_url (e.g., "https://...")
└── region_id (foreign key -> regions.id)
```

## Checking Results

### Count regions
```bash
sqlite3 database/nzfishing.db "SELECT COUNT(*) FROM regions"
```

### List regions
```bash
sqlite3 database/nzfishing.db "SELECT name, slug FROM regions"
```

### Count rivers per region
```bash
sqlite3 database/nzfishing.db \
  "SELECT r.name, COUNT(rv.id) as river_count 
   FROM regions r 
   LEFT JOIN rivers rv ON r.id = rv.region_id 
   GROUP BY r.id 
   ORDER BY river_count DESC"
```

### Show rivers for specific region
```bash
sqlite3 database/nzfishing.db \
  "SELECT rv.name, rv.slug 
   FROM rivers rv 
   JOIN regions r ON rv.region_id = r.id 
   WHERE r.slug = 'auckland-waikato' 
   ORDER BY rv.name"
```

## Advantages of This Approach

### 1. **Works Around Issue #3**
- Main index `/where-to-fish/` is broken (returns 0 regions)
- Regional pages work perfectly
- No waiting for site fix

### 2. **Flexible Input**
- Interactive (quick testing)
- File-based (production use)
- Command-line args (scripting)

### 3. **Selective Scraping**
- Scrape only regions you care about
- Skip regions with known issues
- Easy to update/maintain list

### 4. **Transparent**
- See exactly which URLs being scraped
- Easy to debug URL-specific issues
- Clear progress tracking

### 5. **Compliant**
- Still respects robots.txt
- Still uses 3-second rate limiting
- Still caches HTML (24hr TTL)
- Still maintains data integrity

## Comparison with Auto-Discovery

| Aspect | Auto-Discovery (Broken) | URL Input (Working) |
|--------|------------------------|---------------------|
| **Setup** | None required | Maintain URL list |
| **Flexibility** | Discovers all regions | Choose which regions |
| **Reliability** | ❌ Currently broken | ✅ Working perfectly |
| **Site Changes** | ❌ Fails if structure changes | ✅ Only fails for changed regions |
| **Debugging** | Hard to troubleshoot | Easy - URL-specific |
| **Control** | All or nothing | Granular control |

## Production Workflow

### 1. Create Master URL File
```bash
# Copy provided template
cp regions_urls.txt my_regions.txt

# Edit to include only regions you want
vim my_regions.txt
```

### 2. Test with One Region
```bash
# Create test file
echo "https://nzfishing.com/auckland-waikato/where-to-fish/" > test.txt

# Test scrape
python cli_regional_mode.py test.txt

# Verify results
sqlite3 database/nzfishing.db "SELECT COUNT(*) FROM rivers"
```

### 3. Run Full Scrape
```bash
# Scrape all regions
python cli_regional_mode.py my_regions.txt

# Check results
sqlite3 database/nzfishing.db \
  "SELECT COUNT(*) as regions FROM regions; 
   SELECT COUNT(*) as rivers FROM rivers;"
```

### 4. Schedule Regular Updates
```bash
# Create cron job (daily at 2am)
0 2 * * * cd /path/to/project && python cli_regional_mode.py my_regions.txt
```

## Troubleshooting

### Problem: "No URLs provided"
**Solution:** Make sure file has valid URLs (not just comments)

### Problem: "Fetch failed"
**Solution:** Check internet connection, verify URL is correct

### Problem: "Parse failed"
**Solution:** URL structure may have changed, inspect HTML manually

### Problem: "Database error"
**Solution:** Check database file permissions, disk space

### Problem: Rate limiting
**Solution:** Normal - 3 second delay between requests is intentional

## Next Steps

1. **Test interactive mode**: `python cli_regional_mode.py`
2. **Test file mode**: `python cli_regional_mode.py regions_urls.txt`
3. **Verify database**: Check that regions and rivers are saved
4. **Integrate into main CLI**: Add `--regional-urls` support
5. **Document in main README**: Update user guide

## Files Reference

- **`cli_regional_mode.py`** - Standalone interactive CLI
- **`regions_urls.txt`** - Complete list of 13 regional URLs
- **`CLI_REGIONAL_INTEGRATION.py`** - Integration example for main CLI
- **`TEST_REGIONAL_SCRAPER.md`** - Technical documentation
