# Quickstart: NZ Flyfishing Web Scraper

**Phase**: 1 — Design  
**Created**: 2025-11-30  
**Purpose**: Guide for developers to understand the system and run their first scraper.

---

## Overview

The NZ Flyfishing Web Scraper is a Python CLI tool that:
1. Discovers fly-fishing regions and rivers from nzfishing.com
2. Extracts detailed information (flies, regulations, conditions)
3. Stores everything in a local SQLite database
4. Generates PDF reports of river data
5. Respects robots.txt and rate-limits (3-second delays)

All data is collected from **public pages only**; no authentication or paywall bypass is attempted.

---

## Prerequisites

- Python 3.11+
- pip or poetry
- ~100MB disk space (for database + cache)
- Internet connection (for initial scrape only)

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/KreativZentrum/fly_fishing_log.git
cd fly_fishing_log
```

### 2. Set Up Python Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r config/requirements.txt
```

Expected packages:
- `requests` — HTTP fetching
- `beautifulsoup4` — HTML parsing
- `reportlab` — PDF generation
- `pyyaml` — Configuration
- `pytest` — Testing

---

## Directory Structure

```
fly_fishing_log/
├── src/
│   ├── __init__.py
│   ├── cli.py           # Main CLI entrypoint
│   ├── config.py        # Configuration loader
│   ├── fetcher.py       # HTTP fetching with rate limiting
│   ├── parser.py        # HTML parsing
│   ├── models.py        # Data models
│   ├── storage.py       # SQLite operations
│   ├── pdf_generator.py # PDF generation
│   └── logger.py        # Logging setup
├── config/
│   ├── nzfishing_config.yaml  # Configuration
│   └── requirements.txt         # Python dependencies
├── database/
│   └── schema.sql       # SQLite schema
├── templates/
│   └── river_report.html # Jinja2 PDF template
├── .output/             # Generated PDFs
├── .cache/              # HTML cache
├── logs/
│   └── scraper.log      # Request logs
└── tests/               # Test suite
```

---

## Configuration

### Edit `config/nzfishing_config.yaml`

```yaml
fetcher:
  base_url: "https://nzfishing.com"
  user_agent: "NZFlyfishingBot/1.0 (+https://github.com/KreativZentrum/fly_fishing_log)"
  request_delay: 3.0
  cache_dir: ".cache/nzfishing"
  cache_ttl: 86400

parser:
  selectors:
    region_index: "div.region-list a"  # Customize based on site structure
    river_list: "section#fishing-waters ul li"

pdf_generator:
  template_dir: "templates/"
  output_dir: ".output/"
```

---

## Quick Start Commands

### 1. Run Full Scrape (First Time)

**Discover all regions and rivers, extract details, populate database:**

```bash
python -m src.cli scrape --all
```

**Expected output:**
```
2025-11-30 12:00:00 [INFO] Starting full scrape...
2025-11-30 12:00:05 [INFO] Fetched region index: 20 regions found
2025-11-30 12:00:30 [INFO] Region: Northland - 15 rivers discovered
2025-11-30 12:01:00 [INFO] River: Waiterere River - details extracted (3 flies, 5 regulations)
...
2025-11-30 14:30:00 [INFO] Scrape complete: 20 regions, 5,234 rivers, 21,456 flies, 8,901 regulations
```

**Time estimate:** ~2 hours (respecting 3-second delays)

---

### 2. Run Incremental Scrape (Refresh Only)

**Re-scrape only updated pages; use cache:**

```bash
python -m src.cli scrape --refresh
```

**Expected output:**
```
2025-11-30 15:00:00 [INFO] Starting incremental scrape...
2025-11-30 15:00:05 [INFO] Using cache: 1,234 pages cached (cache hit rate: 85%)
2025-11-30 15:05:00 [INFO] Found 12 updated rivers; updating database
2025-11-30 15:06:00 [INFO] Scrape complete: 12 rivers updated
```

**Time estimate:** ~5–15 minutes (most pages cached)

---

### 3. Clear Cache

**Force re-fetch all pages (bypass cache):**

```bash
python -m src.cli cache --clear
python -m src.cli scrape --all
```

---

### 4. Query the Database

**List all regions:**

```bash
python -m src.cli query regions
```

**Output:**
```
ID | Name           | Slug         | Rivers
---+----------------+--------------+--------
1  | Northland      | northland    | 15
2  | Auckland       | auckland     | 8
3  | Waikato        | waikato      | 42
...
```

---

### 5. List Rivers in a Region

```bash
python -m src.cli query rivers --region northland
```

**Output:**
```
ID | Name                     | Region    | Flies | Regulations
---+--------------------------+-----------+-------+--------------
1  | Waiterere River          | Northland | 8     | 5
2  | Kawakawa River           | Northland | 6     | 4
...
```

---

### 6. Generate a PDF Report

**Generate PDF for a single river:**

```bash
python -m src.cli pdf --river-id 1 --output waiterere_report.pdf
```

