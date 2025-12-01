# Implementation Plan: NZ Flyfishing Web Scraper

**Branch**: `001-nzfishing-scraper` | **Date**: 2025-11-30 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-nzfishing-scraper/spec.md`

## Summary

Build a polite, respectful web scraper for nzfishing.com that discovers fly-fishing regions, rivers, and detailed river information (conditions, regulations, fly patterns) from public pages and stores them in a local SQLite database. The scraper MUST enforce a 3-second request delay, respect robots.txt, log all activity, and support PDF export of river data. The system comprises independent modules for discovery, parsing, storage, and PDF generation, operating deterministically and offline after initial seed.

## Technical Context

**Language/Version**: Python 3.11+ (standard library focused; minimal external dependencies per Article 3 simplicity)  
**Primary Dependencies**: `requests` (HTTP), `beautifulsoup4` (HTML parsing), `sqlite3` (built-in), `reportlab` or `weasyprint` (PDF generation)  
**Storage**: SQLite database (local, file-based; schema designed for extensibility per Article 6.5)  
**Testing**: `pytest` (unit), custom mock HTTP server (integration), contract tests for API-like modules  
**Target Platform**: Linux/macOS CLI tool; single-threaded; no GUI or server component  
**Project Type**: Single project (monolithic scraper + DB + PDF generator)  
**Performance Goals**: Full site crawl completes in <2 hours (respecting 3-sec delays per Article 2.2); PDF generation <5 sec per river (SC-007)  
**Constraints**: Single-threaded only (Article 2.3, 11.3); 3-second minimum delay between requests (Article 2.2, 3.1); offline-capable after seed (SC-010); <100MB memory for typical usage  
**Scale/Scope**: ~50–200 regions; ~5k–20k rivers; initial full crawl ~1–2 hours; re-runs with caching <15 min

## Constitution Check

✅ **GATE: PASS** — Feature satisfies all applicable articles; no violations or exemptions required.

### Article-by-Article Assessment

- **Article 1 (Purpose & Scope)**: ✅ Feature limited to public, unauthenticated pages only (FR-001, US 1–3). No authentication bypass (FR-001, 2.5).
- **Article 2 (Scraping Compliance)**: ✅ robots.txt compliance enforced (FR-004, US 4). 3-second minimum delay (FR-004, US 4, SC-004). Single-threaded (FR-004, Technical Context). Clear User-Agent (FR-004, US 4). Will review robots.txt on changes (Article 2.7, Phase 0 research task).
- **Article 3 (Fetching & Request Principles)**: ✅ Polite crawling with fixed delay ≥3 sec (Article 3.1, FR-004, US 4). Retry with exponential backoff (Article 3.2, Phase 0 research). Halt on repeated 5xx (Article 3.3, FR-007, US 4). Incremental refresh preferred over bulk (Article 3.4, Phase 0 research). HTML cache implemented (Article 3.5, US 5, FR-008).
- **Article 4 (Page Discovery Rules)**: ✅ Region discovery from "Where to Fish" index (US 1, FR-001). River discovery from "Fishing Waters" (US 2, FR-002). No hardcoding except hotfixes (Article 4.3, Phase 1 design). Graceful handling of missing sections (Article 4.4, US 1–2, edge cases).
- **Article 5 (Parsing & Data Interpretation)**: ✅ Extract only explicit content (FR-010, US 3). No inference or fabrication (FR-010, Article 5.2). Accommodate predictable structure (Article 5.3, Phase 1 design). Raw + structured capture (FR-006, US 3). Normalisation after raw storage (Article 5.5, FR-006, US 3).
- **Article 6 (Data Storage Principles)**: ✅ SQLite database default (Technical Context, FR-001–003). Schema distinguishes regions, rivers, sections, flies, regulations, metadata (Key Entities, data-model Phase 1). Every record includes source URL, timestamp, raw text (Article 6.3, Key Entities). Raw data never overwritten (Article 6.4, FR-006). Schema extensible (Article 6.5, Phase 1 design).
- **Article 7 (PDF Generation Principles)**: ✅ Template-driven PDF generation (Article 7.1, US 6, FR-009). Templates operate on database data only (Article 7.2, US 6, FR-009). No live-scrape during PDF generation (Article 7.4, FR-009, US 6).
- **Article 8 (Architecture & Predictability)**: ✅ Deterministic given same inputs (Article 8.1, Technical Context, Phase 1 design). Independent modules: discovery, parsing, storage, PDF (Article 8.2, Phase 1 project structure). No module modifies another's raw output (Article 8.3, FR-006). Configuration centralized (Article 8.4, Phase 0 research).
- **Article 9 (Safety & Operational Discipline)**: ✅ All scraping changes validated vs. robots.txt (Article 9.1, Phase 0 research). Anti-bot response triggers halt (Article 9.2, FR-007, US 4). Complete logging of requests (Article 9.3, FR-005, US 4, SC-005). Prefer cache/DB over refetch (Article 9.4, US 5, FR-008).
- **Article 10 (Extensibility)**: ✅ Multi-site support deferred to v1.1+ (Article 10.1–3). Current implementation monolithic for nzfishing.com; refactoring for modularity planned in Phase 1.
- **Article 11 (Non-Negotiable Constraints)**: ✅ Respectful crawl behavior (Article 11.1–2, FR-004, US 4, SC-004, SC-008). Single-threaded only (Article 11.3, Technical Context, FR-004). All operations inspectable and logged (Article 11.4, FR-005, US 4).

## Project Structure

### Documentation (this feature)

```text
specs/001-nzfishing-scraper/
├── spec.md                          # Feature specification (COMPLETE)
├── plan.md                          # This file (Phase 0–1 plan)
├── research.md                      # Phase 0 output (to be generated)
├── data-model.md                    # Phase 1 output (to be generated)
├── quickstart.md                    # Phase 1 output (to be generated)
├── contracts/                       # Phase 1 output (API contracts for modules)
│   ├── fetcher.md                   # HTTP fetcher contract
│   ├── parser.md                    # HTML parser contract
│   ├── storage.md                   # SQLite storage contract
│   └── pdf_generator.md             # PDF generator contract
├── checklists/
│   └── requirements.md              # Spec quality checklist (COMPLETE)
└── tasks.md                         # Phase 2 output (generated by /speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── config.py                        # Configuration, constants, robots.txt handling
├── logger.py                        # Request logging (URL, timestamp, status, delay)
├── fetcher.py                       # HTTP fetcher with 3-sec delays, caching, retry logic
├── parser.py                        # HTML parsers for regions, rivers, details
├── models.py                        # SQLite ORM/schema (regions, rivers, sections, flies, regulations, metadata)
├── storage.py                       # Database operations (CRUD, schema initialization)
├── pdf_generator.py                 # Template-driven PDF generation from DB records
└── cli.py                           # CLI entrypoint (discovery, parse, export, caching)

