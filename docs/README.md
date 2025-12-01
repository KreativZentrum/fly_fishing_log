# NZ Flyfishing Web Scraper

**Status**: In Development (Phase 2 - Foundational Infrastructure)

A polite, constitution-compliant web scraper for extracting flyfishing information from nzfishing.com.

## Features

- **Polite Crawling**: 3-second delays, robots.txt compliance, automatic backoff
- **Data Integrity**: Raw HTML preservation, content hash tracking, no inference
- **Caching**: Configurable TTL, cache hit tracking, manual refresh support
- **Database**: SQLite with WAL mode, 6 normalized entities, FK constraints
- **PDF Export**: Template-driven river reports (coming in Phase 8)
- **CLI**: Simple command-line interface for scraping, querying, cache management

## Quick Start

### Installation

```bash
# Clone repository
git clone <repository-url>
cd fly_fishing_log

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r config/requirements.txt
```

### Configuration

Edit `config/nzfishing_config.yaml` to customize:
- Base URL and user agent
- Request delays and retry settings
- Cache directory and TTL
- Database and log paths
- PDF output directory

### Usage

```bash
# Scrape all regions and rivers (coming in Phase 3-5)
python -m src.cli scrape --all

# Query database
python -m src.cli query regions
python -m src.cli query rivers --region-id 1
python -m src.cli query river --river-id 42

# Cache management
python -m src.cli cache --stats
python -m src.cli cache --clear

# PDF generation (coming in Phase 8)
python -m src.cli pdf --river-id 42
```

## Development

### Running Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Contract tests
pytest tests/contract/ -v

# Coverage report
pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Linting
flake8 src/ tests/

# Formatting
black src/ tests/

# Type checking (optional)
mypy src/
```

## Project Structure

```
fly_fishing_log/
├── src/                    # Source code
│   ├── config.py          # Configuration loader
│   ├── logger.py          # Structured JSON logging
│   ├── storage.py         # SQLite database layer
│   ├── fetcher.py         # HTTP client with rate limiting
│   ├── parser.py          # HTML parsing (stubs)
│   ├── pdf_generator.py   # PDF export (stubs)
│   └── cli.py             # Command-line interface
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   ├── contract/          # Contract tests
│   └── fixtures/          # Test data and mock server
├── config/                 # Configuration files
│   ├── nzfishing_config.yaml
│   └── requirements.txt
├── database/               # Database schema
│   └── schema.sql
├── templates/              # PDF templates (coming Phase 8)
├── docs/                   # Documentation
└── .github/workflows/      # CI/CD pipeline
```

## Constitution Compliance

This scraper follows an 11-article constitution ensuring:

- **Article 2**: Robots.txt compliance, polite user agent
- **Article 3**: 3-second delays, exponential backoff, halt on 5xx errors
- **Article 5**: No inference, raw data preservation
- **Article 6**: Immutable raw data, content hash tracking
- **Article 8**: Centralized YAML configuration
- **Article 9**: Complete JSON logging with timestamps

See `docs/COMPLIANCE.md` for full details.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - System design and module interaction
- [Database Schema](docs/DATABASE.md) - Entity relationships and queries
- [Compliance](docs/COMPLIANCE.md) - Constitution and robots.txt policy
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

## License

[To be determined]

## Contributing

[To be determined]
