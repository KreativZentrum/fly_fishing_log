# Database Schema

## Overview

SQLite 3.x database with WAL mode, foreign key constraints, and content hash tracking.

**File**: `database/nzfishing.db` (configurable via `database_path` in config)

## Entity Relationship Diagram

```
┌──────────────┐
│   regions    │
│──────────────│
│ id (PK)      │
│ name         │
│ slug (UNIQUE)│
│ canonical_url│
│ source_url   │
│ raw_html     │
│ description  │
└──────┬───────┘
       │ 1:N
       ▼
┌──────────────┐
│    rivers    │
│──────────────│
│ id (PK)      │
│ region_id (FK)│  ┌──────────────────┐
│ name         │  │    metadata      │
│ slug         │  │──────────────────│
│ canonical_url│  │ id (PK)          │
│ raw_html     │  │ session_id       │
└──────┬───────┘  │ entity_id        │
       │ 1:N      │ entity_type      │
       ├──────────┤ raw_content_hash │
       │          │ parsed_hash      │
       ▼          │ page_version     │
┌──────────────┐  │ crawl_timestamp  │
│   sections   │  └──────────────────┘
│──────────────│
│ id (PK)      │
│ river_id (FK)│
│ name         │
│ slug         │
│ canonical_url│
│ raw_html     │
└──────┬───────┘
       │ 1:N
       ├─────────────┬──────────────┐
       ▼             ▼              ▼
┌─────────────────┐ ┌─────────────────┐
│recommended_flies│ │  regulations    │
│─────────────────│ │─────────────────│
│ id (PK)         │ │ id (PK)         │
│ river_id (FK)   │ │ river_id (FK)   │
│ section_id (FK) │ │ section_id (FK) │
│ name            │ │ type            │
│ raw_text        │ │ value           │
│ category        │ │ raw_text        │
│ size            │ │ source_section  │
│ color           │ └─────────────────┘
│ notes           │
└─────────────────┘
```

## Table Definitions

### regions

Stores flyfishing regions (e.g., "North Island", "South Island").

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique region ID |
| name | TEXT | NOT NULL | Display name (e.g., "North Island") |
| slug | TEXT | NOT NULL UNIQUE | URL-safe identifier |
| canonical_url | TEXT | NOT NULL UNIQUE | Authoritative URL for region |
| source_url | TEXT | NOT NULL | Original discovery URL |
| raw_html | TEXT | | Preserved HTML content (Article 6.4) |
| description | TEXT | | Region overview text |
| crawl_timestamp | TEXT | NOT NULL | ISO 8601 timestamp of crawl |
| created_at | TEXT | DEFAULT CURRENT_TIMESTAMP | Record creation time |
| updated_at | TEXT | DEFAULT CURRENT_TIMESTAMP | Last update time |

**Indexes**:
- `idx_canonical_url_region` on `canonical_url`

### rivers

Stores individual rivers within regions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique river ID |
| region_id | INTEGER | NOT NULL REFERENCES regions(id) ON DELETE CASCADE | Parent region |
| name | TEXT | NOT NULL | River name (e.g., "Tongariro River") |
| slug | TEXT | NOT NULL | URL-safe identifier |
| canonical_url | TEXT | NOT NULL UNIQUE | Authoritative URL for river |
| raw_html | TEXT | | Preserved detail page HTML |
| crawl_timestamp | TEXT | NOT NULL | ISO 8601 timestamp of crawl |
| created_at | TEXT | DEFAULT CURRENT_TIMESTAMP | Record creation time |
| updated_at | TEXT | DEFAULT CURRENT_TIMESTAMP | Last update time |

**Constraints**:
- `UNIQUE(region_id, slug)`: No duplicate slugs within region

**Indexes**:
- `idx_river_region_id` on `region_id`
- `idx_canonical_url_river` on `canonical_url`

### sections

Stores named sections/pools within rivers.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique section ID |
| river_id | INTEGER | NOT NULL REFERENCES rivers(id) ON DELETE CASCADE | Parent river |
| name | TEXT | NOT NULL | Section name (e.g., "Red Hut Pool") |
| slug | TEXT | NOT NULL | URL-safe identifier |
| canonical_url | TEXT | | Section-specific URL if available |
| raw_html | TEXT | | Preserved section HTML |
| created_at | TEXT | DEFAULT CURRENT_TIMESTAMP | Record creation time |
| updated_at | TEXT | DEFAULT CURRENT_TIMESTAMP | Last update time |

**Constraints**:
- `UNIQUE(river_id, slug)`: No duplicate slugs within river

### recommended_flies

Stores fly recommendations per river or section.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique fly ID |
| river_id | INTEGER | NOT NULL REFERENCES rivers(id) ON DELETE CASCADE | Parent river |
| section_id | INTEGER | REFERENCES sections(id) ON DELETE CASCADE | Specific section (nullable) |
| name | TEXT | NOT NULL | Fly pattern name (e.g., "Royal Wulff") |
| raw_text | TEXT | NOT NULL | Exact text from source (Article 5.1) |
| category | TEXT | | Dry/Nymph/Streamer (nullable per Article 5.2) |
| size | TEXT | | Hook size (nullable) |
| color | TEXT | | Color description (nullable) |
| notes | TEXT | | Additional notes |
| crawl_timestamp | TEXT | NOT NULL | ISO 8601 timestamp of crawl |
| created_at | TEXT | DEFAULT CURRENT_TIMESTAMP | Record creation time |
| updated_at | TEXT | DEFAULT CURRENT_TIMESTAMP | Last update time |

**Indexes**:
- `idx_fly_river_id` on `river_id`

