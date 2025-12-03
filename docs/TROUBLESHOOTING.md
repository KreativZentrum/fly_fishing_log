# Troubleshooting Guide

## Common Issues and Solutions

### Installation and Setup

#### Issue: `ModuleNotFoundError: No module named 'src'`
**Cause**: Not running from project root or virtual environment not activated

**Solution**:
```bash
# Ensure you're in project root
cd /path/to/fly_fishing_log

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate      # Windows

# Run as module
python -m src.cli --help
```

#### Issue: `FileNotFoundError: config/nzfishing_config.yaml`
**Cause**: Config file missing or wrong working directory

**Solution**:
```bash
# Check if config exists
ls config/nzfishing_config.yaml

# If missing, create from template
cp config/nzfishing_config.yaml.example config/nzfishing_config.yaml

# Run from project root
cd /path/to/fly_fishing_log
python -m src.cli query regions
```

#### Issue: `sqlite3.OperationalError: no such table: regions`
**Cause**: Database schema not initialized

**Solution**:
```python
from src.storage import Storage
from src.config import Config

config = Config('config/nzfishing_config.yaml')
storage = Storage(config.database_path)
storage.initialize_schema()  # Creates all tables
storage.close()
```

---

### Configuration Errors

#### Issue: `ConfigError: request_delay must be >= 3.0 (got 1.0)`
**Cause**: Article 3.1 compliance violation

**Solution**:
Edit `config/nzfishing_config.yaml`:
```yaml
request_delay: 3.0  # Minimum 3 seconds required
```

#### Issue: `ConfigError: Missing required field: base_url`
**Cause**: Invalid or incomplete YAML file

**Solution**:
Verify all required fields exist:
```yaml
base_url: "https://nzfishing.com"
user_agent: "nzfishing-scraper/1.0"
request_delay: 3.0
database_path: "database/nzfishing.db"
log_path: "logs/scraper.log"
output_dir: "pdfs/"
discovery_rules: { ... }
```

---

### Scraping Issues

#### Issue: `FetchError: URL disallowed by robots.txt`
**Cause**: Attempting to scrape disallowed path

**Solution**:
Check `logs/scraper.log` for disallowed URL:
```bash
grep '"event": "disallow"' logs/scraper.log
```

Verify robots.txt:
```bash
curl https://nzfishing.com/robots.txt
```

Do not scrape disallowed paths (Article 2.3).

#### Issue: `HaltError: 3 consecutive 5xx errors`
**Cause**: Server returning 503/500 errors repeatedly

**Solution**:
1. Check server status manually:
   ```bash
   curl -I https://nzfishing.com
   ```

2. Wait for server to recover (check `Retry-After` header)

3. Review `logs/scraper.log` for error details:
   ```bash
   grep '"event": "halt"' logs/scraper.log
   ```

4. Retry after waiting (Article 3.3 compliance):
   ```bash
   python -m src.cli scrape --refresh
   ```

#### Issue: Scraper taking too long (hours for 100 rivers)
**Cause**: 3-second delay per request (Article 3.1 requirement)

**Expected Time**:
- 100 rivers × 3 seconds = 300 seconds (~5 minutes minimum)
- Plus region pages, retry delays, network latency

**Optimizations**:
- Use caching (default 24-hour TTL):
  ```bash
  # First run: slow (fetches all)
  python -m src.cli scrape --all
  
  # Subsequent runs: fast (uses cache)
  python -m src.cli scrape --all
  ```

- Check cache hit rate:
  ```bash
  python -m src.cli cache --stats
  ```

#### Issue: `ParserError: Could not find selector 'div.river-list a'`
**Cause**: Website HTML structure changed

**Solution**:
1. Inspect current HTML structure:
   ```bash
   curl https://nzfishing.com/region/north-island | grep -A5 "river"
   ```

2. Update selectors in `config/nzfishing_config.yaml`:
   ```yaml
   discovery_rules:
     region_selector: "div.new-region-class a"  # Update this
     river_selector: ".new-river-class a"        # Update this
   ```

3. Test new selectors:
   ```bash
   python -m src.cli discover --regions
   ```

#### Issue: Region discovery returns 0 regions (Issue #3)
**Cause**: CSS selectors don't match actual site HTML structure at https://nzfishing.com/where-to-fish

**Current Selector**: `.region-list .region-item` (may not match live site)

**Solution**:
1. Inspect the actual HTML structure:
   ```bash
   curl -s https://nzfishing.com/where-to-fish | head -100
   ```

2. Find the correct selector by viewing page source in browser:
   - Visit https://nzfishing.com/where-to-fish
   - Right-click → "Inspect Element"
   - Find the container with region links
   - Note the class names and structure

3. Update `config/nzfishing_config.yaml`:
   ```yaml
   discovery_rules:
     region_selector: "YOUR_CORRECT_SELECTOR_HERE"
   ```

4. Common selector patterns to try:
   ```yaml
   region_selector: "div.region-list a"           # Direct links
   region_selector: ".fishing-regions .region a"  # Nested structure
   region_selector: "article.region h2 a"         # Semantic HTML
   region_selector: "[data-region] a"             # Data attributes
   ```

