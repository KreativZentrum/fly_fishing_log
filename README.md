# NZ Flyfishing Web Scraper

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-131%20passing-success)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-51%25-orange)](htmlcov/index.html)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**A polite, ethical web scraper for New Zealand fishing information** - designed for personal research and educational purposes.

---

## Overview

The **NZ Flyfishing Web Scraper** systematically collects structured data about fishing regions, rivers, recommended flies, and regulations from New Zealand fishing websites. Built with compliance and ethics as core principles, it respects robots.txt, enforces rate limiting, and maintains complete audit trails.

### Key Features

- **🗺️ Regional Discovery**: Automatically discovers all fishing regions
- **🏞️ River Cataloging**: Extracts river names, descriptions, and metadata
- **🎣 Fly Recommendations**: Parses fly patterns, sizes, and colors
- **📜 Regulation Tracking**: Captures bag limits, seasons, and restrictions
- **⚡ Smart Caching**: Avoids redundant requests with TTL-based HTML caching
- **🤝 Polite Crawling**: 3-second delays, exponential backoff, halt on errors
- **🔒 Compliance First**: Respects robots.txt, comprehensive logging, no inference
- **📊 SQLite Storage**: Structured database with raw data preservation

---

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/fly_fishing_log.git
cd fly_fishing_log

# Setup environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r config/requirements.txt

# Verify installation
pytest tests/ -v
```

### Basic Usage

```bash
# 1. Discover all regions
python -m src.cli discover --regions

# 2. Discover rivers in all regions
python -m src.cli discover --rivers --all

# 3. Extract detailed river information
python -m src.cli scrape-details --all

# 4. Query the database
sqlite3 data/nzfishing.db "SELECT name, slug FROM regions LIMIT 5;"
```

📘 **Full Guide**: See [docs/quickstart.md](docs/quickstart.md)

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                      CLI (cli.py)                       │
│         Command Interface & Workflow Orchestration      │
└───────────┬─────────────────────────────────┬───────────┘
            │                                 │
            ▼                                 ▼
┌───────────────────────┐         ┌──────────────────────┐
│   Fetcher (fetcher.py)│         │  Parser (parser.py)  │
│  - HTTP Requests      │────────▶│  - HTML Parsing      │
│  - Rate Limiting      │         │  - Field Extraction  │
│  - Caching            │         │  - Data Validation   │
│  - robots.txt         │         └──────────┬───────────┘
└───────────┬───────────┘                    │
            │                                │
            ▼                                ▼
┌───────────────────────┐         ┌──────────────────────┐
│  Logger (logger.py)   │         │ Storage (storage.py) │
│  - JSON Logging       │         │  - SQLite Operations │
│  - Audit Trail        │         │  - Schema Management │
│  - Compliance Tracking│         │  - Data Integrity    │
└───────────────────────┘         └──────────────────────┘
```

📐 **Details**: See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## Database Schema

### Entity Relationships

```
regions (1) ──── (N) rivers (1) ──── (N) flies
                         │
                         │
                         └──── (N) regulations
                         │
                         └──── (N) sections
```

### Core Tables

| Table         | Records | Purpose                          |
|---------------|---------|----------------------------------|
| `regions`     | ~20     | Fishing regions (e.g., Northland)|
| `rivers`      | ~200+   | Rivers and streams per region    |
| `flies`       | ~500+   | Recommended fly patterns         |
| `regulations` | ~300+   | Bag limits, seasons, restrictions|
| `sections`    | ~100+   | River sections (Upper/Lower)     |

📊 **Schema**: See [docs/DATABASE.md](docs/DATABASE.md)

---

## Compliance & Ethics

### Core Principles (Article 1-11)