**Article 5.2 Compliance**: `category`, `size`, `color` remain NULL unless explicitly stated in source.

### regulations

Stores fishing regulations per river or section.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique regulation ID |
| river_id | INTEGER | NOT NULL REFERENCES rivers(id) ON DELETE CASCADE | Parent river |
| section_id | INTEGER | REFERENCES sections(id) ON DELETE CASCADE | Specific section (nullable) |
| type | TEXT | NOT NULL | Regulation type (e.g., "Bag Limit", "Season") |
| value | TEXT | NOT NULL | Regulation value (e.g., "2 fish per day") |
| raw_text | TEXT | NOT NULL | Exact text from source |
| source_section | TEXT | | HTML section where found |
| crawl_timestamp | TEXT | NOT NULL | ISO 8601 timestamp of crawl |
| created_at | TEXT | DEFAULT CURRENT_TIMESTAMP | Record creation time |
| updated_at | TEXT | DEFAULT CURRENT_TIMESTAMP | Last update time |

**Indexes**:
- `idx_regulation_river_id` on `river_id`

### metadata

Tracks scraping metadata and content hashes for change detection.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique metadata ID |
| session_id | TEXT | NOT NULL | Scraping session UUID |
| entity_id | INTEGER | NOT NULL | ID of region/river/section |
| entity_type | TEXT | NOT NULL | "region", "river", or "section" |
| raw_content_hash | TEXT | NOT NULL | MD5 hash of raw HTML |
| parsed_hash | TEXT | | MD5 hash of parsed data (JSON) |
| page_version | TEXT | | Version/ETag if available |
| crawl_timestamp | TEXT | NOT NULL | ISO 8601 timestamp of crawl |

**Constraints**:
- `UNIQUE(session_id, entity_id, entity_type)`: One metadata record per entity per session

**Indexes**:
- `idx_metadata_entity` on `(entity_id, entity_type)`

## Common Queries

### Get all regions
```sql
SELECT * FROM regions ORDER BY name;
```

### Get rivers in a region
```sql
SELECT * FROM rivers 
WHERE region_id = ? 
ORDER BY name;
```

### Get river details with sections
```sql
SELECT r.*, s.name as section_name
FROM rivers r
LEFT JOIN sections s ON s.river_id = r.id
WHERE r.id = ?;
```

### Get flies for a river
```sql
SELECT * FROM recommended_flies
WHERE river_id = ?
ORDER BY name;
```

### Get regulations for a river
```sql
SELECT * FROM regulations
WHERE river_id = ?
ORDER BY type;
```

### Find uncrawled regions
```sql
SELECT * FROM regions
WHERE crawl_timestamp IS NULL OR crawl_timestamp = '';
```

### Check if content changed (Article 6.4)
```sql
SELECT raw_content_hash FROM metadata
WHERE entity_id = ? AND entity_type = ?
ORDER BY crawl_timestamp DESC
LIMIT 1;
```

## Data Integrity Rules

### Foreign Key Constraints
- **ON DELETE CASCADE**: Deleting a region deletes all its rivers, sections, flies, regulations
- **Enforced**: `PRAGMA foreign_keys = ON` in all connections

### Unique Constraints
- **Canonical URLs**: Globally unique per entity type (regions, rivers)
- **Slugs**: Unique within parent (region_id+slug, river_id+slug)

### Timestamps
- **created_at**: Set once on INSERT
- **updated_at**: Updated on every UPDATE (manually in app)
- **crawl_timestamp**: User-provided ISO 8601 timestamp

### Content Preservation (Article 6.4)
- **raw_html**: Never overwritten, only appended via upsert
- **Upsert pattern**: `ON CONFLICT(canonical_url) DO UPDATE SET ...`
- **Change detection**: Compare new `raw_content_hash` with latest in `metadata`

## Performance Optimization

### WAL Mode
```sql
PRAGMA journal_mode = WAL;
```
- Allows concurrent reads during writes
- Better performance for scraping workflow

### Row Factory
```python
conn.row_factory = sqlite3.Row
```
- Access columns by name: `row['name']`
- More maintainable than index access

### Batch Inserts
- Use transactions for bulk operations
- `batch_insert_regions()`, `batch_insert_rivers()` in Storage

### Index Usage
- Indexes on all foreign keys (`region_id`, `river_id`, `section_id`)
- Indexes on unique identifiers (`canonical_url`)
- Composite index on `(entity_id, entity_type)` for metadata lookups

## Schema Initialization

**File**: `database/schema.sql`

**Execution**:
```python
storage = Storage('database/nzfishing.db')
storage.initialize_schema()  # Idempotent
```

**Idempotence**: Uses `CREATE TABLE IF NOT EXISTS`, safe to run multiple times.

## Backup and Migration

### Backup
```bash
sqlite3 database/nzfishing.db ".backup database/backup.db"
```

### Export to CSV
```bash
sqlite3 database/nzfishing.db -csv -header "SELECT * FROM rivers" > rivers.csv
```

### Schema Version
- No formal migrations yet
- Consider adding `schema_version` table for future migrations

## Testing

### Test Database
- Created per test in `temp_dir` (pytest fixture)
- Schema initialized via `storage.initialize_schema()`
- Cleaned up automatically after test

### Fixtures
- `test_storage`: Initialized empty database
- `populated_storage`: Database with 1 region, 1 river
- Sample data: `sample_region_data`, `sample_river_data`, etc.

## Future Schema Changes

Potential additions (not in current scope):
- `access_notes` table for parking/access information
- `images` table for storing image URLs/captions
- `species` table for fish species per river
- `weather` table for historical conditions
- `user_reports` table for crowd-sourced updates
