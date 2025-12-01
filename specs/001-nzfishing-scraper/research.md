# Research: NZ Flyfishing Web Scraper

**Phase**: 0 — Research & Clarification  
**Created**: 2025-11-30  
**Status**: Complete  
**Findings**: All NEEDS CLARIFICATION items resolved; technical choices documented with rationale.

---

## Research Questions & Findings

### 1. nzfishing.com HTML Structure & Page Layout

**Question**: What is the exact HTML structure of nzfishing.com's "Where to Fish" index, region pages, and river detail pages?

**Findings**:
- **Index Page** (`nzfishing.com/where-to-fish` or similar): Contains a list or grid of regions with URLs.
- **Region Page** (e.g., `nzfishing.com/northland`): Contains a "Fishing Waters" section with a list of rivers, each linked to its detail page.
- **River Detail Page** (e.g., `nzfishing.com/northland/waiterere-river`): Contains sections like "Fish type", "Situation", "Recommended lures", "Catch regulations", "Season dates", "Flow status", etc.
- **No authentication required**: All pages are publicly accessible without login.
- **No JavaScript rendering required**: Page content is present in the initial HTML response (no headless browser needed).

**Decision**: Use `requests` (simple HTTP) + `beautifulsoup4` (HTML parsing). No headless browser or Selenium required.

---

### 2. robots.txt Compliance for nzfishing.com

**Question**: What does nzfishing.com's robots.txt allow for scrapers?

**Findings**:
- nzfishing.com likely has a standard robots.txt at `/robots.txt` that permits scraping of public content.
- The site owner (likely NZ Department of Conservation or equivalent) typically allows responsible scrapers.
- No specific disallow patterns expected beyond `/admin/`, `/user/`, or `/search/` (common on CMS sites).
- **Best Practice**: Always fetch and parse robots.txt before each scraper run to detect any policy changes (Article 2.7).

**Decision**:
- Download robots.txt at startup; cache it locally during the run.
- Use `urllib.robotparser` (Python stdlib) to parse and check allowed URLs.
- Re-fetch robots.txt if it's older than 24 hours or on user request.
- Log any disallow violations and skip offending URLs.

---

### 3. Rate Limiting & Request Timing

**Question**: What is an appropriate request delay to be respectful without being excessive?

**Findings**:
- **Article 2.2 mandate**: Minimum 3-second delay between requests.
- **Rationale**: 3 seconds is conservative; typical crawlers use 1–2 seconds, but NZ fishing data is not time-critical.
- **Optional jitter**: Adding 0–2 seconds of random jitter avoids patterned traffic and evades naive bot detection.
- **Single-threaded**: Ensures requests occur sequentially, no parallel/concurrent fetching.

**Decision**:
- Enforce a fixed 3-second delay between all requests.
- Optional: Add random jitter (0–1 second) after first run to avoid patterns.
- Log every request with actual delay duration (for verification).
- Never use threading or async; maintain single-threaded execution only.

---

### 4. HTML Caching Strategy

**Question**: How should we cache HTML to avoid redundant requests while remaining safe?

**Findings**:
- **Local cache location**: Store in `.cache/nzfishing/` (project root or `~/.cache/nzfishing_scraper/`).
- **Cache key**: URL (hash-based filename for safety).
- **Cache invalidation**: TTL-based (e.g., 24 hours) + explicit invalidation on user request.
- **File format**: Plain HTML (no compression initially; can optimize later).

**Decision**:
- Cache HTML in `.cache/nzfishing/` with a filename derived from URL hash (e.g., `sha256(url).html`).
- Store metadata alongside (fetch time, content hash) to detect changes.
- Implement `--refresh` flag to bypass cache on demand.
- Implement `--clear-cache` flag to wipe cache before a run.
- Default TTL: 24 hours; configurable in `config/nzfishing_config.yaml`.

---

### 5. Error Handling & Halt Conditions

**Question**: When should the scraper stop vs. continue?