tests/
├── __init__.py
├── unit/
│   ├── test_fetcher.py              # Unit tests for polite crawling, caching, delays
│   ├── test_parser.py               # Unit tests for parsing logic (no inference)
│   ├── test_storage.py              # Unit tests for schema and CRUD operations
│   └── test_pdf_generator.py        # Unit tests for template rendering
├── integration/
│   ├── test_discovery_workflow.py   # End-to-end region + river discovery
│   ├── test_detail_extraction.py    # End-to-end river detail parsing + storage
│   ├── test_pdf_export.py           # End-to-end PDF generation from DB
│   └── test_rate_limiting.py        # Integration test for 3-sec delays, logging, error halts
├── contract/
│   └── test_module_contracts.py     # Contract tests ensuring module interfaces
├── fixtures/
│   ├── mock_server.py               # Local mock HTTP server with robots.txt, sample pages
│   ├── sample_pages.html            # Sample nzfishing.com pages (for offline testing)
│   └── db_fixtures.py               # Pre-seeded test databases
└── conftest.py                      # Pytest configuration

.github/workflows/
└── ci.yml                           # CI pipeline (lint, unit tests, integration tests)

docs/
├── README.md                        # Project overview, usage, constraints
├── ARCHITECTURE.md                  # Module design, flow diagrams
├── DATABASE.md                      # Schema documentation, relationships
├── COMPLIANCE.md                    # robots.txt compliance, legal notes
└── TROUBLESHOOTING.md               # Common issues, logs, debugging

config/
├── nzfishing_config.yaml            # Base URLs, discovery rules, delay settings
└── requirements.txt                 # Python dependencies (requests, bs4, reportlab, pytest)

database/
└── schema.sql                       # Initial SQLite schema (regions, rivers, sections, flies, regulations, metadata)
```

**Structure Decision**: Single-project Python CLI tool with modular architecture. Each major responsibility (fetching, parsing, storage, PDF generation) is a separate Python module with clear interfaces, enabling independent testing and future refactoring. Tests include unit, integration (workflow), and contract tests. Configuration is centralized in YAML. Documentation includes architecture, schema, compliance, and troubleshooting.

## Complexity Tracking

**No violations documented.** All architecture decisions comply with the constitution. The single-project structure is appropriate for a CLI scraper with internal modules (fetcher, parser, storage, PDF); refactoring into separate packages is deferred to v1.1+ when multi-site support is added (Article 10).
