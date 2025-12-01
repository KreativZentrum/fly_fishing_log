# Architecture

## System Overview

The NZ Flyfishing Web Scraper is built on a modular, contract-driven architecture with strict separation of concerns.

## Core Principles

1. **Independence**: Modules interact only through defined interfaces
2. **Testability**: Each module can be tested in isolation
3. **Constitution Compliance**: All modules enforce constitutional articles
4. **Database-First**: Storage layer is the source of truth

## Module Diagram

```
┌─────────────┐
│    CLI      │ (Entry point, argument parsing)
└──────┬──────┘
       │
       ├─────────────────┬─────────────────┬──────────────┐
       │                 │                 │              │
       ▼                 ▼                 ▼              ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐  ┌──────────────┐
│   Config    │   │   Logger    │   │  Storage    │  │ PDFGenerator │
└─────────────┘   └─────────────┘   └─────────────┘  └──────────────┘
                         ▲                 ▲
                         │                 │
                         │                 │
                  ┌─────────────┐   ┌─────────────┐
                  │   Fetcher   │   │   Parser    │
                  └─────────────┘   └─────────────┘
```

## Module Responsibilities

### Config (`src/config.py`)
- Loads YAML configuration file
- Validates required fields and constraints
- Provides typed access to settings
- **Article 8 Compliance**: Centralized configuration

**Key Methods**:
- `__init__(config_path)`: Load and validate YAML
- Properties: `base_url`, `request_delay`, `database_path`, etc.

### Logger (`src/logger.py`)
- Structured JSON logging to file
- Human-readable console output
- Request/error/discovery event tracking
- **Article 9 Compliance**: Complete, parseable logs

**Key Methods**:
- `log_request(url, status_code, delay, cache_hit)`
- `log_halt(reason)`
- `log_discovery(entity_type, action)`

### Storage (`src/storage.py`)
- SQLite database wrapper
- CRUD operations for 6 entities
- Content hash tracking for change detection
- **Article 6 Compliance**: Raw data immutability

**Key Methods**:
- `initialize_schema()`: Create tables if not exist
- `insert_region()`, `get_regions()`, `get_uncrawled_regions()`
- `insert_river()`, `get_rivers_by_region()`
- `has_changed(entity_id, content_hash)`

**Database Schema**:
- `regions`: Name, slug, canonical_url (unique), raw_html
- `rivers`: region_id (FK), name, slug, canonical_url (unique), raw_html
- `sections`: river_id (FK), name, slug, raw_html
- `recommended_flies`: river_id (FK), section_id (nullable FK), name, raw_text, category, size, color
- `regulations`: river_id (FK), section_id (nullable FK), type, value, raw_text
- `metadata`: session_id, entity_id, entity_type, content hashes, crawl timestamps

### Fetcher (`src/fetcher.py`)
- HTTP client with requests.Session
- Robots.txt compliance checking
- Rate limiting (3-second minimum delay)
- Exponential backoff retry logic
- Cache management (MD5-keyed, TTL-based)
- **Article 2, 3 Compliance**: Polite crawling

**Key Methods**:
- `is_allowed(url)`: Check robots.txt
- `fetch(url, use_cache, refresh)`: Main fetch with rate limiting
- `clear_cache()`, `get_cache_stats()`

**Rate Limiting**:
- Tracks `_last_request_time`
- Sleeps to enforce 3-second minimum between requests
- Adds random jitter (0-0.5 seconds)

**Retry Logic**:
- Max retries: 3 (configurable)
- Backoff delays: [1, 2, 4, 8] seconds
- Resets on success
- Halts on 3 consecutive 5xx errors

**Caching**:
- Cache key: MD5(url)
- TTL: 24 hours (configurable)
- Directory: `.cache/nzfishing/`
- Automatic cleanup on `clear_cache()`

### Parser (`src/parser.py`)
- HTML parsing with BeautifulSoup4
- CSS selector-based extraction
- No inference (Article 5.2 compliance)
- **Implementation Status**: Stubs (Phase 3-5)

**Key Methods** (to be implemented):
- `parse_region_index(html)`: Extract region links
- `parse_region_page(html, region)`: Extract river links
- `parse_river_detail(html, river)`: Extract sections, flies, regulations
- `classify_fly(name, raw_text)`: Return nulls per Article 5.2

### PDFGenerator (`src/pdf_generator.py`)
- Template-driven PDF generation with ReportLab
- Database-only (no live scraping per Article 7)
- **Implementation Status**: Stub (Phase 8)

