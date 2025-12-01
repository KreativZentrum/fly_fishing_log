# NZ Flyfishing Scraper - Quick Start Guide

**Legal Notice**: This scraper is provided for personal research and educational purposes only. Users must comply with all applicable laws, terms of service, and robots.txt directives. See [COMPLIANCE.md](COMPLIANCE.md) for full ethical guidelines.

---

## Installation

### Prerequisites
- Python 3.11 or higher
- pip package manager
- Virtual environment (recommended)

### Setup Steps

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/fly_fishing_log.git
cd fly_fishing_log

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify installation
python -m pytest tests/ -v
```

---

## Quick Start Commands

### 1. Discover All Fishing Regions

Scrape the regional index to discover all fishing regions in New Zealand:

```bash
python -m src.cli discover --regions
```

**Output**:
- Database: Populated `regions` table with ~20 regions
- Logs: Request timestamps in `logs/nzfishing.log`
- Duration: ~60 seconds (3-second delays between requests)

---

### 2. Discover Rivers in a Specific Region

After discovering regions, scrape rivers for a particular region:

```bash
# Example: Discover rivers in region ID 1 (e.g., "Northland")
python -m src.cli discover --rivers --region-id 1
```

**Output**:
- Database: Populated `rivers` table with rivers for that region
- Logs: All HTTP requests logged with timestamps
- Duration: Varies by number of rivers (~3 seconds per river)

---

### 3. Discover Rivers in All Regions

Batch-discover rivers across all regions:

```bash
python -m src.cli discover --rivers --all
```

**Output**:
- Database: Rivers for all regions
- Logs: Complete audit trail
- Duration: Several minutes (polite crawling enforced)

---

### 4. Extract Detailed River Information

Scrape detailed pages for individual rivers:

```bash
# Extract details for river ID 5
python -m src.cli scrape-details --river-id 5

# Extract details for all rivers in region 1
python -m src.cli scrape-details --region-id 1

# Extract details for all rivers
python -m src.cli scrape-details --all
```

**Output**:
- Database: `flies`, `regulations`, `sections` tables populated
- Logs: Parsing results and field extractions
- Duration: ~3 seconds per river detail page

---

### 5. View Cached Data

Check caching statistics to see how much bandwidth you've saved:

```bash
python -m src.cli cache --stats
```

**Output**:
```
Cache Statistics:
  Total Requests: 45
  Cache Hits: 12
  Cache Misses: 33
  Hit Rate: 26.7%
  Bytes Cached: 1.2 MB
```

---

### 6. Clear Cache

Remove all cached HTML to force fresh scraping:

```bash
python -m src.cli cache --clear
```

**Warning**: This will delete all cached files. Subsequent scrapes will hit the server again.

---

### 7. Query Database

Use SQLite to query the scraped data:

```bash
# Open SQLite console
sqlite3 data/nzfishing.db

# Example queries:
SELECT COUNT(*) FROM regions;
SELECT name, slug FROM regions LIMIT 5;
SELECT COUNT(*) FROM rivers WHERE region_id = 1;
SELECT * FROM flies WHERE river_id = 10;
```

---

### 8. Run Tests

Validate the scraper functionality:

```bash
# Run all tests
pytest tests/ -v

# Run specific test suites
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/contract/ -v

# Run with coverage
pytest --cov=src --cov-report=term-missing
```

---

## Usage Patterns

### Pattern 1: Full Scrape (Initial Run)

For the first time, scrape everything systematically:

```bash
# Step 1: Discover regions
python -m src.cli discover --regions

# Step 2: Discover all rivers
python -m src.cli discover --rivers --all

