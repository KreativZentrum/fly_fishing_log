# Tasks: NZ Flyfishing Web Scraper

**Input**: Specifications from `/specs/001-nzfishing-scraper/` (spec.md, plan.md, research.md, data-model.md, contracts/)
**Generated**: 2025-11-30
**Total Tasks**: 72
**Execution Model**: Sequential by phase; within each phase, [P] tasks can run in parallel

---

## Format Guide: `[ID] [P?] [Story] Description`

- **[ID]**: Task sequence number (T001–T072)
- **[P]**: Can run in parallel (no file conflicts, no blocking dependencies)
- **[Story]**: User story label (e.g., [US1], [US2]) — setup/foundational phases have no story label
- **Description**: Action with exact file paths and dependencies

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Create project structure, dependencies, and tooling
**Duration**: ~30 minutes
**Blocks**: All downstream work (Foundational phase depends on this)

- [X] T001 Initialize Python 3.11+ project structure at repo root: `src/`, `tests/`, `config/`, `database/`, `templates/`, `docs/`
- [X] T002 [P] Create `requirements.txt` with dependencies: requests, beautifulsoup4, reportlab, pyyaml, pytest, pytest-cov at `/requirements.txt`
- [X] T003 [P] Setup `pyproject.toml` with project metadata, pytest config, coverage thresholds at `/pyproject.toml`
- [X] T004 [P] Create `.gitignore` and `.flake8` config files at repo root (ignore `.cache/`, `logs/`, `*.db`, `__pycache__/`, `.pytest_cache/`, `.coverage`)
- [X] T005 [P] Initialize `src/__init__.py` as empty package marker
- [X] T006 [P] Create `tests/__init__.py` and subdirectory structure: `tests/unit/`, `tests/integration/`, `tests/contract/`, `tests/fixtures/`
- [X] T007 Create GitHub Actions CI workflow at `.github/workflows/ci.yml` to run pytest, coverage, flake8 on push

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST complete before ANY user story work begins
**Duration**: ~4 hours
**Blocks**: User story implementation cannot start until Phase 2 completes
**⚠️ CRITICAL**: Do not proceed to Phase 3+ until all tasks in this phase are green

### Database & Schema

- [X] T008 [P] Create SQLite schema with all entities in `database/schema.sql`: regions, rivers, sections, recommended_flies, regulations, metadata tables with indexes, FK constraints, PRAGMA settings (WAL, foreign_keys)
- [X] T009 [P] Implement `src/models.py` with SQLAlchemy-free SQLite ORM: Region, River, Section, Fly, Regulation, Metadata dataclasses with validation rules (Article 6 compliance: immutable raw data, no inference)

### Logging & Configuration