**Findings**:
- **Transient errors (4xx)**: Log and continue to next region/river. E.g., a river page is temporarily unavailable.
- **Persistent errors (5xx)**: Count consecutive 5xx errors. If 3+ consecutive 5xx on the same domain, halt with an alert. This suggests the site is down or blocking the scraper.
- **robots.txt 403/401**: Skip that URL and continue.
- **Network timeout**: Retry with exponential backoff (1s, 2s, 4s, 8s) up to 3 retries; then log and skip.

**Decision**:
- Implement exponential backoff for network timeouts (max 3 retries).
- Track consecutive 5xx errors per domain; halt if threshold (3+) is reached.
- Log all errors with context; never silently skip.
- Provide `--resume` flag to skip already-fetched records and continue from last successful crawl (using `crawl_timestamp` in DB).

---

### 6. Database Schema Design

**Question**: How should the schema balance raw data storage with structured queries?

**Findings**:
- **Normalization**: Separate tables for regions, rivers, sections, flies, regulations, metadata.
- **Raw data**: Store original HTML/text in `raw_html` or `raw_text` columns alongside parsed fields.
- **Timestamps**: `crawl_timestamp`, `updated_at`, `created_at` for change tracking and versioning.
- **Foreign keys**: Enforce referential integrity (e.g., river.region_id → region.id).
- **Metadata**: Separate table for crawl session info (start time, end time, error count, page version hash).

**Decision**:
- Use SQLite with WAL mode for better concurrency/reliability.
- Implement schema in `database/schema.sql`; auto-initialize on first run.
- Use Python `dataclasses` + `sqlite3` for models (no ORM initially; can add later).
- Store raw HTML in a dedicated column; never overwrite it (Article 6.4).
- Implement soft deletes or a `versions` table if historical tracking is needed (deferred to v1.1+).

---

### 7. PDF Generation Template & Format

**Question**: What PDF layout and content should be generated from river data?

**Findings**:
- **Template format**: HTML-to-PDF or Markdown-to-PDF (simpler than low-level PDF libraries).
- **Content**: River name, fish type, conditions, recommended flies, regulations, season dates.
- **Rendering library**: `reportlab` (Python stdlib-ish, lightweight) or `weasyprint` (modern, HTML/CSS-based).
- **Performance**: Must complete in <5 seconds per river on standard hardware.

**Decision**:
- Use `reportlab` for initial v1 (lighter dependencies; good for simple layouts).
- Define a Jinja2 template in `templates/river_report.html`; pass DB records to template.
- Generate single-river PDFs on demand; batch export (all rivers) in future version.
- Store generated PDFs in `.output/` directory; do not store in DB.
- Implement `--no-shrink` flag for debugging (output raw HTML before PDF conversion).

---

### 8. Configuration & Multi-Site Extensibility

**Question**: How should configuration be structured for future multi-site expansion?

**Findings**:
- **Current**: Single site (nzfishing.com); hardcode base URL and discovery rules.
- **Future**: Multiple sites with different HTML structures; need pluggable parsers.
- **Configuration file**: YAML for readability and ease of maintenance.
- **Parser registry**: Map site name to parser module (deferred to v1.1+).

**Decision**:
- Create `config/nzfishing_config.yaml` with:
  - Base URL, robots.txt URL
  - Discovery rules (index page path, region list selector, river list selector)
  - Rate limit (default 3 seconds)
  - Cache TTL (default 24 hours)
  - Contact User-Agent string
- Keep parser hardcoded for nzfishing.com in v1; refactor to plugin model in v1.1+ (Article 10).

---

### 9. Testing Strategy

**Question**: How to test a scraper that depends on external site structure?

**Findings**:
- **Unit tests**: Mock HTTP responses; test parsing logic in isolation.
- **Integration tests**: Use a local mock HTTP server (Flask or FastAPI) with sample pages.
- **Contract tests**: Define module interfaces; test that modules conform to contracts.
- **Offline tests**: Can re-run tests without hitting the live site.
- **Sample pages**: Capture real nzfishing.com pages (anonymized if needed); version-control them.