5. Test each selector:
   ```bash
   python -m src.cli discover --regions
   # Check output: "Found N regions"
   ```

**Note**: The parser was designed for a generic fishing site structure. The actual nzfishing.com site may use different CSS classes. This is a known limitation documented in Phase 9 validation report.
   ```

2. Update selectors in `config/nzfishing_config.yaml`:
   ```yaml
   discovery_rules:
     river_selector: "ul.river-links li a"  # New selector
   ```

3. Re-run scraper:
   ```bash
   python -m src.cli scrape --refresh
   ```

---

### Database Issues

#### Issue: `sqlite3.IntegrityError: UNIQUE constraint failed: rivers.canonical_url`
**Cause**: Attempting to insert duplicate river

**Expected Behavior**: Upsert should update, not fail

**Debug**:
```python
from src.storage import Storage

storage = Storage('database/nzfishing.db')

# Check for existing river
river = storage.get_river_by_canonical_url("http://example.com/river/test")
print(river)  # Should return existing record

# Upsert should work
storage.insert_river(
    region_id=1,
    name="Test River",
    canonical_url="http://example.com/river/test",  # Duplicate
    raw_html="<html>...</html>"
)  # Should update, not error
```

**Fix**: Verify `insert_river()` uses `ON CONFLICT(canonical_url) DO UPDATE`.

#### Issue: `sqlite3.OperationalError: database is locked`
**Cause**: Multiple processes accessing database simultaneously

**Solution**:
1. Close all open connections:
   ```python
   storage.close()
   ```

2. Enable WAL mode (should be default):
   ```sql
   PRAGMA journal_mode = WAL;
   ```

3. Avoid concurrent writes from multiple scripts.

#### Issue: Foreign key constraint failed
**Cause**: Inserting river with non-existent `region_id`

**Solution**:
```python
# Insert region first
region_id = storage.insert_region(
    name="Test Region",
    canonical_url="http://example.com/region/test",
    ...
)

# Then insert river with valid region_id
storage.insert_river(
    region_id=region_id,  # Valid FK
    name="Test River",
    ...
)
```

**Verify Foreign Keys**:
```python
import sqlite3
conn = sqlite3.connect('database/nzfishing.db')
cursor = conn.execute('PRAGMA foreign_keys')
print(cursor.fetchone())  # Should return (1,) for enabled
```

---

### Caching Issues

#### Issue: Getting stale data (HTML changed but cache still old)
**Cause**: Cache TTL not expired yet

**Solution**:
```bash
# Force refresh (ignore cache)
python -m src.cli scrape --refresh

# Or clear cache manually
python -m src.cli cache --clear
```

#### Issue: Cache directory taking too much space
**Cause**: Many cached HTML files accumulating

**Solution**:
```bash
# Check cache size
du -sh .cache/nzfishing/

# Clear old cache
python -m src.cli cache --clear

# Reduce TTL in config (default 24 hours)
```yaml
cache_ttl: 3600  # 1 hour instead of 24
```

---

### Logging Issues

#### Issue: No log file created
**Cause**: `logs/` directory doesn't exist or not writable

**Solution**:
```bash
# Create logs directory
mkdir -p logs

# Check permissions
ls -ld logs/  # Should be writable

# Verify log path in config
grep log_path config/nzfishing_config.yaml
```

#### Issue: Log file too large (GB size)
**Cause**: Long-running scraper with verbose logging

**Solution**:
```bash
# Rotate logs manually
mv logs/scraper.log logs/scraper.log.old
gzip logs/scraper.log.old

# Or implement log rotation (future enhancement)
```

#### Issue: Cannot parse JSON logs
**Cause**: Malformed JSON lines

**Debug**:
```bash
# Validate JSON
jq . logs/scraper.log  # Should parse without errors

# Find malformed lines
while read line; do
  echo "$line" | jq . > /dev/null 2>&1 || echo "Malformed: $line"
done < logs/scraper.log
```

---

### PDF Generation Issues (Phase 8)

#### Issue: `PDFError: PDF generation not yet implemented`
**Cause**: PDF feature not implemented yet (Phase 8)

**Status**: Stub implementation in `src/pdf_generator.py`

**Workaround**: Query database and export manually:
```python
from src.storage import Storage

storage = Storage('database/nzfishing.db')
river = storage.get_river(42)
flies = storage.get_flies_by_river(42)
regulations = storage.get_regulations_by_river(42)

# Manual export to text/HTML
print(f"River: {river['name']}")
print(f"Flies: {[f['name'] for f in flies]}")
print(f"Regulations: {[r['type'] + ': ' + r['value'] for r in regulations]}")
```

---

### Testing Issues

#### Issue: `pytest: command not found`
**Cause**: pytest not installed or virtual environment not activated

**Solution**:
```bash
# Activate virtual environment
source .venv/bin/activate

# Install test dependencies
pip install pytest pytest-cov pytest-mock

# Run tests
pytest tests/unit/ -v
```