1. **Personal Use Only**: Educational and research purposes
2. **Polite Crawling**: 3-second delays, respect rate limits
3. **robots.txt Compliance**: Auto-loads and respects directives
4. **No Inference**: Extract only explicit content
5. **Raw Data Preservation**: Original HTML always stored
6. **Complete Logging**: All requests timestamped and auditable
7. **Halt on Errors**: Stop on 3+ consecutive 5xx errors
8. **Privacy**: No personal data collection
9. **Attribution**: Source URLs tracked for all data

### Rate Limiting

- **Request Delay**: 3.0 seconds (configurable)
- **Exponential Backoff**: 1s, 2s, 4s on errors
- **Cache Bypass**: Cached responses = instant (no delay)
- **Halt Condition**: 3+ consecutive 5xx → stop execution

📜 **Full Guidelines**: See [docs/COMPLIANCE.md](docs/COMPLIANCE.md)

---

## Testing

### Test Coverage

| Module          | Coverage | Tests |
|-----------------|----------|-------|
| `fetcher.py`    | 91.60%   | 22    |
| `parser.py`     | 83.33%   | 28    |
| `logger.py`     | 83.33%   | 13    |
| `storage.py`    | 80.00%   | 35    |
| `exceptions.py` | 100.00%  | 8     |
| **Total**       | **51.49%** | **131** |

### Run Tests

```bash
# All tests with coverage
pytest --cov=src --cov-report=term-missing --cov-report=html

# Specific test suites
pytest tests/unit/ -v           # Unit tests
pytest tests/integration/ -v    # Integration tests
pytest tests/contract/ -v       # Contract tests

# View HTML coverage report
open htmlcov/index.html
```

---

## Project Structure

```
fly_fishing_log/
├── src/                        # Source code
│   ├── cli.py                 # Command-line interface
│   ├── fetcher.py             # HTTP client + caching
│   ├── parser.py              # HTML parsing logic
│   ├── storage.py             # SQLite operations
│   ├── logger.py              # JSON logging
│   ├── config.py              # Configuration management
│   ├── models.py              # Data models
│   └── exceptions.py          # Custom exceptions
├── tests/                      # Test suites
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── contract/              # Contract tests
├── config/                     # Configuration files
│   └── nzfishing_config.yaml  # Main config
├── docs/                       # Documentation
│   ├── quickstart.md          # Quick start guide
│   ├── ARCHITECTURE.md        # System design
│   ├── DATABASE.md            # Schema reference
│   ├── COMPLIANCE.md          # Ethical guidelines
│   └── TROUBLESHOOTING.md     # Common issues
├── data/                       # SQLite database
│   └── nzfishing.db           # Scraped data
├── logs/                       # JSON logs
│   └── nzfishing.log          # Audit trail
├── cache/                      # HTML cache
│   └── *.html                 # Cached responses
├── specs/                      # Spec-Kit methodology
│   └── 001-nzfishing-scraper/ # Project specifications
│       ├── spec.md            # Requirements
│       ├── plan.md            # Technical plan
│       ├── tasks.md           # Implementation tasks
│       ├── data-model.md      # Entity model
│       └── contracts/         # API contracts
├── requirements.txt            # Python dependencies
├── pyproject.toml             # pytest configuration
└── README.md                  # This file
```

---

## Configuration

### Config File: `config/nzfishing_config.yaml`

```yaml
base_url: "https://fishandgame.org.nz"
user_agent: "nzfishing-scraper/1.0 (educational/personal use)"

# Rate limiting
request_delay: 3.0
jitter_max: 0.5

# Caching
cache_dir: "cache/"
cache_ttl: 86400  # 24 hours

# Retry logic
max_retries: 3
retry_backoff: [1, 2, 4]
halt_on_consecutive_5xx: 3

# Paths
database_path: "data/nzfishing.db"
log_path: "logs/nzfishing.log"
```

---

## Troubleshooting

### Common Issues

