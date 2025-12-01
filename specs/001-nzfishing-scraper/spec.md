# Feature Specification: NZ Flyfishing Web Scraper

**Feature Branch**: `001-nzfishing-scraper`  
**Created**: 2025-11-30  
**Status**: Draft  
**Input**: Build web scraper for nzfishing.com to collect public fly-fishing information (regions, rivers, conditions, regulations) and store in SQLite database; support PDF export of river data.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover and Scrape Regions (Priority: P1)

As a user, I want the scraper to discover all fly-fishing regions from nzfishing.com's "Where to Fish" index
and store their metadata (name, URL, description) in the database so I can browse regions offline.

**Why this priority**: Regions are the top-level organization of all data; without them, no rivers can be discovered.
This is the foundation for all downstream scraping.

**Independent Test**: Can be fully tested by running the scraper on nzfishing.com, verifying that all visible regions
in the "Where to Fish" index are present in the database with correct URLs and names.

**Acceptance Scenarios**:

1. **Given** a fresh database, **When** the region discovery scraper runs, **Then** all regions from the "Where to Fish" index are stored in the `regions` table with name, canonical URL, and crawl timestamp.
2. **Given** a region already in the database, **When** the scraper re-runs discovery, **Then** the region is updated with the latest crawl timestamp but not duplicated.
3. **Given** the "Where to Fish" index has been reformatted or a region is removed, **When** the scraper runs, **Then** it gracefully handles missing sections and logs warnings.

---

### User Story 2 - Discover and Scrape Rivers for a Region (Priority: P1)

As a user, I want the scraper to discover all rivers within a region by parsing the region's "Fishing Waters" section
and store river metadata (name, URL, section/reach info) so I can explore rivers by region.

**Why this priority**: Rivers are the primary entity users care about; discovering rivers is prerequisite for collecting detailed conditions and regulations.

**Independent Test**: Can be fully tested by selecting one region and verifying that all rivers listed in its "Fishing Waters" section appear in the database with correct structure.

**Acceptance Scenarios**:

1. **Given** a region URL, **When** the river discovery scraper parses the region page, **Then** all rivers in the "Fishing Waters" section are stored in the `rivers` table with name, region FK, canonical URL, and raw HTML excerpt.
2. **Given** a river page contains multiple sections or reaches (e.g., "Upper", "Middle", "Lower"), **When** parsed, **Then** each section is captured as a separate record or linked via `sections` table.
3. **Given** the scraper encounters a malformed or missing "Fishing Waters" section, **When** it processes that region, **Then** it logs the issue and continues with other regions.

---

### User Story 3 - Extract and Store River Details (Priority: P1)

As a user, I want the scraper to extract structured information from each river page (fish type, conditions, recommended flies, regulations)
and store it in separate, normalized database tables so I can query and filter rivers by these attributes.

**Why this priority**: Structured river data is the core value proposition; this enables offline browsing, filtering, and PDF generation.

**Independent Test**: Can be fully tested by scraping a single river page, verifying that all structured fields (fish type, conditions, flies, regulations) are correctly parsed and stored in the database.

**Acceptance Scenarios**:

1. **Given** a river detail page with sections like "Fish type", "Situation", "Recommended lures", **When** parsed, **Then** each section's content is extracted and stored in the `recommended_flies`, `regulations`, and `metadata` tables with raw text and timestamp.
2. **Given** a river has flow information (e.g., "Medium flow"), **When** parsed, **Then** the raw text is stored and optionally normalized to a canonical flow level in a separate column (not overwriting raw).
3. **Given** a field is missing or empty on the river page, **When** parsed, **Then** that field is left null in the database; no inference or default values are added.
4. **Given** the scraper re-fetches a river already in the database, **When** new data is available, **Then** the raw text and timestamp are updated; historical records are retained if a versioning table is implemented.

---

### User Story 4 - Polite Crawling & Rate Limiting (Priority: P1)

As a site owner (nzfishing.com), I want the scraper to respect robots.txt, enforce a 3-second delay between requests,
and log all requests so I can trust that the tool is not abusing the site's resources.

**Why this priority**: Legal and ethical compliance with the website; non-negotiable per Article 2 of the constitution.

**Independent Test**: Can be fully tested by running a scraper on a local mock server with robots.txt, verifying that requests are delayed by ≥3 seconds, logged, and respect any disallow directives.

**Acceptance Scenarios**:

1. **Given** a scraper run against nzfishing.com, **When** requests are made, **Then** each request is logged with timestamp, URL, HTTP status, and delay duration; all logs are written to a local file.
2. **Given** the scraper fetches page A at 10:00:00, **When** it fetches page B, **Then** page B is not fetched before 10:00:03.
3. **Given** robots.txt disallows `/admin/`, **When** the scraper encounters an admin URL, **Then** it skips that URL and logs the skip.
4. **Given** the scraper receives 3+ consecutive 5xx errors from nzfishing.com, **When** processing that region, **Then** the scraper halts with an alert message and does not retry.

---

### User Story 5 - Cache HTML to Avoid Redundant Requests (Priority: P2)

As a scraper operator, I want HTML responses to be cached locally during a run so that re-running the scraper
without clearing the cache will not re-fetch unchanged pages, saving time and bandwidth.

**Why this priority**: Efficiency for re-runs; reduces load on the site. Important but not blocking the MVP.

**Independent Test**: Can be fully tested by running the scraper twice in succession, verifying that the second run uses cached HTML and does not make redundant HTTP requests.