**Output:**
```
2025-11-30 15:10:00 [INFO] Generating PDF for Waiterere River...
2025-11-30 15:10:02 [INFO] PDF saved to .output/waiterere_report.pdf
```

---

### 7. Generate Batch PDFs

**Generate PDFs for all rivers in a region:**

```bash
python -m src.cli pdf --region northland --output-dir .output/northland/
```

**Output:**
```
2025-11-30 15:15:00 [INFO] Generating 15 PDFs for Northland rivers...
2025-11-30 15:15:30 [INFO] 15 PDFs generated in .output/northland/
```

---

### 8. View Logs

**Check request logs (what was scraped, when, status codes):**

```bash
tail -f logs/scraper.log
```

**Output:**
```
2025-11-30T12:00:05Z | FETCH | https://nzfishing.com/where-to-fish | 200 | 3.002s | cache_miss
2025-11-30T12:00:08Z | FETCH | https://nzfishing.com/northland | 200 | 3.001s | cache_miss
2025-11-30T12:00:11Z | FETCH | https://nzfishing.com/northland/waiterere-river | 200 | 3.002s | cache_miss
...
```

---

## Usage Patterns

### Pattern 1: One-Time Full Scrape

```bash
# First time — build the database
python -m src.cli scrape --all

# Wait 2 hours...

# Query the database
python -m src.cli query regions
python -m src.cli query rivers --region northland

# Generate a PDF
python -m src.cli pdf --river-id 42 --output my_favorite_river.pdf
```

### Pattern 2: Periodic Updates (Weekly)

```bash
# Set up a cron job to run weekly:
# 0 3 * * 0 /path/to/fly_fishing_log/venv/bin/python -m src.cli scrape --refresh

# Or run manually:
python -m src.cli scrape --refresh  # Uses cache; takes ~5–10 min

# Check for new data
python -m src.cli query rivers --recent
```

### Pattern 3: Specific Region Deep Dive

```bash
# Scrape a specific region to save time
python -m src.cli scrape --region northland

# Query rivers in that region
python -m src.cli query rivers --region northland

# Generate PDF for each river
python -m src.cli pdf --region northland --zip northland_rivers.zip
```

---

## Compliance & Ethics

✅ **What This Tool Does Correctly:**
- Respects `robots.txt`
- Enforces 3-second delays between requests
- Uses a clear, identifiable User-Agent
- Logs all requests for inspection
- Stores data offline (no tracking, no upload)
- Includes raw HTML for transparency

⚠️ **Important Notes:**
- This tool is designed for **personal use only**.
- Do not use for commercial purposes without explicit permission from nzfishing.com.
- Do not bypass rate limits or robots.txt.
- Do not redistribute scraped data.

---

## Troubleshooting

### Issue: "Halted: 3+ consecutive 5xx errors"

**Cause**: The website is likely down or blocking the scraper.

**Solution**:
```bash
# Wait a few hours, then retry
sleep 3600
python -m src.cli scrape --refresh
```

### Issue: "HTTP 403 (Forbidden)"

**Cause**: The scraper's User-Agent was blocked, or a page disallows scraping.

**Solution**:
1. Check `robots.txt`:
   ```bash
   curl https://nzfishing.com/robots.txt
   ```
2. Update User-Agent in config if needed.
3. Check logs to see which page triggered the block.

### Issue: Database is Locked

**Cause**: Multiple instances trying to access the database simultaneously.

**Solution**: Ensure only one scraper instance is running. SQLite is single-writer; concurrent writes cause locks.

### Issue: "Cache Hit Rate Low"

**Cause**: Cache expired or was cleared.

**Solution**: Cache TTL defaults to 24 hours. Check cache age:
```bash
ls -lh .cache/nzfishing/
```

---

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

Run specific test:
```bash
pytest tests/unit/test_fetcher.py -v
pytest tests/integration/test_discovery_workflow.py -v
```

---

## Architecture & Design

See [../plan.md](../plan.md) for high-level design.  
See [../data-model.md](../data-model.md) for database schema.  
See [../contracts/](../contracts/) for detailed module interfaces.

---

## Next Steps

1. **First time?** Run `python -m src.cli scrape --all` and wait for completion.
2. **Explore the data**: `python -m src.cli query rivers --region northland`
3. **Generate PDFs**: `python -m src.cli pdf --river-id 1 --output my_river.pdf`
4. **Set up periodic updates**: Add a cron job to run `scrape --refresh` weekly.
5. **Customize**: Edit `config/nzfishing_config.yaml` to adjust delays, cache TTL, or output directories.

---

## Support

- **Logs**: Check `logs/scraper.log` for detailed request history.
- **Database queries**: Use `python -m src.cli query --help` for options.
- **Issues**: See the project README or file an issue on GitHub.

---

## Legal Notice

This tool is provided as-is for personal research and use only. Users are responsible for ensuring their use complies with nzfishing.com's Terms of Service and robots.txt. The maintainers assume no liability for misuse.

---

## Next Phase

Once you're comfortable with the tool, see [../tasks.md](../tasks.md) for implementation tasks and development workflow.
