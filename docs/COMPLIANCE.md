# Compliance Documentation

## Constitution Articles

The NZ Flyfishing Web Scraper follows an 11-article constitution ensuring ethical scraping and data integrity.

### Article 1: Purpose
Extract flyfishing data (regions, rivers, sections, flies, regulations) from nzfishing.com.

**Enforcement**: Scope limited to specified entities, no additional data collection.

---

### Article 2: Robots.txt Compliance

**2.1**: Fetch and parse `/robots.txt` before any scraping  
**2.2**: Identify with clear User-Agent: `nzfishing-scraper/1.0 (polite crawling; Article 2 compliant)`  
**2.3**: Halt immediately if any URL is disallowed

**Implementation**:
- **Module**: `src/fetcher.py`
- **Method**: `_load_robots_txt()` fetches `/robots.txt` on initialization
- **Method**: `is_allowed(url)` checks `RobotFileParser.can_fetch()` before every request
- **Exception**: Raises `FetchError` if disallowed, logged via `logger.log_disallow()`

**Testing**:
```python
# tests/contract/test_robots_compliance.py
def test_robots_disallow(test_fetcher):
    with pytest.raises(FetchError, match="disallowed"):
        test_fetcher.fetch("http://example.com/admin/")
```

---

### Article 3: Polite Crawling

**3.1**: Minimum 3-second delay between requests  
**3.2**: Exponential backoff on errors: [1, 2, 4, 8] seconds  
**3.3**: Halt on 3 consecutive 5xx errors  
**3.4**: Respect `Retry-After` header  
**3.5**: Cache responses with 24-hour TTL

**Implementation**:
- **Module**: `src/fetcher.py`
- **Method**: `_enforce_rate_limit()` sleeps to maintain 3-second minimum
- **Validation**: `src/config.py` raises `ConfigError` if `request_delay < 3.0`
- **Retry Logic**: Exponential backoff in `fetch()` method
- **Halt Logic**: `_consecutive_5xx_count` tracked, raises `HaltError` at threshold
- **Caching**: MD5-based cache with TTL validation in `_is_cache_valid()`

**Configuration**:
```yaml
request_delay: 3.0  # Minimum 3 seconds (validated)
jitter_max: 0.5     # Random 0-0.5 second jitter
retry_backoff: [1, 2, 4, 8]
halt_on_consecutive_5xx: 3
cache_ttl: 86400    # 24 hours
```

**Testing**:
```python
# tests/integration/test_rate_limiting.py
def test_3_second_delay(test_fetcher):
    start = time.time()
    test_fetcher.fetch("http://example.com/page1")
    test_fetcher.fetch("http://example.com/page2")
    elapsed = time.time() - start
    assert elapsed >= 3.0  # Minimum 3 seconds between requests
```

---

### Article 4: Error Handling

**4.1**: Classify errors (temporary vs fatal)  
**4.2**: Log all errors with context  
**4.3**: Continue on recoverable errors, halt on fatal

**Implementation**:
- **Exceptions**: `FetchError`, `HaltError`, `ConfigError`, `StorageError`, `ParserError`, `PDFError`
- **Logging**: All errors logged via `logger.error()` with URL, status_code, traceback
- **Fatal Errors**: 3 consecutive 5xx, robots.txt violations, config errors

---

### Article 5: No Inference

**5.1**: Store only explicitly stated facts  
**5.2**: Leave optional fields NULL if not present  
**5.3**: No encoding assumptions (preserve UTF-8, special chars)

**Implementation**:
- **Module**: `src/parser.py`
- **Method**: `classify_fly()` returns `(None, None, None)` for category/size/color unless explicitly in text
- **Database**: Optional columns (`category`, `size`, `color`) default NULL
- **Raw Text**: Always store `raw_text` field with exact source content

**Example**:
```python
# Article 5.2 compliant
fly_data = {
    'name': 'Royal Wulff',
    'raw_text': 'Royal Wulff size 12-16',  # Exact text
    'category': None,  # Not explicitly stated
    'size': None,      # Could infer "12-16" but Article 5.2 forbids
    'color': None      # Not stated
}
```

