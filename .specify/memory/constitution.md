<!--
Sync Impact Report

- Version change: 1.0.0 -> 1.1.0
- Scope: Complete constitutional rewrite for NZ Flyfishing Intelligence Collector scraper/database/PDF pipeline
- Modified principles: Replaced generic principles with domain-specific articles (scraping compliance, parsing, data storage, PDF generation, etc.)
- Removed principles: I-V (User Data Ownership, Privacy, Simplicity, Test-First, Versioning)
- Added articles: Article 1–11 covering scraping compliance, request rate limiting, page discovery, parsing rules, storage, PDF generation, architecture, safety, extensibility
- Templates requiring updates:
  - .specify/templates/plan-template.md ⚠ update Constitution Check to reference Articles 1–11
  - .specify/templates/tasks-template.md ✅ no change required (tests still mandatory)
  - .specify/templates/spec-template.md ⚠ no change required
- Follow-up TODOs:
  - Verify CI gates reference new article names.
  - Update plan-template.md Constitution Check gates.
 -->

# 📜 Spec-Kit Constitution — NZ Flyfishing Intelligence Collector

## Article 1 — Purpose & Scope

1.1 The project exists to **collect, structure, and store public fly-fishing information** for personal use.
1.2 All data collection MUST be limited to the **public, unauthenticated pages** of target websites.
1.3 The project MUST maintain strict separation between:

* raw scraped content
* parsed/structured fields
* derived insights or metadata

---

## Article 2 — Legal & Ethical Scraping Compliance

2.1 All scraping MUST explicitly comply with each target site's **robots.txt**.
2.2 The scraper MUST implement a **minimum 3-second delay** between HTTP requests to `nzfishing.com`.
2.3 The scraper MUST use a **single-threaded** fetch process unless robots.txt explicitly permits higher concurrency.
2.4 The scraper MUST set a clear and identifiable **User-Agent string** indicating purpose and contact.
2.5 The scraper MUST NOT attempt to bypass paywalls, authentication, anti-bot protections, or access non-public content.
2.6 The scraper MUST NOT use headless browser tactics to evade bot protections unless explicitly permitted.
2.7 Request rate, concurrency, and crawl behaviour MUST be reviewed whenever robots.txt changes.

---

## Article 3 — Fetching & Request Principles

3.1 All network operations MUST use a **polite-crawling strategy**, including:

* fixed delay ≥ 3 seconds
* optional random jitter to avoid patterned traffic

3.2 The fetcher SHOULD implement **retry with exponential backoff** for transient errors.
3.3 The scraper MUST stop and alert if repeated **4xx/5xx errors** occur on a site.
3.4 Bulk/full-site crawls MUST be rare and deliberate; incremental refreshes SHOULD be preferred.
3.5 HTML responses SHOULD be cached locally during a run to avoid redundant hits on the origin server.

---

## Article 4 — Page Discovery Rules

4.1 Region pages MUST be discovered directly from the **"Where to Fish"** index.
4.2 River pages MUST be discovered by parsing the region's **"Fishing Waters"** section.
4.3 The scraper MUST NOT hardcode lists of rivers or URLs except when needed for hotfixes.
4.4 The system SHOULD detect and gracefully handle pages with missing or reformatted sections.

---

## Article 5 — Parsing & Data Interpretation

5.1 Parsers MUST extract structured fields only from **content explicitly present** in the public HTML.
5.2 The parser MUST NOT infer or fabricate values not present on the page.
5.3 Parsing logic SHOULD accommodate the predictable content structure on `nzfishing.com` (e.g., "Fish type…", "Situation…", "Recommended lures…").
5.4 Each river entry MUST capture both:

* the **raw HTML/text** for reference
* **structured fields** parsed from it

5.5 Normalisation of values (flows, fly patterns, categories) SHOULD be applied only after raw content is stored.

---

## Article 6 — Data Storage Principles

6.1 All scraped data MUST be stored locally in a **SQLite database** by default.
6.2 The schema MUST distinguish between:

* `regions`
* `rivers`
* `sections/reaches`
* `recommended_flies`
* `regulations`
* `metadata` (crawl time, source URL, fetch hash)

6.3 Every record MUST include:

* canonical source URL
* timestamp of last successful scrape
* raw text captured from the page

6.4 Derived values (e.g., cleaned conditions, interpreted flow levels) MUST NOT overwrite raw data.
6.5 The schema SHOULD be designed for extensibility (additional sites, new fields, new regulations).

---

## Article 7 — PDF Generation Principles

7.1 PDF generation MUST be template-driven (HTML→PDF or equivalent).
7.2 Templates MUST operate only on **data present in the database**, not live-scraped pages.
7.3 PDF output MUST present:

* structured fields
* standard formatting
* optional maps/images from external static sources

7.4 The system MUST NOT fetch external dynamic content during PDF generation.

---

## Article 8 — Architecture & Predictability

8.1 The entire pipeline MUST run deterministically given the same inputs.
8.2 Scraping, parsing, normalisation, and PDF generation MUST be implemented as **independent modules**.
8.3 No module may directly modify another module's raw output.
8.4 All configuration (delays, base URLs, signatures) MUST be maintained in a single, version-controlled file.

---

## Article 9 — Safety & Operational Discipline

9.1 Any change to scraping behaviour MUST be validated against robots.txt compliance.
9.2 Any detected anti-bot response MUST trigger an immediate halt.
9.3 All crawls MUST log:

* every requested URL
* timestamp
* HTTP status
* time spent waiting for crawl-delay

9.4 The system SHOULD prefer local cache or DB content over refetching unless a refresh is explicitly required.

---

## Article 10 — Extensibility & Multi-Site Scraping

10.1 Additional fishing websites MAY be added provided their robots.txt and Terms of Use explicitly allow scraping.
10.2 Each site MUST have a **separate scraper module** encapsulating:

* discovery rules
* parsing rules
* compliance rules

10.3 Shared abstractions MUST NOT assume identical HTML structures across sites.

---

## Article 11 — Non-Negotiable Constraints

11.1 The project MUST respect website owners, bandwidth, and server health.
11.2 The system MUST never run high-frequency crawls, even locally.
11.3 The scraper MUST NOT run in parallel or distributed mode without explicit permission from site owners.
11.4 All operations MUST be inspectable, logged, and reproducible.

---

## Governance

Amendments to this constitution MUST be proposed via a pull request that:
- Describes the change and rationale.
- Identifies affected systems, tests, and migration steps (if any).
- Includes a suggested semantic version bump and justification.

Amendments require at least one maintainer approval and passing CI validation.

**Version**: 1.1.0 | **Ratified**: 2025-11-30 | **Last Amended**: 2025-11-30