# Step 3: Extract details for all rivers
python -m src.cli scrape-details --all
```

**Duration**: 30-60 minutes (depending on site size)  
**Result**: Complete database with regions, rivers, flies, regulations

---

### Pattern 2: Periodic Refresh

Update existing data periodically (e.g., monthly):

```bash
# Re-scrape with cache enabled (default)
# Only changed pages will be re-fetched
python -m src.cli discover --regions
python -m src.cli discover --rivers --all
python -m src.cli scrape-details --all --refresh
```

**Duration**: 5-10 minutes (most requests use cache)  
**Result**: Updated data without redundant network requests

---

### Pattern 3: Regional Deep Dive

Focus on a specific region for detailed analysis:

```bash
# Step 1: Discover all regions (if not already done)
python -m src.cli discover --regions

# Step 2: Find region ID
sqlite3 data/nzfishing.db "SELECT id, name FROM regions WHERE name LIKE '%Waikato%';"

# Step 3: Deep dive into that region
python -m src.cli discover --rivers --region-id 3
python -m src.cli scrape-details --region-id 3
```

**Duration**: 2-5 minutes (targeted scraping)  
**Result**: Comprehensive data for one region

---

## Compliance & Ethics

### Robots.txt Compliance

The scraper automatically:
- Loads `robots.txt` on startup
- Respects `Disallow:` directives
- Logs disallowed URLs without fetching them

```bash
# Check robots.txt compliance in logs
grep "disallowed" logs/nzfishing.log
```

---

### Rate Limiting (Polite Crawling)

**Enforced Delays**:
- 3-second delay between all HTTP requests (Article 2)
- Exponential backoff on errors (1s, 2s, 4s)
- Halt on 3+ consecutive 5xx errors

**Cache Optimization**:
- Cached responses bypass rate limiting (instant)
- Default TTL: 24 hours
- Use `--refresh` flag to force re-fetch

---

### Ethical Guidelines

1. **Personal Use Only**: Do not scrape for commercial purposes
2. **Respect Rate Limits**: Never disable the 3-second delay
3. **Monitor Logs**: Check for errors and halt conditions
4. **Minimal Impact**: Use caching to avoid redundant requests
5. **Halt on Errors**: The scraper stops on persistent 5xx errors

For full compliance documentation, see [COMPLIANCE.md](../COMPLIANCE.md).

---

## Troubleshooting

### Issue 1: "Connection Refused" Errors

**Symptom**:
```
urllib.error.URLError: <urlopen error [Errno 61] Connection refused>
```

**Causes**:
- Site is down or blocking requests
- Network connectivity issues
- Invalid base URL in config

**Solutions**:
1. Check site accessibility in browser
2. Verify `base_url` in `config/nzfishing_config.yaml`
3. Wait 5-10 minutes and retry (temporary outage)
4. Check logs for 403/429 status codes (rate limiting)

---

### Issue 2: "HaltError: 3+ Consecutive 5xx Errors"

**Symptom**:
```
src.exceptions.HaltError: Halting: 3+ consecutive 5xx errors
```

**Cause**:
- Server is experiencing errors (503, 500, 502)
- Scraper halts to avoid overwhelming the server

**Solutions**:
1. Wait 30-60 minutes before retrying
2. Check site status in browser
3. Reduce scraping scope (one region at a time)
4. Clear cache if stale: `python -m src.cli cache --clear`

---

### Issue 3: No Data Extracted

**Symptom**:
- Commands run successfully
- Database tables are empty or missing expected data

**Causes**:
- Site HTML structure changed
- CSS selectors in config outdated
- Parser logic needs updating

**Solutions**:
1. Inspect HTML manually:
   ```bash
   curl -A "test-scraper/1.0" https://example.com/region/test
   ```
2. Update selectors in `config/nzfishing_config.yaml`
3. Check parser logic in `src/parser.py`
4. Run unit tests: `pytest tests/unit/test_parser* -v`

---

### Issue 4: Slow Scraping Performance

**Symptom**:
- Scraping takes hours to complete
- Each request takes exactly 3 seconds

**Causes**:
- Rate limiting enforced (expected behavior)
- Cache not being used (TTL expired or disabled)

**Solutions**:
1. Enable caching (default):
   ```bash
   python -m src.cli scrape-details --all  # Uses cache
   ```
2. Check cache stats:
   ```bash
   python -m src.cli cache --stats
   ```
3. Increase cache TTL in config (default 24 hours):
   ```yaml
   cache_ttl: 86400  # seconds
   ```
4. **Do NOT disable rate limiting** - this violates ethical guidelines

---

### Issue 5: Database Locked Errors

**Symptom**:
```
sqlite3.OperationalError: database is locked
```

**Causes**:
- Multiple processes accessing database simultaneously
- Previous process didn't close connection properly

**Solutions**:
1. Close all other scraper processes
2. Close SQLite console sessions
3. Check for orphaned processes:
   ```bash
   ps aux | grep python
   ```
4. If persistent, restart:
   ```bash
   pkill -9 python
   python -m src.cli discover --regions  # Retry
   ```

---

## Testing Instructions

### Run All Tests

```bash
# Full test suite with coverage
pytest --cov=src --cov-report=term-missing --cov-report=html