**Key Methods** (to be implemented):
- `generate_river_pdf(river_id, filename)`
- `generate_batch_pdfs(region_id, output_zip)`

### CLI (`src/cli.py`)
- Argparse-based command interface
- Routes to appropriate module workflows
- Error handling and user feedback

**Commands**:
- `scrape --all | --refresh | --region <id>`: Run scraper
- `query regions | rivers | river --river-id <id>`: Query database
- `cache --stats | --clear`: Manage cache
- `pdf --river-id <id> | --region <id>`: Generate PDFs

## Data Flow

### Scraping Workflow (Phase 3-5 implementation)

```
1. CLI invokes scrape command
2. Fetcher retrieves index page (with rate limiting)
3. Parser extracts region links
4. Storage inserts/updates regions
5. For each region:
   a. Fetcher retrieves region page
   b. Parser extracts river links
   c. Storage inserts/updates rivers
6. For each river:
   a. Fetcher retrieves river detail page
   b. Parser extracts sections, flies, regulations
   c. Storage inserts/updates all entities
   d. Logger records discovery events
```

### PDF Generation Workflow (Phase 8 implementation)

```
1. CLI invokes pdf command with river_id
2. Storage queries river + sections + flies + regulations
3. PDFGenerator loads Jinja2 template
4. Template renders with database data
5. ReportLab generates PDF file
6. Logger records PDF generation event
```

## Error Handling Strategy

### Fetcher Errors
- `FetchError`: HTTP errors (4xx, 5xx)
  - 4xx: Log and skip
  - 5xx: Retry with exponential backoff
  - 3 consecutive 5xx: Raise `HaltError`
- `HaltError`: Fatal errors requiring manual intervention
  - Logged with full context
  - Terminates scraper gracefully

### Parser Errors
- `ParserError`: Malformed HTML or unexpected structure
  - Log warning with URL and selector
  - Return empty results (don't fail entire scrape)

### Storage Errors
- `StorageError`: Database constraint violations or I/O errors
  - Log error with entity details
  - Transaction rollback for batch operations

### Configuration Errors
- `ConfigError`: Invalid YAML or missing required fields
  - Fail fast at startup
  - Clear error message to user

## Testing Strategy

### Unit Tests (`tests/unit/`)
- Test each module in isolation
- Mock all external dependencies
- Focus on edge cases and error handling

### Integration Tests (`tests/integration/`)
- Test module interactions
- Use test database and cache directories
- Verify data flow end-to-end

### Contract Tests (`tests/contract/`)
- Test against live/mock HTTP server
- Verify robots.txt compliance
- Validate rate limiting behavior
- Test retry logic and halt conditions

## Performance Considerations

### Rate Limiting Impact
- Minimum 3 seconds per request
- ~1,200 requests per hour maximum
- ~100 rivers takes ~5 minutes minimum

### Database Performance
- WAL mode for concurrent reads during scraping
- Indexes on foreign keys and canonical URLs
- Batch inserts for regions/rivers (transactions)

### Cache Effectiveness
- 24-hour TTL reduces re-fetching
- Hit rate visible via `cache --stats`
- Manual refresh via `--refresh` flag

## Constitution Article Mapping

| Article | Module(s) | Enforcement |
|---------|-----------|-------------|
| 2.1 Robots.txt | Fetcher | `is_allowed()` check before fetch |
| 2.2 User-Agent | Fetcher, Config | Set in Session headers |
| 3.1 Delay | Fetcher | `_enforce_rate_limit()` |
| 3.2 Backoff | Fetcher | Exponential retry delays |
| 3.3 Halt 5xx | Fetcher | `_consecutive_5xx_count` tracking |
| 3.5 Caching | Fetcher | MD5 cache with TTL validation |
| 5.2 No Inference | Parser | `classify_fly()` returns nulls |
| 6.3 Required Fields | Models | `__post_init__` validation |
| 6.4 Immutability | Storage | Upsert pattern, separate raw_html |
| 8.1 Config | Config | YAML with validation |
| 9.1-9.3 Logging | Logger | JSON lines with UTC timestamps |

## Future Enhancements

- [ ] Async fetching (aiohttp) for parallel region scraping
- [ ] Change detection (skip unchanged rivers based on hash)
- [ ] Incremental scraping (only new/updated rivers)
- [ ] CLI progress bars (tqdm)
- [ ] PDF templates with custom styling
- [ ] Database migration tool
- [ ] Web UI for querying/PDF generation