| Issue                  | Cause                     | Solution                          |
|------------------------|---------------------------|-----------------------------------|
| Connection Refused     | Site down / blocking      | Wait 5-10 min, check base_url     |
| HaltError (3x 5xx)     | Server errors             | Wait 30-60 min before retry       |
| No data extracted      | HTML structure changed    | Update CSS selectors in config    |
| Slow performance       | Rate limiting enforced    | Expected; use caching             |
| Database locked        | Multiple processes        | Close other scraper instances     |

🛠️ **Full Guide**: See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

---

## Success Criteria (Phase 9 Validation)

- ✅ **SC-001**: Regional discovery extracts 20+ regions
- ✅ **SC-002**: River discovery extracts 50+ rivers per region
- ✅ **SC-003**: Detail extraction captures flies, regulations, descriptions
- ✅ **SC-004**: 3-second delays enforced between requests
- ✅ **SC-005**: Complete JSON logging with timestamps
- ✅ **SC-006**: robots.txt compliance validated
- ✅ **SC-007**: Halt on 3+ consecutive 5xx errors
- ✅ **SC-008**: Caching reduces duplicate requests
- ✅ **SC-009**: Raw data preserved immutably
- ✅ **SC-010**: Offline queries work without internet

---

## Development Methodology

This project was built using **Spec-Kit**, a systematic approach to software development:

1. **Specification** ([spec.md](specs/001-nzfishing-scraper/spec.md)): Requirements and user stories
2. **Planning** ([plan.md](specs/001-nzfishing-scraper/plan.md)): Tech stack and architecture
3. **Task Breakdown** ([tasks.md](specs/001-nzfishing-scraper/tasks.md)): 72 tasks across 9 phases
4. **Contracts** ([contracts/](specs/001-nzfishing-scraper/contracts/)): API and test specifications
5. **Implementation**: Phase-by-phase execution with TDD

**Current Status**: Phase 9 (Polish & Cross-Cutting) - 61/72 tasks complete (85%)

---

## Roadmap

### Completed Phases ✅

- Phase 1: Project Setup (7/7 tasks)
- Phase 2: Foundational Modules (18/18 tasks)
- Phase 3: US1 Region Discovery (8/8 tasks)
- Phase 5: US3 River Details (8/9 tasks)
- Phase 6: US4 Polite Crawling (8/8 tasks)
- Phase 7: US5 HTML Caching (6/6 tasks)
- Phase 9: Polish & Integration (3/10 tasks) - **IN PROGRESS**

### Pending Features 🚧

- Phase 4: US2 River Discovery (fixes needed, 7/32 tests failing)
- Phase 8: US6 PDF Export (deferred)

### Future Enhancements 🔮

- Web UI for data visualization
- Export to CSV/JSON formats
- GIS integration (map overlays)
- Multi-site support (configurable parsers)
- Incremental updates (delta scraping)

---

## Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature`
3. **Write tests**: Maintain ≥80% coverage
4. **Follow code style**: `black src/ tests/`
5. **Run tests**: `pytest tests/ -v`
6. **Submit pull request** with clear description

### Code Style

- **Formatter**: Black (line length 100)
- **Linter**: Flake8
- **Type Hints**: Required for public APIs
- **Docstrings**: Google style

---

## License

This project is licensed under the **MIT License**.

**Disclaimer**: This scraper is provided for educational and personal research purposes only. Users are solely responsible for compliance with applicable laws, terms of service, and ethical web scraping practices. The authors assume no liability for misuse.

---

## Acknowledgments

- **Spec-Kit Methodology**: Systematic development approach
- **pytest**: Testing framework
- **BeautifulSoup4**: HTML parsing
- **SQLite**: Embedded database
- **httpbin.org**: Testing infrastructure

---

## Support

- **Documentation**: See [docs/](docs/) directory
- **Issues**: [GitHub Issues](https://github.com/yourusername/fly_fishing_log/issues)
- **Tests**: Run `pytest -v` to validate installation

---

**Built with ❤️ for the fishing community. Scrape responsibly. 🎣**