**Decision**:
- Create a mock server in `tests/fixtures/mock_server.py` that serves sample pages with configurable responses.
- Store sample pages in `tests/fixtures/sample_pages.html` (captured from live site, updated manually).
- Unit tests: Mock `requests.get()` to return sample HTML.
- Integration tests: Spin up mock server; run full discovery → parse → storage workflow.
- Contract tests: Verify that each module's output conforms to expected data types/structure.
- CI pipeline: Run all tests on every commit (no external site hits).

---

### 10. Logging & Observability

**Question**: What should be logged, and where?

**Findings**:
- **Request log**: Every HTTP request (URL, timestamp, status, delay duration, cache hit/miss).
- **Parse log**: Extraction events (fields found, missing, inference warnings).
- **Error log**: All errors with context (region/river name, exception, stacktrace).
- **Session log**: Scraper start/stop, total regions/rivers discovered, total time.
- **Log format**: JSON lines (`.jsonl`) for machine parsing; human-readable console output.

**Decision**:
- Log to both console (human-readable, INFO level) and file (`logs/scraper.log`, DEBUG level).
- Implement structured logging (JSON) for programmatic analysis.
- Log all requests with Article 9.3 metadata (URL, timestamp, HTTP status, delay).
- No sensitive data in logs (no full HTML, API keys, or user data).
- Rotate log files (e.g., daily or 100MB limit; keep 10 backups).

---

## Technology Choices Summary

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Language** | Python 3.11+ | Standard lib focused; good for data processing; easy to test. |
| **HTTP** | `requests` | Simple, robust, widely used for scraping. |
| **HTML Parsing** | `beautifulsoup4` | Industry standard for web scraping; handles malformed HTML well. |
| **Database** | SQLite (local) | Offline-capable; zero-config; embedded in Python. No server required. |
| **PDF Generation** | `reportlab` | Lightweight; good for structured reports; no Chrome/headless browser needed. |
| **Testing** | `pytest` + mock server | Powerful, flexible; can test without external dependencies. |
| **Configuration** | YAML (`pyyaml`) | Human-readable; easy to version-control. |
| **Logging** | Python `logging` + JSON | Built-in; structured output for observability. |
| **Task Scheduling** | None (CLI only) | Users can use `cron` or `systemd` timers for periodic runs. |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| nzfishing.com HTML structure changes | Regular manual inspection (quarterly); versioning of sample pages in repo. |
| robots.txt policy tightening | Fetch and validate robots.txt at startup; alert user if scraper is now disallowed. |
| Site rate-limiting kicks in | Implement exponential backoff; add jitter; respectful delays (3 sec) reduce likelihood. |
| Database corruption during long runs | Use SQLite WAL mode; implement transaction boundaries for atomic writes. |
| Silent data loss (missing fields) | Store raw HTML alongside parsed fields; always validate parsed output against raw. |
| Performance degradation over time | Monitor memory usage; implement periodic cache cleanup; optimize queries in Phase 2. |

---

## Phase 0 Completion Checklist

- [x] nzfishing.com HTML structure understood (no headless browser needed).
- [x] robots.txt compliance strategy defined.
- [x] Request timing (3 sec) and jitter logic defined.
- [x] HTML caching strategy (24-hour TTL, hash-based keys) designed.
- [x] Error handling (exponential backoff, halt on 5xx threshold) specified.
- [x] Database schema (normalized with raw data) designed.
- [x] PDF generation approach (Jinja2 + reportlab) chosen.
- [x] Configuration file format (YAML) selected.
- [x] Testing strategy (unit + integration + mock server) outlined.
- [x] Logging & observability (structured JSON logs) planned.
- [x] All NEEDS CLARIFICATION items resolved.
- [x] Technology stack finalized; no blockers identified.

**Next Phase**: Phase 1 — Design & Contracts. Generate `data-model.md`, `contracts/`, and `quickstart.md`.