# View coverage report in browser
open htmlcov/index.html
```

### Test Categories

1. **Unit Tests** (`tests/unit/`):
   - Parser logic
   - Storage operations
   - Logger formatting
   - Cache TTL validation

2. **Integration Tests** (`tests/integration/`):
   - End-to-end workflows
   - Database integrity
   - Caching behavior
   - Rate limiting enforcement

3. **Contract Tests** (`tests/contract/`):
   - Robots.txt compliance
   - Rate limiting contracts
   - Error handling

### Expected Coverage

**Target**: ≥80% code coverage on `src/` modules

**Current Coverage** (as of Phase 9):
- `src/fetcher.py`: ~91%
- `src/parser.py`: ~83%
- `src/logger.py`: ~83%
- `src/storage.py`: ~80%
- `src/exceptions.py`: 100%

---

## Configuration Reference

### Config File: `config/nzfishing_config.yaml`

```yaml
# Base URL for scraping
base_url: "https://fishandgame.org.nz"

# User agent string (identify yourself)
user_agent: "nzfishing-scraper/1.0 (educational/personal use)"

# Rate limiting (seconds)
request_delay: 3.0
jitter_max: 0.5

# Caching
cache_dir: "cache/"
cache_ttl: 86400  # 24 hours

# Retry logic
max_retries: 3
retry_backoff: [1, 2, 4]  # Exponential backoff (seconds)
halt_on_consecutive_5xx: 3

# Paths
database_path: "data/nzfishing.db"
log_path: "logs/nzfishing.log"
output_dir: "output/"

# Discovery rules (CSS selectors)
discovery_rules:
  index_path: "/fishing-locations"
  region_selector: "div.region-list a"
  river_selector: ".fishing-waters a"
  detail_selectors:
    name: "h1.river-name"
    description: "div.description"
    flies: "div.recommended-flies li"
    regulations: "div.regulations p"
```

---

## Next Steps

1. **Read Documentation**:
   - [README.md](../README.md): Project overview
   - [ARCHITECTURE.md](ARCHITECTURE.md): System design
   - [DATABASE.md](DATABASE.md): Schema reference
   - [COMPLIANCE.md](COMPLIANCE.md): Ethical guidelines

2. **Customize Scraper**:
   - Update `base_url` for different sites
   - Modify CSS selectors in config
   - Extend parser for new fields

3. **Analyze Data**:
   - Export to CSV: `sqlite3 -header -csv data/nzfishing.db "SELECT * FROM rivers;" > rivers.csv`
   - Visualize fly patterns, regulations, etc.
   - Integrate with mapping tools (GIS)

4. **Contribute**:
   - Report bugs via GitHub Issues
   - Submit parser improvements
   - Share config for other fishing sites

---

## Support

For issues, questions, or contributions:
- **GitHub Issues**: [github.com/youruser/fly_fishing_log/issues](https://github.com/youruser/fly_fishing_log/issues)
- **Documentation**: See `docs/` directory
- **Tests**: Run `pytest -v` to validate changes

---

**Remember**: Scrape responsibly, respect rate limits, and comply with terms of service. Happy fishing! 🎣