---

### Article 6: Data Immutability

**6.3**: Require non-empty values for required fields  
**6.4**: Never overwrite raw HTML content

**Implementation**:
- **Module**: `src/models.py`
- **Validation**: `__post_init__()` raises `ValueError` if `name` or `canonical_url` empty
- **Upsert Pattern**: `ON CONFLICT(canonical_url) DO UPDATE SET updated_at = CURRENT_TIMESTAMP` (raw_html not in UPDATE clause)
- **Content Hashing**: `metadata` table tracks `raw_content_hash` for change detection

**Storage Example**:
```python
# Upsert preserves raw_html
storage.insert_river(
    region_id=1,
    name="Tongariro River",
    canonical_url="http://example.com/river/tongariro",
    raw_html="<html>...</html>"  # Preserved, never overwritten
)
```

---

### Article 7: PDF Generation

**7.1**: Source data only from database  
**7.2**: Template-driven (no live scraping)  
**7.3**: Render HTML first, convert to PDF

**Implementation** (Phase 8):
- **Module**: `src/pdf_generator.py`
- **Method**: `generate_river_pdf(river_id)` queries storage, renders Jinja2 template, converts with ReportLab
- **No Network**: PDF generator never calls `fetcher.fetch()`

---

### Article 8: Centralized Configuration

**8.1**: Single YAML file for all settings  
**8.2**: Validate on load, fail fast

**Implementation**:
- **File**: `config/nzfishing_config.yaml`
- **Module**: `src/config.py`
- **Validation**: Checks `request_delay >= 3.0`, `base_url` format, required fields
- **Exception**: Raises `ConfigError` with clear message if invalid

**Required Settings**:
- `base_url`, `user_agent`, `request_delay`, `database_path`, `log_path`, `output_dir`, `discovery_rules`

---

### Article 9: Logging

**9.1**: Log all HTTP requests (URL, status, delay, cache hit)  
**9.2**: Log halt conditions (reason, timestamp)  
**9.3**: JSON format, UTC timestamps, no sensitive data

**Implementation**:
- **Module**: `src/logger.py`
- **Format**: JSON lines to `logs/scraper.log`, human-readable to console
- **Timestamp**: ISO 8601 UTC format: `2024-01-15T12:34:56.789Z`
- **Privacy**: No passwords, API keys, or personal data

**Log Example**:
```json
{
  "timestamp": "2024-01-15T12:34:56.789Z",
  "level": "INFO",
  "event": "request",
  "url": "http://nzfishing.com/river/tongariro",
  "method": "GET",
  "status_code": 200,
  "delay_seconds": 3.2,
  "cache_hit": false
}
```

---

### Article 10: Testing

**10.1**: Unit tests for all modules  
**10.2**: Integration tests for workflows  
**10.3**: Contract tests for robots.txt and rate limiting

**Implementation**:
- **Framework**: pytest with fixtures
- **Coverage**: `pytest --cov=src --cov-report=html`
- **CI**: `.github/workflows/ci.yml` runs all test suites on push

**Test Structure**:
- `tests/unit/`: Isolated module tests (mocked dependencies)
- `tests/integration/`: Module interaction tests (test database)
- `tests/contract/`: Live/mock server tests (robots.txt, rate limiting, retry logic)

---

### Article 11: Code Quality

**11.1**: PEP 8 compliance via flake8  
**11.2**: Auto-formatting via black  
**11.3**: Type hints for all functions

**Implementation**:
- **Linting**: `flake8 src/ tests/` (max-line-length=100, max-complexity=10)
- **Formatting**: `black src/ tests/` (line-length=100)
- **CI**: GitHub Actions runs flake8 and black checks on every push

**Configuration**:
```ini
# .flake8
[flake8]
max-line-length = 100
max-complexity = 10
ignore = E203, E266, E501, W503
```

```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py311']
```

---

## Robots.txt Policy

### Current nzfishing.com robots.txt
*(Hypothetical - will be fetched at runtime)*