**Acceptance Scenarios**:

1. **Given** a fresh scraper run, **When** pages are fetched, **Then** HTML is stored in a local cache directory with a cache key derived from the URL.
2. **Given** a cached HTML file exists and has not been invalidated, **When** the scraper runs again, **Then** the page is loaded from cache and no HTTP request is made.
3. **Given** a cache entry is older than a configured TTL (e.g., 24 hours), **When** the scraper runs, **Then** the cache entry is invalidated and the page is re-fetched.

---

### User Story 6 - Export River Data to PDF (Priority: P2)

As a user, I want to export a river's information to a PDF document containing the river name, conditions, recommended flies, and regulations
so I can view or print it offline.

**Why this priority**: PDF export is a key deliverable for offline use. Important but depends on Stories 1–3 being complete.

**Independent Test**: Can be fully tested by querying a river from the database and generating a PDF, verifying that all structured data is present and formatted correctly.

**Acceptance Scenarios**:

1. **Given** a river record in the database with structured fields, **When** a PDF is generated, **Then** the PDF contains the river name, fish type, conditions, recommended flies, and regulations in a readable format.
2. **Given** a PDF template is defined, **When** the PDF is generated, **Then** the template is applied and only data present in the database is included (no live-scraping during generation).
3. **Given** a river has missing fields (e.g., no regulations), **When** the PDF is generated, **Then** empty sections are omitted or marked as "Not available"; the PDF still renders correctly.

---

### Edge Cases

- What happens when a region page is removed or no longer accessible (404)? → Scraper logs the error and continues; a stale record remains in the database.
- What happens if a river's HTML structure changes significantly? → Parser may fail to extract some fields; raw HTML is stored for manual inspection.
- What happens if the user interrupts the scraper mid-run? → All data fetched so far is committed to the database; the next run can resume from where it left off (via crawl timestamp).
- What happens if a user requests a PDF for a river never scraped? → System returns an error or a partial PDF with only name/URL; no live-scraping is attempted.
- What happens if the SQLite database becomes corrupted? → User should re-run the full scraper; a backup or recovery mechanism is not in scope for v1.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST discover all regions from nzfishing.com's "Where to Fish" index and store them in the `regions` table (per Article 1, 4).
- **FR-002**: System MUST discover all rivers within each region by parsing the "Fishing Waters" section and store them in the `rivers` table (per Article 4).
- **FR-003**: System MUST extract and store structured river data (fish type, conditions, flies, regulations) from river detail pages in separate normalized tables (per Article 5, 6).
- **FR-004**: System MUST respect robots.txt, enforce a 3-second minimum delay between requests, use single-threaded fetching, and set a clear User-Agent string (per Article 2, 3).
- **FR-005**: System MUST log every HTTP request with URL, timestamp, status code, and delay duration to a local log file (per Article 9).
- **FR-006**: System MUST store raw HTML/text alongside parsed structured fields and MUST NOT overwrite raw data with derived values (per Article 5, 6).
- **FR-007**: System MUST halt and alert if 3+ consecutive 5xx errors occur on a site (per Article 3, 9).
- **FR-008**: System SHOULD cache HTML responses locally during a run to avoid redundant requests (per Article 3).
- **FR-009**: System MUST generate PDF documents from database records using a template, not live-scraped pages (per Article 7).
- **FR-010**: System MUST NOT infer or fabricate data not explicitly present on the page (per Article 5).

### Key Entities

- **Region**: Represents a fly-fishing region (e.g., "Northland", "Waikato"). Attributes: name, canonical URL, raw description/HTML, crawl timestamp, source URL.
- **River**: Represents a river within a region. Attributes: name, region FK, canonical URL, raw HTML excerpt, crawl timestamp, source URL.
- **Section/Reach**: (Optional) Represents a section of a river (e.g., "Upper Waikato"). Attributes: name, river FK, canonical URL, raw HTML, crawl timestamp.
- **Recommended Fly**: Represents a fly pattern recommended for a river. Attributes: name, river FK, raw text, parsed categories (if applicable), crawl timestamp.
- **Regulation**: Represents a regulation or condition (e.g., "Catch limit", "Season dates") for a river. Attributes: type, value, river FK, raw text, crawl timestamp.
- **Metadata**: Stores crawl metadata (fetch hash, page version, raw content hash) to enable change detection and versioning.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All regions visible on nzfishing.com's "Where to Fish" index are successfully discovered and stored in the database (100% discovery rate).
- **SC-002**: All rivers listed in each region's "Fishing Waters" section are discovered and stored (100% discovery rate per region tested).
- **SC-003**: Structured data (fish type, conditions, flies, regulations) is extracted from 100% of river detail pages with no data loss or inference.
- **SC-004**: Scraper enforces a minimum 3-second delay between all HTTP requests; no two requests occur within a 3-second window.
- **SC-005**: All HTTP requests are logged with timestamp and status; logs are parseable and contain no sensitive data.
- **SC-006**: Scraper respects robots.txt directives for nzfishing.com and halts gracefully if repeated 5xx errors occur.
- **SC-007**: PDF generation completes in under 5 seconds per river; generated PDFs are readable and contain all stored structured fields.
- **SC-008**: A full scrape of all regions and rivers on nzfishing.com completes in under 2 hours on a standard machine (respecting rate limits).
- **SC-009**: Raw HTML and structured fields are stored separately; no raw data is overwritten by derived values.
- **SC-010**: Scraper is offline-capable after initial seed; no internet connection required to query database or generate PDFs.