#### Issue: Tests failing with `ModuleNotFoundError`
**Cause**: Running pytest from wrong directory

**Solution**:
```bash
# Run from project root
cd /path/to/fly_fishing_log
pytest tests/unit/ -v

# Or run as module
python -m pytest tests/unit/ -v
```

#### Issue: Integration tests hanging
**Cause**: Mock server not starting or port conflict

**Debug**:
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill conflicting process
kill -9 <PID>

# Run tests with verbose output
pytest tests/integration/ -v -s
```

---

### Performance Issues

#### Issue: Scraper using too much memory
**Cause**: Large HTML pages cached in memory

**Solution**:
1. Process regions in batches:
   ```bash
   # Scrape one region at a time
   python -m src.cli scrape --region 1
   python -m src.cli scrape --region 2
   ```

2. Clear cache between runs:
   ```bash
   python -m src.cli cache --clear
   ```

#### Issue: Database queries slow
**Cause**: Missing indexes or large dataset

**Debug**:
```sql
-- Check query plan
EXPLAIN QUERY PLAN SELECT * FROM rivers WHERE region_id = 1;

-- Should use index: idx_river_region_id
```

**Solution**:
1. Verify indexes exist:
   ```bash
   sqlite3 database/nzfishing.db ".schema rivers"
   ```

2. Re-create indexes if missing:
   ```sql
   CREATE INDEX IF NOT EXISTS idx_river_region_id ON rivers(region_id);
   ```

3. Vacuum database:
   ```bash
   sqlite3 database/nzfishing.db "VACUUM;"
   ```

---

## Debugging Tips

### Enable Verbose Logging
Edit `src/logger.py` to set console handler to DEBUG level:
```python
console_handler.setLevel(logging.DEBUG)  # Instead of INFO
```

### Check HTTP Requests
Use `curl` to manually fetch pages:
```bash
# Fetch with same User-Agent
curl -A "nzfishing-scraper/1.0" https://nzfishing.com/index.html
```

### Inspect Database
```bash
# Open SQLite shell
sqlite3 database/nzfishing.db

# List tables
.tables

# View schema
.schema rivers

# Count records
SELECT COUNT(*) FROM rivers;

# View recent crawls
SELECT name, crawl_timestamp FROM rivers ORDER BY crawl_timestamp DESC LIMIT 10;
```

### Monitor Cache Hit Rate
```bash
# Check cache stats periodically
watch -n 5 'python -m src.cli cache --stats'
```

### Validate Configuration
```python
from src.config import Config

try:
    config = Config('config/nzfishing_config.yaml')
    print("Config valid!")
    print(f"Base URL: {config.base_url}")
    print(f"Delay: {config.request_delay}s")
except Exception as e:
    print(f"Config error: {e}")
```

---

## Getting Help

### Check Logs First
```bash
# View recent errors
tail -100 logs/scraper.log | grep '"level": "ERROR"'

# View recent events
tail -50 logs/scraper.log | jq .
```

### Verify Environment
```bash
# Python version (requires 3.11+)
python --version

# Installed packages
pip list | grep -E '(requests|beautifulsoup4|pytest)'

# File structure
tree -L 2 -I '.venv|__pycache__'
```

### Report Issues
When reporting bugs, include:
1. Python version (`python --version`)
2. Operating system (macOS, Linux, Windows)
3. Full error traceback
4. Relevant logs from `logs/scraper.log`
5. Configuration file (redact sensitive info)
6. Steps to reproduce

### Constitution Violations
If scraper behaves unethically:
1. **Stop immediately**: `Ctrl+C` to halt
2. **Review logs**: Check for robots.txt violations
3. **Report**: Open GitHub issue with logs
4. **Do not run** until fixed

---

## FAQ

**Q: How long does a full scrape take?**  
A: Minimum 3 seconds per HTTP request (Article 3.1). For 100 rivers + 10 regions = 330 seconds (~5.5 minutes). Actual time depends on network latency and retry delays.

**Q: Can I reduce the delay to speed up scraping?**  
A: No. 3-second minimum is required by Article 3.1 and validated in config loader.

**Q: What if nzfishing.com is down?**  
A: Scraper will retry with exponential backoff, then halt after 3 consecutive 5xx errors (Article 3.3). Wait and retry later.

**Q: Can I run multiple scrapers in parallel?**  
A: Not recommended. Database locking issues and robots.txt rate limits. Use caching instead.

**Q: How do I know if scraper is respecting robots.txt?**  
A: Check logs for `event: "disallow"`. Should be zero violations. If any, scraper halts immediately.

**Q: Why are category/size/color NULL for flies?**  
A: Article 5.2 compliance. Only explicitly stated facts are stored. Raw text always preserved.

**Q: Can I export data to CSV?**  
A: Yes, using SQLite:
```bash
sqlite3 database/nzfishing.db -csv -header "SELECT * FROM rivers" > rivers.csv
```

**Q: How do I update the scraper for new website structure?**  
A: Update CSS selectors in `config/nzfishing_config.yaml` under `discovery_rules`, then re-scrape with `--refresh`.