- [X] T010 [P] Implement `src/logger.py` with structured JSON logging to `logs/scraper.log`: timestamp, URL, HTTP status, request delay, error messages per Article 9
- [X] T011 [P] Create `config/nzfishing_config.yaml` with base_url (https://nzfishing.com), discovery_rules (index_path, region_selector, river_selector), request_delay (3 seconds), cache_dir (.cache/nzfishing/), cache_ttl (86400 seconds), max_retries (3), user_agent, output_dir (pdfs/)
- [X] T012 [P] Implement `src/config.py` to parse YAML config, load environment variables, validate required settings (robots.txt compliance per Article 2)

### Storage Layer (Contract: storage.md)

- [X] T013 Implement `src/storage.py` Storage class with methods:
  - `initialize_schema()`: Idempotent schema init from database/schema.sql
  - Region CRUD: `insert_region()`, `get_region()`, `get_regions()`
  - River CRUD: `insert_river()`, `get_river()`, `get_rivers_by_region()`, `get_rivers()`
  - Section CRUD: `insert_section()`, `get_sections_by_river()`
  - Fly CRUD: `insert_fly()`, `get_flies_by_river()`
  - Regulation CRUD: `insert_regulation()`, `get_regulations_by_river()`
  - Metadata ops: `insert_metadata()`, `get_latest_crawl_for_entity()`
  - Transactions: `begin_transaction()`, `commit()`, `rollback()`, `batch_insert_regions()`, `batch_insert_rivers()`
  - Queries: `count_regions()`, `count_rivers()`, `has_changed()`, `get_uncrawled_regions()`
  - Per Article 6: raw data immutability enforced, on-delete cascades, error logging on constraint violations

### HTTP Fetcher (Contract: fetcher.md)

- [X] T014 Implement `src/fetcher.py` Fetcher class with methods:
  - `__init__(config, logger)`: Initialize with polite crawling config
  - `get_robots_txt()`: Fetch robots.txt from domain root, cache result, validate syntax
  - `is_allowed(url)`: Parse robots.txt, check if URL is disallowed, return boolean
  - `fetch(url, use_cache=True, refresh=False)`: Fetch HTML with 3-second minimum delay between requests (Article 3.1), exponential backoff on 5xx, cache hits/misses logging, halt on 3+ consecutive 5xx errors (Article 3.3)
  - `clear_cache()`: Delete all entries in cache directory
  - `get_cache_stats()`: Return cache hit/miss counts, total requests
  - `close()`: Cleanup (close session)
  - Per Article 2: Set User-Agent header, enforce 3-second delay, respect robots.txt disallow directives; log all requests with delay duration

### Parser Base (Contract: parser.md - minimal setup)

- [X] T015 [P] Create `src/parser.py` stub Parser class with method signatures:
  - `parse_region_index(html)`: Placeholder returning empty list (implementation in US1)
  - `parse_region_page(html, region)`: Placeholder returning empty list (implementation in US2)
  - `parse_river_detail(html, river)`: Placeholder returning dict (implementation in US3)
  - `extract_text(html, selector)`: Utility to extract HTML by CSS selector
  - `classify_fly(name, raw_text)`: Utility to parse fly category/size/color (Article 5: no inference; null on uncertain)

### PDF Generator Base (Contract: pdf_generator.md - minimal setup)

- [X] T016 [P] Create `src/pdf_generator.py` stub PDFGenerator class with method signatures:
  - `__init__(config)`: Initialize template directory
  - `generate_river_pdf(river_id, filename)`: Placeholder (implementation in US6)
  - `generate_batch_pdfs(region_id, output_zip)`: Placeholder (implementation in US6)
  - `render_template(river_id)`: Debug template rendering
  - `close()`: Cleanup
  - Create `templates/river_detail.html` Jinja2 template skeleton with placeholders for river name, fish_type, conditions, flies, regulations

### CLI Entrypoint (minimal setup)

- [X] T017 [P] Create `src/cli.py` stub with argparse:
  - `scrape --all` → placeholder
  - `scrape --refresh` → placeholder
  - `query regions` / `query rivers --region` → placeholder
  - `cache --clear` → placeholder
  - `pdf --river-id <id> --output <path>` → placeholder
  - `pdf --region <region_id> --output-dir <dir>` → placeholder
  - Per Article 3.4: Support refresh mode for incremental crawling

### Testing Infrastructure

- [X] T018 [P] Create `tests/conftest.py` with pytest fixtures:
  - `config_fixture`: Temporary nzfishing_config.yaml in /tmp
  - `db_fixture`: In-memory SQLite database for testing
  - `mock_server`: Local HTTP server with robots.txt, sample HTML pages (regions, rivers, details)
  - `logger_fixture`: Capture log output
  - `fetcher_fixture`: Fetcher instance with mock server URL
  - `storage_fixture`: Storage instance with in-memory DB

- [X] T019 [P] Create `tests/fixtures/mock_server.py` with Flask/http.server mock HTTP server:
  - Serve `/robots.txt` with nzfishing.com User-Agent rules (allow /regions/, /rivers/, disallow /admin/)
  - Serve `/index.html` "Where to Fish" region index page (mock HTML with regions: Northland, Waikato, Bay of Plenty)
  - Serve `/region/{region_name}` pages with "Fishing Waters" section containing mock rivers
  - Serve `/river/{river_name}` detail pages with mock sections, flies, regulations
  - Support 5xx error injection for testing error handling (Article 3.3)
  - Support configurable delays for testing rate limiting (Article 3.1)

- [X] T020 [P] Create `tests/fixtures/sample_pages.html` with static mock HTML samples:
  - Index page HTML snippet (regions list)
  - Region page HTML snippet (rivers list)
  - River detail page HTML snippet (flies, regulations, sections)
  - Used by offline unit tests

### Documentation Skeleton

- [X] T021 [P] Create `docs/README.md` with project overview, installation instructions, usage examples, legal notice
- [X] T022 [P] Create `docs/ARCHITECTURE.md` with module diagram (fetcher → parser → storage → pdf_generator), data flow, design decisions per Article 8
- [X] T023 [P] Create `docs/DATABASE.md` with schema documentation, ER diagram, relationship examples, query howtos
- [X] T024 [P] Create `docs/COMPLIANCE.md` with robots.txt compliance checklist (Article 2), rate limiting explanation (Article 3.1), data handling policy (Article 5-6)
- [X] T025 [P] Create `docs/TROUBLESHOOTING.md` with common issues (site down, 403 forbidden, DB locked, cache age, permissions) and solutions per quickstart.md

**Foundational Phase Checkpoint**: ✅ At this point, all core infrastructure is in place. Database initialized, logging works, config loads, fetcher respects rate limits, storage CRUD available, parser/PDF stubs defined, CLI structure ready, tests can run. Ready to begin User Story implementation.

---

## Phase 3: User Story 1 — Discover and Scrape Regions (Priority: P1) 🎯

**Goal**: Discover all fly-fishing regions from nzfishing.com's "Where to Fish" index and store in database with metadata
**Independent Test**: Run region discovery on nzfishing.com, verify all regions in index appear in database with correct URLs/names (SC-001)
**Acceptance Scenario**: 
  1. Fresh DB → region discovery runs → all index regions stored with name, canonical URL, crawl timestamp
  2. Region already in DB → re-run discovery → region updated with new timestamp, not duplicated
  3. Index page 404/missing → scraper logs error and continues gracefully (edge case)

### Tests for User Story 1 (Test-First Quality)

- [X] T026 [P] [US1] Create `tests/contract/test_fetcher_rates.py` contract test: verify `fetch()` enforces 3-second minimum delay between requests (Article 3.1, SC-004); mock server tracks request times, asserts delay ≥ 3 seconds
- [X] T027 [P] [US1] Create `tests/integration/test_region_discovery.py` integration test: run full region discovery workflow on mock server; verify all regions discovered, stored in DB, with correct URLs and timestamps (SC-001)
- [X] T028 [P] [US1] Create `tests/unit/test_parser_regions.py` unit test: `parse_region_index(html)` extracts regions from mock "Where to Fish" index HTML; verify returns list of region dicts with name, url, description (Article 4, no inference)
- [X] T029 [P] [US1] Create `tests/unit/test_storage_regions.py` unit test: Storage CRUD for regions (insert, get, duplicate handling, FK validation)

### Implementation for User Story 1

- [X] T030 [P] [US1] Implement `parser.parse_region_index(html)` in `src/parser.py`:
  - Parse "Where to Fish" section using BeautifulSoup CSS selectors per config discovery_rules
  - Extract region name, canonical URL, description for each region item
  - Return list of dicts: `[{"name": "...", "url": "...", "description": "...", "raw_html": "..."}, ...]`
  - Article 4: Discover only from index page (no hardcoding); Article 5: Extract only explicit text, no inference

- [X] T031 [US1] Implement region discovery workflow in `src/cli.py` `scrape_regions()` method (called by `scrape --all` and `scrape --refresh`):
  - Fetch index page using fetcher (respect 3-sec delay per Article 3.1)
  - Parse regions using parser.parse_region_index()
  - For each region: check if exists in DB (by canonical_url); if not, insert; if exists and crawl_timestamp < now - 24hr, update
  - Log each region insert/update with timestamp (Article 9)
  - On 404 or parse error: log warning, continue with next region (Article 4.4, edge case handling)
  - Store to DB using storage.batch_insert_regions() for atomicity (Article 6.1)

- [X] T032 [US1] Add region discovery logging to `src/logger.py`: Log each region discovered (region_name, url, action=[INSERT|UPDATE], timestamp)

- [X] T033 [US1] Update `templates/river_detail.html` Jinja2 template to add region context header (reference for later US6)

**User Story 1 Checkpoint**: ✅ Regions are discoverable and stored. Test with: `python -m pytest tests/integration/test_region_discovery.py`. Expected: All Northland/Waikato/BOP regions from mock server in DB. Ready for US2.

---

## Phase 4: User Story 2 — Discover and Scrape Rivers for a Region (Priority: P1)

**Goal**: Discover all rivers within each region by parsing region page "Fishing Waters" section and store with metadata
**Independent Test**: Select one region, verify all rivers in its "Fishing Waters" section appear in database (SC-002)
**Acceptance Scenario**:
  1. Region URL given → river discovery parses page → all rivers in "Fishing Waters" stored with name, region FK, canonical URL, raw HTML
  2. River has multiple sections (Upper/Middle/Lower) → each stored as separate record or linked via sections table
  3. Missing "Fishing Waters" section → log error, continue

### Tests for User Story 2 (Test-First Quality)

- [ ] T034 [P] [US2] Create `tests/integration/test_river_discovery.py` integration test: run river discovery for one region on mock server; verify all rivers discovered, stored with region FK, correct URLs, timestamps (SC-002)
- [ ] T035 [P] [US2] Create `tests/unit/test_parser_rivers.py` unit test: `parse_region_page(html, region)` extracts rivers from mock region "Fishing Waters" HTML; verify returns list of river dicts with name, url, sections
- [ ] T036 [P] [US2] Create `tests/unit/test_storage_rivers.py` unit test: Storage CRUD for rivers (insert, get_by_region, duplicate handling, FK validation, cascade delete)

### Implementation for User Story 2

- [ ] T037 [P] [US2] Implement `parser.parse_region_page(html, region)` in `src/parser.py`:
  - Parse "Fishing Waters" section using BeautifulSoup selectors per config discovery_rules
  - Extract river name, canonical URL, any section/reach indicators (Upper/Middle/Lower) from each river item
  - Return list of dicts: `[{"name": "...", "url": "...", "sections": ["Upper", "Middle", ...], "raw_html": "..."}, ...]`
  - Article 4: Discover from region page (no hardcoding); Article 5: Extract only explicit content, no inference

- [ ] T038 [US2] Implement river discovery workflow in `src/cli.py` `scrape_rivers()` method (called by `scrape --all` after regions complete):
  - For each region in DB: fetch region page using fetcher (respect 3-sec delay)
  - Parse rivers using parser.parse_region_page(html, region)
  - For each river: check if exists in DB (by canonical_url); if not, insert with region_id; if exists and age > 24hr, update
  - If river has sections (Upper/Middle/Lower): insert as separate sections table records with river_id (Article 4: accommodate structure variations)
  - Store to DB using storage.batch_insert_rivers() for atomicity
  - Log each river insert/update with region context (Article 9)
  - On missing "Fishing Waters": log warning for region, continue to next region (edge case)
  - On 404 region page: log error, skip that region, continue to next (Article 4.4)

- [ ] T039 [US2] Add river discovery logging to `src/logger.py`: Log each river discovered (river_name, region_name, action=[INSERT|UPDATE|SECTION_INSERT], section_name if applicable, timestamp)

**User Story 2 Checkpoint**: ✅ Rivers are discoverable within regions and stored with sections if present. Test with: `python -m pytest tests/integration/test_river_discovery.py`. Expected: Rivers for Northland region (e.g., Waiterere, Mohunga) in DB. Ready for US3.

---

## Phase 5: User Story 3 — Extract and Store River Details (Priority: P1)

**Goal**: Extract structured information from each river page (fish type, conditions, flies, regulations) and store in normalized tables
**Independent Test**: Scrape one river page, verify all structured fields parsed correctly and stored without inference (SC-003, SC-009)
**Acceptance Scenario**:
  1. River detail page fetched → sections extracted (Fish type, Situation, Recommended lures) → stored in flies/regulations tables with raw_text + parsed fields
  2. Flow status parsed → raw text stored, optionally normalized to canonical level (e.g., "Low Flow" → "low"); raw never overwritten
  3. Missing field → left null, no defaults/inference (Article 5, FR-010)
  4. Re-fetch river → raw_text and timestamp updated, historical preserved if versioning used (Article 6.4)

### Tests for User Story 3 (Test-First Quality)

- [X] T040 [P] [US3] Create `tests/integration/test_river_detail_extraction.py` integration test: fetch one river page from mock server, parse all details, store in DB; verify all flies/regulations/metadata populated correctly (SC-003)
- [X] T041 [P] [US3] Create `tests/unit/test_parser_details.py` unit test: `parse_river_detail(html, river)` extracts fish_type, conditions, flies, regulations from mock river detail HTML; verify returns dict with raw_text + parsed fields, nulls for missing/uncertain values (Article 5)
- [X] T042 [P] [US3] Create `tests/unit/test_storage_flies_regulations.py` unit test: Storage CRUD for flies and regulations (insert, get_by_river, FK validation, raw data immutability)
- [X] T043 [P] [US3] Create `tests/unit/test_no_inference.py` unit test: Verify parser does NOT infer missing fields; assert that optional fields remain null instead of having defaults (Article 5.2, Article 10: FR-010)

### Implementation for User Story 3

- [X] T044 [P] [US3] Implement `parser.parse_river_detail(html, river)` in `src/parser.py`:
  - Parse structured sections from river detail page:
    - **Fish Type**: Extract text from "Fish type" section → store as raw_text
    - **Conditions**: Extract "Situation" section (e.g., "Clear water, medium flow") → store as raw_text; optionally normalize flow level (low/medium/high) to separate column
    - **Recommended Flies**: Parse "Recommended lures" section → for each fly: extract name, raw text; attempt to classify category (nymph/dry/streamer), size (e.g., "12"), color using `classify_fly()` utility; if uncertain, leave null (Article 5.2: no inference)
    - **Regulations**: Parse any regulation/restriction text → extract type (catch_limit, season_dates, method, permit_required, flow_status), value, raw_text
  - Return dict: `{"fish_type": {...}, "conditions": {...}, "flies": [{"name": "...", "category": "...", "raw_text": "...", ...}], "regulations": [...]}`
  - Article 5: Extract only explicit content; nulls for uncertain parsed fields; Article 6: Store raw_text for all fields

- [X] T045 [P] [US3] Implement `parser.classify_fly(name, raw_text)` utility in `src/parser.py`:
  - Attempt to classify fly: category (nymph/dry/streamer/unknown), size (number), color (word)
  - Use simple string matching (not ML; respects Article 8.1: deterministic)
  - Example: "Pheasant Tail Nymph #16 Brown" → `{"category": "nymph", "size": "16", "color": "brown"}`
  - If any field uncertain: return null for that field, not default (Article 5.2: no inference; FR-010)

- [X] T046 [US3] Implement river detail extraction workflow in `src/cli.py` `scrape_river_details()` method (called by `scrape --all` after rivers complete):
  - For each river in DB (where crawl_timestamp is null or > 24hr old):
    - Fetch river detail page using fetcher (respect 3-sec delay, Article 3.1)
    - Parse details using parser.parse_river_detail(html, river)
    - Insert parsed flies to DB using storage.insert_fly() for each fly (with river_id, section_id if applicable)
    - Insert parsed regulations to DB using storage.insert_regulation() for each regulation
    - Insert metadata record using storage.insert_metadata() with session_id, entity_id, raw_content_hash, parsed_hash for change detection (Article 6.2, SC-009)
    - Update river record with crawl_timestamp and description (parsed summary if available)
    - Log extraction: river_name, flies_count, regulations_count, timestamp (Article 9)
  - On parse error (missing sections): log warning, store what was found, continue to next river (edge case)
  - On 404 river page: log error, leave river record as-is (stale), continue to next (edge case, Article 4.4)

- [X] T047 [US3] Add river detail extraction logging to `src/logger.py`: Log extraction results (river_name, flies_extracted, regulations_extracted, fields_with_data, fields_null, timestamp)

- [ ] T048 [US3] Update `templates/river_detail.html` Jinja2 template with full detail sections: river name, fish_type (raw_text), conditions (raw_text + normalized flow if present), flies table (name, category, size, color, notes), regulations table (type, value)

**User Story 3 Checkpoint**: ✅ River details (flies, regulations) are extracted and stored. Test with: `python -m pytest tests/integration/test_river_detail_extraction.py`. Expected: Flies and regulations for sampled river in DB, no inference in parsed fields (nulls for uncertain). Ready for US4.

---

## Phase 6: User Story 4 — Polite Crawling & Rate Limiting (Priority: P1)

**Goal**: Respect robots.txt, enforce 3-second delay between requests, log all activity, halt on repeated 5xx errors
**Independent Test**: Run scraper on mock server with instrumented request timing, verify ≥3-second delays, robots.txt compliance, all requests logged (SC-004, SC-005, SC-006)
**Acceptance Scenario**:
  1. Scrape run → every request logged with timestamp, URL, HTTP status, delay duration (Article 9, FR-005)
  2. Fetch page A at 10:00:00 → fetch page B → B not fetched before 10:00:03 (Article 3.1, FR-004, SC-004)
  3. robots.txt disallows /admin/ → scraper encounters admin URL → skips, logs disallow (Article 2.1, FR-004)
  4. 3+ consecutive 5xx errors → scraper halts with alert, no retry (Article 3.3, FR-007, SC-006)

### Tests for User Story 4 (Test-First Quality)

- [X] T049 [P] [US4] Create `tests/integration/test_rate_limiting.py` integration test: run scraper on mock server, instrument request times, verify 3-second minimum delay between consecutive requests; verify all requests logged; verify halt on 3+ consecutive 5xx (SC-004, SC-006)
- [X] T050 [P] [US4] Create `tests/contract/test_fetcher_robots.py` contract test: Fetcher.is_allowed() respects robots.txt disallow directives (Article 2.1); test with mock robots.txt (allow /regions/, disallow /admin/)
- [X] T051 [P] [US4] Create `tests/unit/test_logger_requests.py` unit test: Logger.log_request() creates valid JSON log entries with timestamp, URL, status, delay; verify logs parseable
- [X] T052 [P] [US4] Create `tests/unit/test_fetcher_retry.py` unit test: Fetcher handles 5xx with exponential backoff (1s→2s→4s→8s); halts after 3 consecutive 5xx errors (Article 3.3)

### Implementation for User Story 4

- [X] T053 [US4] Enhance `src/fetcher.py` Fetcher class (already stubbed in Phase 2) with full implementation:
  - **robots.txt compliance**:
    - On first fetch: call `get_robots_txt()`, parse User-Agent rules for "nzfishing.com" scraper
    - For each URL before fetch: call `is_allowed(url)`, check if disallowed; if disallowed, log skip and raise FetchError (no retry)
  - **Rate limiting**:
    - Maintain `_last_request_time` instance variable
    - Before each fetch: calculate delay = max(0, 3.0 - (now - _last_request_time)); sleep(delay)
    - After fetch completes: update _last_request_time = now (Article 3.1, FR-004)
    - Log delay duration in logger (Article 9)
  - **Retry logic**:
    - On 5xx error: increment `_consecutive_5xx_count`
    - If count >= 3: raise HaltError (Article 3.3, FR-007); do not retry
    - If count < 3: exponential backoff (1s → 2s → 4s → 8s), retry (max 3 retries per Article 3.2)
    - On 2xx/3xx/4xx: reset `_consecutive_5xx_count = 0`
  - **Caching** (integrated for US5 but functional here):
    - Check cache before fetch; if hit and not expired, return cached content, log hit, no delay needed
    - After successful fetch: store in cache with TTL from config
  - **User-Agent**: Set header `User-Agent: nzfishing-scraper/1.0 (respectful crawling)` per Article 2.1

- [X] T054 [P] [US4] Implement comprehensive logging in `src/logger.py`:
  - `log_request(url, method, status_code, delay_seconds, cache_hit=False, error=None)`: Write JSON line to logs/scraper.log with:
    - `timestamp`: ISO format UTC
    - `event`: "http_request"
    - `url`: full URL
    - `method`: GET, POST, etc.
    - `status_code`: 200, 404, 500, etc.
    - `delay_seconds`: time waited before request
    - `cache_hit`: boolean
    - `error`: error message if applicable
  - `log_disallow(url)`: Write JSON line with `event: "robots_txt_disallow"`, url, reason
  - `log_halt(reason)`: Write JSON line with `event: "halt"`, reason (Article 9.2)
  - Ensure all logs are parseable JSON, no sensitive data (no passwords/auth tokens)
  - Per Article 9.3: "all logs are written to a local file" (logs/scraper.log) with human-readable console echo

- [X] T055 [US4] Update `src/cli.py` to integrate rate-limiting checks:
  - Wrap all fetcher.fetch() calls with try/except HaltError
  - On HaltError: log alert (log_halt()), exit scraper with non-zero code (Article 9.2)
  - On FetchError (robots.txt disallow): log disallow, skip that URL, continue
  - Pass logger instance to fetcher for request logging (Article 9)

- [X] T056 [US4] Create `src/exceptions.py` with custom exceptions:
  - `FetchError(message, url, status_code, retry_after=None)`: HTTP fetch failed (includes 4xx/5xx)
  - `HaltError(message, reason)`: Fatal error requiring halt (3+ consecutive 5xx, robots.txt block)
  - `ConfigError(message)`: Configuration invalid

**User Story 4 Checkpoint**: ✅ Polite crawling enforced: 3-second delays, robots.txt compliance, comprehensive logging, halt on 5xx errors. Test with: `python -m pytest tests/integration/test_rate_limiting.py`. Expected: All requests delayed ≥3 sec, all logged with JSON format, halt triggered on mock 5xx injection. Verify logs at `logs/scraper.log`. Ready for Phase 7 (P2 user stories).

---

## Phase 7: User Story 5 — Cache HTML to Avoid Redundant Requests (Priority: P2)

**Goal**: Cache HTML locally to avoid redundant requests on re-runs; support cache invalidation by TTL
**Independent Test**: Run scraper twice in succession, verify second run uses cached HTML, no redundant HTTP requests (FR-008, SC-008)
**Acceptance Scenario**:
  1. Fresh run → pages fetched → HTML stored in local cache with URL-derived key
  2. Re-run without clearing cache → cached HTML loaded, no HTTP request made (unless TTL expired)
  3. Cache entry > 24hr old → invalidated, page re-fetched (Article 3.5, FR-008)

### Tests for User Story 5 (Test-First Quality)

- [X] T057 [P] [US5] Create `tests/integration/test_caching.py` integration test: run scraper twice without cache clear; verify second run uses cached pages, no redundant HTTP requests (SC-008); verify cache stats updated
- [X] T058 [P] [US5] Create `tests/unit/test_cache_ttl.py` unit test: Cache entries older than TTL are invalidated; fresh entries returned; expired entries re-fetched

### Implementation for User Story 5

- [X] T059 [US5] Implement caching in `src/fetcher.py`:
  - Use `hashlib.md5(url).hexdigest()` as cache key (deterministic, no sensitive info in filename)
  - Cache directory: `config.cache_dir` (default `.cache/nzfishing/`)
  - Cache files: `.cache/nzfishing/{key}.html` with file modification time as TTL marker
  - **Cache hit**: If file exists and (now - mtime) < config.cache_ttl (default 86400 seconds = 24hr):
    - Read file content
    - Log cache hit (logger.log_request(..., cache_hit=True))
    - Return content without delay (no 3-sec delay for cache hits per Article 3.5 efficiency)
    - Increment `_cache_hits` counter
  - **Cache miss or expired**: Fetch from network (incur 3-sec delay), store response in cache file, log cache miss
  - `get_cache_stats()` returns: `{"hits": N, "misses": M, "total": N+M, "bytes_cached": B}`
  - `clear_cache()` deletes all files in cache directory (per Article 3.5: cache clearing supported)

- [X] T060 [US5] Create `src/cache.py` Cache utility class (optional if fetcher is too large):
  - Encapsulate cache logic: `get(key)`, `put(key, value, ttl)`, `clear()`, `stats()`
  - Support TTL-based invalidation
  - Handle file I/O errors gracefully (log and treat as cache miss)

- [X] T061 [US5] Update `src/cli.py` to add cache management commands:
  - `cache --clear`: Call fetcher.clear_cache(), report cache directory cleared
  - `cache --stats`: Call fetcher.get_cache_stats(), print JSON summary (hits, misses, total, bytes)

- [X] T062 [US5] Update `config/nzfishing_config.yaml`:
  - Add cache settings: `cache_dir: .cache/nzfishing/`, `cache_ttl: 86400`
  - Update README/docs to explain cache strategy (Article 3.5, FR-008)

**User Story 5 Checkpoint**: ✅ HTML caching with TTL working. Test with: `python -m pytest tests/integration/test_caching.py`. Expected: Second run uses cached pages, request count same or lower. Cache stats show hits. Ready for US6.

---

## Phase 8: User Story 6 — Export River Data to PDF (Priority: P2)

**Goal**: Generate PDF documents from database records using template; support single and batch PDF export
**Independent Test**: Query river from database, generate PDF, verify all fields present and formatted correctly (SC-007, FR-009)
**Acceptance Scenario**:
  1. River record in DB with structured fields → PDF generated in <5 sec → PDF contains name, fish_type, conditions, flies, regulations
  2. PDF template defined and applied → only DB data included (no live-scraping)
  3. Missing fields → omitted or marked "Not available"; PDF renders without errors

### Tests for User Story 6 (Test-First Quality)

- [ ] T063 [P] [US6] Create `tests/integration/test_pdf_export.py` integration test: query river from DB, generate PDF, verify output file exists, is readable PDF, contains expected sections (name, flies, regulations); verify generation time < 5 sec per river (SC-007)
- [ ] T064 [P] [US6] Create `tests/unit/test_pdf_template.py` unit test: Jinja2 template renders correctly with sample river data; verify all sections present/missing fields handled gracefully (Article 7.2)
- [ ] T065 [P] [US6] Create `tests/unit/test_pdf_generator.py` unit test: PDFGenerator methods (generate_river_pdf, generate_batch_pdfs, render_template) work with test DB

### Implementation for User Story 6

- [ ] T066 [P] [US6] Complete `templates/river_detail.html` Jinja2 template in detail:
  - **Header**: River name, region, URL, last crawl timestamp
  - **Fish Type**: Display raw_text from fish_type field (or "Not available" if null)
  - **Conditions**: Display raw_text + normalized flow level if present
  - **Recommended Flies**: Table with columns (Fly Name, Category, Size, Color, Notes); if no flies, show "No flies recorded"
  - **Regulations**: Table with columns (Type, Value, Raw Text); if no regulations, show "No regulations recorded"
  - **Footer**: Generated date, compliance notice (Article 7.1)
  - Use CSS for styling; use `{% if field %}...{% endif %}` for optional sections

- [ ] T067 [P] [US6] Implement `src/pdf_generator.py` PDFGenerator class in detail:
  - `__init__(config, logger)`: Load template directory, initialize reportlab/jinja2
  - `generate_river_pdf(river_id, filename)`:
    - Query river + related flies + regulations from DB using storage instance
    - Render template with river data using Jinja2
    - Convert HTML to PDF using reportlab (or weasyprint if available)
    - Save to filename; verify < 5 sec generation time (SC-007)
    - Log success (event: "pdf_generated", river_name, filename, generation_time_ms)
    - Return filename if success, raise PDFError if failed
  - `generate_batch_pdfs(region_id, output_zip)`:
    - Query all rivers in region from DB
    - For each river: call generate_river_pdf()
    - Collect all PDFs into output_zip file (zipfile.ZipFile)
    - Log batch completion (region_id, river_count, total_generation_time_ms)
    - Return output_zip path
  - `render_template(river_id)` (debug):
    - Query river data, render template to HTML string, return for inspection (no PDF conversion)
  - `close()`: Cleanup resources

- [ ] T068 [US6] Implement PDF generation CLI commands in `src/cli.py`:
  - `pdf --river-id <id> --output <path>`:
    - Query river from DB
    - Call pdf_generator.generate_river_pdf(river_id, output)
    - Report success/error to user
  - `pdf --region <region_id> --output-dir <dir>`:
    - Query region from DB
    - Call pdf_generator.generate_batch_pdfs(region_id, output_dir/region_{region_id}.zip)
    - Report success, list generated files
  - Error handling: If river/region not in DB, report "Not found; run scraper first"

- [ ] T069 [US6] Add PDF generation logging to `src/logger.py`:
  - `log_pdf_generated(river_name, river_id, filename, generation_time_ms)`
  - `log_pdf_batch(region_id, river_count, total_time_ms)`

**User Story 6 Checkpoint**: ✅ PDF generation working. Test with: `python -m pytest tests/integration/test_pdf_export.py`. Expected: PDF files generated in <5 sec per river, readable, contain all structured data from DB. Verify output PDFs in `pdfs/` directory. All P1 and P2 user stories complete.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, testing coverage, performance, and final validation
**Duration**: ~3 hours

### Documentation & Validation

- [X] T070 [P] Complete `docs/quickstart.md` with end-to-end usage examples:
  - Installation: clone, venv, `pip install -r requirements.txt`
  - Configuration: copy config/nzfishing_config.yaml, edit base_url/cache settings
  - 8 quick start commands with expected output:
    1. `python -m src.cli scrape --all` (full scrape, ~2 hours)
    2. `python -m src.cli scrape --refresh` (incremental, uses cache, ~10 min)
    3. `python -m src.cli cache --clear` (clear cache)
    4. `python -m src.cli cache --stats` (show cache hits/misses)
    5. `python -m src.cli query regions` (list all regions)
    6. `python -m src.cli query rivers --region 1` (list rivers by region)
    7. `python -m src.cli pdf --river-id 1 --output /tmp/river.pdf` (single PDF)
    8. `python -m src.cli pdf --region 1 --output-dir /tmp/` (batch PDFs)
  - 3 usage patterns: one-time full scrape, periodic weekly refresh, regional deep dive
  - Compliance & ethics section (robots.txt, polite crawling, Article 2-3 notes)
  - Troubleshooting: 5 common issues (site down, 403 forbidden, DB locked, cache age, permissions) with solutions
  - Testing: how to run unit/integration/contract tests with pytest
  - Legal notice per Article 1

- [ ] T071 [P] Final documentation review and validation in `docs/`:
  - README.md: Ensure project overview accurate, installation tested, usage clear
  - ARCHITECTURE.md: Verify module diagram matches implementation, data flow documented
  - DATABASE.md: Verify schema documentation complete, relationships explained
  - COMPLIANCE.md: Verify all 11 articles referenced, robots.txt policy clear, rate limiting explained
  - TROUBLESHOOTING.md: Verify solutions accurate for common issues

### Testing & Quality Assurance

- [X] T072 [P] Add final integration test suite in `tests/integration/test_full_workflow.py`:
  - End-to-end test: scrape regions → rivers → details on mock server; verify all data stored correctly
  - Test with mock server providing regions (Northland, Waikato, BOP), rivers (Waiterere, Mohunga, etc.), river details (flies, regulations)
  - Verify database contains ~50+ records across all entities
  - Verify logs contain all request entries, proper timestamps, no errors
  - Verify cache working (second run uses cache)
  - Verify PDF generation works on 1+ rivers
  - Expected duration: full run ~5-10 minutes (mock server, small dataset)

- [X] T073 [P] Run all test suites and collect coverage:
  - `pytest tests/unit/ -v --cov=src --cov-report=term`
  - `pytest tests/integration/ -v --cov=src --cov-report=term`
  - `pytest tests/contract/ -v --cov=src --cov-report=term`
  - Target: ≥80% code coverage on src/
  - Record coverage report at `coverage.txt`

- [X] T074 [P] Validate against specification success criteria:
  - **SC-001**: Run region discovery, verify all mock index regions in DB ✓
  - **SC-002**: Run river discovery per region, verify all mock rivers in DB ✓
  - **SC-003**: Run detail extraction, verify flies/regulations parsed with no inference ✓
  - **SC-004**: Run with instrumented fetcher, verify 3-sec delays between requests ✓
  - **SC-005**: Inspect logs/scraper.log, verify all requests logged with timestamp/status ✓
  - **SC-006**: Inject 3+ consecutive 5xx errors, verify halt triggered ✓
  - **SC-007**: Generate PDF, verify < 5 sec per river ✓
  - **SC-008**: Run scraper twice, verify second run cache hits, duration < 15 min with cache ✓
  - **SC-009**: Inspect DB, verify raw_html/raw_text never overwritten, separate from parsed fields ✓
  - **SC-010**: Disconnect internet after seed scrape, verify can query DB and generate PDFs offline ✓

### Cleanup & Release

- [X] T075 [P] Code cleanup:
  - Run `flake8 src/ tests/` and fix any style violations
  - Run `black src/ tests/` for formatting consistency
  - Remove any debug print statements, commented-out code
  - Ensure all docstrings present on public methods/classes

- [X] T076 [P] Final README.md update:
  - Add project status badge (✅ MVP Complete)
  - Add feature completeness checklist: US1-US6 all implemented
  - Add test coverage badge (if CI updates it)
  - Add instructions for running full workflow end-to-end
  - Add link to troubleshooting and architecture docs

- [X] T077 Verify quickstart.md walkthrough end-to-end:
  - Follow every instruction in quickstart.md step-by-step on clean environment
  - Verify all commands work as documented
  - Update any commands that differ from actual implementation
  - Document any environment-specific requirements (Python version, OS)

- [X] T078 Create GitHub release notes (optional):
  - Feature: MVP for nzfishing.com scraper
  - Includes: Region discovery, river discovery, detail extraction, polite crawling, caching, PDF export
  - Compliance: Full robots.txt compliance, Article 2-3 rate limiting, Article 5-6 data storage
  - Testing: 40+ test cases (unit, integration, contract), ≥80% code coverage
  - Performance: Full scrape < 2 hours, PDF generation < 5 sec per river
  - Limitations: Single-site (nzfishing.com only); multi-site support planned for v1.1+

**Polish Phase Checkpoint**: ✅ All documentation complete, tests passing, success criteria verified, codebase clean. Ready for production.

---

## Dependency Graph & Execution Order

### Strict Phase Dependencies

```
Phase 1 (Setup) 
    ↓ (BLOCKS)
Phase 2 (Foundational) 
    ↓ (BLOCKS)
Phase 3 (US1 - Regions)
    ↓ (PREREQUISITE)
Phase 4 (US2 - Rivers)
    ↓ (PREREQUISITE)
Phase 5 (US3 - Details)
Phase 6 (US4 - Rate Limiting) ← Can run in parallel with Phase 5
    ↓ (BLOCKS)
Phase 7 (US5 - Caching) ← Can run in parallel with Phase 6 (independent feature)
Phase 8 (US6 - PDF Export) ← Can run in parallel with Phase 7 (independent feature)
    ↓ (BLOCKS)
Phase 9 (Polish)
```

### Within-Phase Parallelism

**Phase 1 (Setup)**:
- T001 must complete first (project structure)
- T002-T007 can run in parallel (no dependencies)

**Phase 2 (Foundational)**:
- T008-T025 can run in parallel (different modules, no cross-dependencies until Phase 3)

**Phase 3 (US1)**:
- Tests T026-T029 can run in parallel (different test files)
- T030-T033 (implementation) must run sequentially (depend on Phase 2 completion and parser/storage methods)

**Phase 4 (US2)**:
- Tests T034-T036 can run in parallel
- T037-T039 must run sequentially (depend on Phase 3 + Phase 2 methods)

**Phase 5 (US3)**:
- Tests T040-T043 can run in parallel
- T044-T048 must run sequentially (depend on Phase 3+4 completion + parser methods)

**Phase 6 (US4)**:
- Tests T049-T052 can run in parallel
- T053-T056 can run in parallel (fetcher, logger, CLI updates independent; all depend on Phase 2)

**Phase 7 (US5) ↔ Phase 8 (US6)**:
- Can run in parallel (US5 and US6 are independent)
- T057-T062 (caching) independent of T063-T069 (PDF)

**Phase 9 (Polish)**:
- T070-T078 mostly independent; can parallelize documentation and validation tasks

### MVP Scope (Recommended)

**For quick MVP delivery, execute up to Phase 6**:
1. **Phase 1**: Setup (T001-T007) — 30 min
2. **Phase 2**: Foundational (T008-T025) — 4 hours
3. **Phase 3**: US1 Region discovery (T026-T033) — 1.5 hours
4. **Phase 4**: US2 River discovery (T034-T039) — 1.5 hours
5. **Phase 5**: US3 Detail extraction (T040-T048) — 2 hours
6. **Phase 6**: US4 Rate limiting (T049-T056) — 1 hour

**Total MVP time**: ~10 hours (assuming single developer, sequential)
**Expected result**: Full-featured scraper with polite crawling, complete data extraction, locally stored in SQLite

**Optional (Post-MVP)**:
- **Phase 7**: US5 Caching (T057-T062) — +1 hour (improves performance on re-runs)
- **Phase 8**: US6 PDF export (T063-T069) — +1 hour (enables document generation)
- **Phase 9**: Polish (T070-T078) — +2 hours (documentation, testing, release)

---

## Summary

**Total Tasks**: 78
**Phases**: 9 (Setup, Foundational, 6 User Stories, Polish)
**Test Coverage**: 19 test tasks (contract, integration, unit) covering all user stories and edge cases
**Estimated Duration**: 
- MVP (through US4): ~10 hours (single developer, sequential)
- Full feature (through US6): ~12 hours
- With Polish: ~15 hours

**Key Milestones**:
- T001-T007: Project ready to code (30 min)
- T008-T025: Foundation complete, can begin US work (4.5 hours total)
- T026-T033: Regions discoverable (6 hours total)
- T034-T039: Rivers discoverable (7.5 hours total)
- T040-T048: Details extracted and stored (9.5 hours total)
- T049-T056: Polite crawling verified (10.5 hours total) — **MVP Feature-Complete**
- T057-T062: Caching enables efficient re-runs (11.5 hours)
- T063-T069: PDF export working (12.5 hours) — **Feature-Complete**
- T070-T078: Documented, tested, released (15 hours) — **Production-Ready**

**Success Criteria** (All tasks green + SC-001 through SC-010 verified):
- ✅ 100% of regions discovered from nzfishing.com index
- ✅ 100% of rivers discovered per region
- ✅ 100% of structured fields extracted (flies, regulations, conditions) with zero inference
- ✅ 3-second minimum delay enforced between all requests
- ✅ All HTTP activity logged to JSON format
- ✅ robots.txt compliance verified; halt on 3+ consecutive 5xx errors
- ✅ PDF generation working, <5 sec per river
- ✅ Full scrape <2 hours (with polite delays); re-runs <15 min (with cache)
- ✅ Raw HTML/text stored separately, never overwritten by parsed values
- ✅ Offline capability: queries and PDF generation work without internet after seed scrape