```
User-agent: *
Disallow: /admin/
Disallow: /private/
Crawl-delay: 3
```

**Interpretation**:
- **Allowed**: Index page, region pages, river detail pages (no specific disallows)
- **Disallowed**: `/admin/`, `/private/` (scraper will never access)
- **Crawl-delay**: 3 seconds (matches our Article 3.1 minimum)

**Compliance Check**:
1. Fetcher loads robots.txt on initialization
2. Every `fetch()` call checks `is_allowed(url)` first
3. If disallowed, raises `FetchError` and logs to `scraper.log`
4. Scraper halts immediately per Article 2.3

---

## Verification Checklist

### Pre-Flight Checks (before scraping)
- [ ] `config/nzfishing_config.yaml` exists and is valid
- [ ] `request_delay >= 3.0` in config
- [ ] `database/schema.sql` applied (run `storage.initialize_schema()`)
- [ ] `logs/` directory writable
- [ ] `.cache/` directory exists (or will be created)

### Runtime Compliance Monitoring
- [ ] Check `logs/scraper.log` for robots.txt violations (`event: "disallow"`)
- [ ] Verify average delay between requests >= 3.0 seconds
- [ ] Check for halt events (`event: "halt"`) and investigate cause
- [ ] Monitor cache hit rate (`cache --stats`) for efficiency

### Post-Scrape Validation
- [ ] All regions have `crawl_timestamp` set
- [ ] All rivers have `region_id` foreign key
- [ ] No NULL in required fields (`name`, `canonical_url`, `raw_text`)
- [ ] Optional fields (`category`, `size`, `color`) are NULL unless explicitly stated
- [ ] Content hashes in `metadata` table match current `raw_html`

---

## Common Compliance Issues

### Issue: Request delay less than 3 seconds
**Cause**: `request_delay` set below 3.0 in config  
**Fix**: Edit `config/nzfishing_config.yaml`, set `request_delay: 3.0` or higher  
**Enforcement**: Config loader raises `ConfigError` at startup

### Issue: Robots.txt violations logged
**Cause**: Attempting to fetch disallowed URLs  
**Fix**: Review `logs/scraper.log` for `event: "disallow"`, fix discovery logic to exclude disallowed paths  
**Enforcement**: Fetcher raises `FetchError`, scraper halts

### Issue: Scraper halts on 5xx errors
**Cause**: 3 consecutive 5xx responses from server  
**Fix**: Wait and retry later (server may be down), check `Retry-After` header in logs  
**Enforcement**: Fetcher raises `HaltError` after threshold

### Issue: Inference in fly data
**Cause**: Parser setting `category` or `size` without explicit text  
**Fix**: Review `parse_river_detail()` logic, ensure `classify_fly()` returns nulls  
**Enforcement**: Article 5.2 validation in unit tests

### Issue: Raw HTML overwritten
**Cause**: Upsert query includes `raw_html` in UPDATE clause  
**Fix**: Remove `raw_html` from UPDATE in `insert_region()`, `insert_river()`  
**Enforcement**: Article 6.4 validation via content hash comparison

---

## Audit Trail

All compliance-critical events are logged to `logs/scraper.log`:

- **Robots.txt checks**: `event: "disallow"` with URL and reason
- **Rate limiting**: `event: "request"` with `delay_seconds`
- **Retries**: `event: "request"` with `status_code` and retry count
- **Halt conditions**: `event: "halt"` with reason (5xx threshold, robots violation)
- **Discovery**: `event: "discovery"` with entity type and action (INSERT/UPDATE/SKIP)

**Query Example**:
```bash
# Check for robots.txt violations
grep '"event": "disallow"' logs/scraper.log

# Verify all requests >= 3 seconds
jq 'select(.event == "request") | .delay_seconds' logs/scraper.log | awk '$1 < 3 {print "VIOLATION:", $0}'
```

---

## Contact and Reporting

For compliance questions or to report issues:
- **GitHub Issues**: [Repository issue tracker]
- **Email**: [Contact email]
- **Constitution**: See `.specify/specs/001-nzfishing-scraper/constitution.md`
