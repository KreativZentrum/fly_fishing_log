# Data Model: NZ Flyfishing Web Scraper

**Phase**: 1 — Design  
**Created**: 2025-11-30  
**Status**: Complete  
**Purpose**: Define SQLite schema and data entities for the scraper.

---

## Entity Diagram

```
Region (1) ──── (M) River
  │                  │
  │                  └─── (M) Section (reach)
  │                  │
  │                  └─── (M) Recommended_Fly
  │                  │
  │                  └─── (M) Regulation
  │
  └─── (M) Metadata (scrape sessions)
```

---

## Entity Definitions

### 1. Region

**Purpose**: Top-level geographic organization of fly-fishing areas.

**Attributes**:
- `id` (INTEGER PRIMARY KEY): Unique region ID (auto-increment).
- `name` (TEXT NOT NULL): Region name (e.g., "Northland", "Waikato").
- `slug` (TEXT UNIQUE NOT NULL): URL-friendly identifier (e.g., "northland").
- `canonical_url` (TEXT NOT NULL): Full URL on nzfishing.com (e.g., `https://nzfishing.com/northland`).
- `source_url` (TEXT): URL where this region was discovered (e.g., "Where to Fish" index).
- `raw_html` (TEXT): Raw HTML snippet from the index page.
- `description` (TEXT): Parsed description (if available; may be null).
- `crawl_timestamp` (TIMESTAMP): Last successful fetch time (UTC).
- `created_at` (TIMESTAMP): Record creation time.
- `updated_at` (TIMESTAMP): Record last update time.

**Constraints**:
- Primary key: `id`
- Unique: `slug`, `canonical_url`
- Foreign keys: None (top-level entity)

**Validation**:
- `name` and `canonical_url` MUST NOT be empty.
- `canonical_url` MUST match nzfishing.com domain.

---

### 2. River

**Purpose**: A river or waterway within a region, as a primary data entity.

**Attributes**:
- `id` (INTEGER PRIMARY KEY): Unique river ID.
- `region_id` (INTEGER NOT NULL): Foreign key to `regions.id`.
- `name` (TEXT NOT NULL): River name (e.g., "Waiterere River").
- `slug` (TEXT NOT NULL): URL-friendly identifier (e.g., "waiterere-river").
- `canonical_url` (TEXT NOT NULL): Full detail page URL.
- `source_url` (TEXT): URL where this river was discovered (region page).
- `raw_html` (TEXT): Raw HTML excerpt from the region's Fishing Waters section.
- `description` (TEXT): Parsed description or summary (if available).
- `crawl_timestamp` (TIMESTAMP): Last fetch time.
- `created_at` (TIMESTAMP): Record creation time.
- `updated_at` (TIMESTAMP): Record last update time.

**Constraints**:
- Primary key: `id`
- Foreign key: `region_id` → `regions.id` (ON DELETE CASCADE)
- Unique: `(region_id, slug)` (ensure unique slug per region)
- Unique: `canonical_url` (no duplicate URLs in system)

**Validation**:
- `name` and `canonical_url` MUST NOT be empty.
- `region_id` MUST reference an existing region.

---

### 3. Section (or Reach)

**Purpose**: Subdivisions of a river (e.g., Upper, Middle, Lower reaches) when applicable.

**Attributes**:
- `id` (INTEGER PRIMARY KEY): Unique section ID.
- `river_id` (INTEGER NOT NULL): Foreign key to `rivers.id`.
- `name` (TEXT NOT NULL): Section name (e.g., "Upper Waikato").
- `slug` (TEXT NOT NULL): URL-friendly identifier (e.g., "upper").
- `canonical_url` (TEXT): If the section has its own detail page; may be null if sections are subsections of a single river page.
- `raw_html` (TEXT): Raw HTML for this section (if parsed from a combined page).
- `description` (TEXT): Parsed description.
- `crawl_timestamp` (TIMESTAMP): Last fetch time.
- `created_at` (TIMESTAMP): Record creation time.
- `updated_at` (TIMESTAMP): Record last update time.

**Constraints**:
- Primary key: `id`
- Foreign key: `river_id` → `rivers.id` (ON DELETE CASCADE)
- Unique: `(river_id, slug)` (unique per river)

**Validation**:
- `name` MUST NOT be empty.
- `river_id` MUST reference an existing river.

---

### 4. Recommended_Fly

**Purpose**: A fly pattern recommended for a river, with raw and parsed data.

**Attributes**:
- `id` (INTEGER PRIMARY KEY): Unique fly ID.
- `river_id` (INTEGER NOT NULL): Foreign key to `rivers.id`.
- `section_id` (INTEGER): Optional foreign key to `sections.id` (if section-specific; may be null).
- `name` (TEXT NOT NULL): Fly name (e.g., "Pheasant Tail Nymph").
- `raw_text` (TEXT NOT NULL): Raw HTML/text from the "Recommended lures" section.
- `category` (TEXT): Parsed category (e.g., "nymph", "dry", "streamer"; may be null if unclassified).
- `size` (TEXT): Parsed size (e.g., "12", "16"; may be null).
- `color` (TEXT): Parsed color (e.g., "brown", "olive"; may be null).
- `notes` (TEXT): Additional notes (e.g., "Best in summer").
- `crawl_timestamp` (TIMESTAMP): When this was discovered.
- `created_at` (TIMESTAMP): Record creation time.
- `updated_at` (TIMESTAMP): Record last update time.

**Constraints**:
- Primary key: `id`
- Foreign key: `river_id` → `rivers.id` (ON DELETE CASCADE)
- Foreign key: `section_id` → `sections.id` (ON DELETE CASCADE, NULLABLE)

**Validation**:
- `name` and `raw_text` MUST NOT be empty.
- `river_id` MUST reference an existing river.

---

### 5. Regulation

**Purpose**: Regulations, conditions, or restrictions for a river.

**Attributes**:
- `id` (INTEGER PRIMARY KEY): Unique regulation ID.
- `river_id` (INTEGER NOT NULL): Foreign key to `rivers.id`.
- `section_id` (INTEGER): Optional foreign key to `sections.id` (section-specific).
- `type` (TEXT NOT NULL): Regulation type (e.g., "catch_limit", "season_dates", "method", "permit_required", "flow_status").
- `value` (TEXT NOT NULL): The regulation value (e.g., "12 fish per day", "November–April", "Fly only", "Yes", "Medium").
- `raw_text` (TEXT NOT NULL): Raw HTML/text from the page.
- `source_section` (TEXT): Page section where this came from (e.g., "Catch regulations").
- `crawl_timestamp` (TIMESTAMP): When discovered.
- `created_at` (TIMESTAMP): Record creation time.
- `updated_at` (TIMESTAMP): Record last update time.

**Constraints**:
- Primary key: `id`
- Foreign key: `river_id` → `rivers.id` (ON DELETE CASCADE)
- Foreign key: `section_id` → `sections.id` (ON DELETE CASCADE, NULLABLE)

**Validation**:
- `type`, `value`, and `raw_text` MUST NOT be empty.
- `river_id` MUST reference an existing river.

---

### 6. Metadata

**Purpose**: Track crawl sessions, record versions, and enable change detection.

**Attributes**:
- `id` (INTEGER PRIMARY KEY): Unique session ID.
- `session_id` (TEXT UNIQUE NOT NULL): A unique identifier for this scraper run (e.g., timestamp-based UUID).
- `entity_id` (INTEGER): The entity being versioned (region_id, river_id, etc.).
- `entity_type` (TEXT NOT NULL): Type of entity ("region", "river", "section", "fly", "regulation").
- `raw_content_hash` (TEXT): SHA256 hash of raw HTML/text (for change detection).
- `parsed_hash` (TEXT): SHA256 hash of parsed data (for change detection).
- `page_version` (TEXT): Version indicator (e.g., page layout version; optional).
- `crawl_timestamp` (TIMESTAMP NOT NULL): When this was fetched.
- `created_at` (TIMESTAMP): Record creation time.

**Constraints**:
- Primary key: `id`
- Unique: `(session_id, entity_id, entity_type)` (one entry per entity per session)

**Validation**:
- `session_id`, `entity_type`, `raw_content_hash` MUST NOT be empty.

---

## Schema Relationships

### Cardinality

- **Region → River**: One-to-many (1:M). Each region has multiple rivers.
- **River → Section**: One-to-many (1:M, optional). Rivers may or may not have sections.
- **River → Recommended_Fly**: One-to-many (1:M). Each river has multiple flies.
- **River → Regulation**: One-to-many (1:M). Each river has multiple regulations.
- **River → Metadata**: One-to-many (1:M). Each river's crawl history is tracked.

### Referential Integrity

- All foreign keys use `ON DELETE CASCADE` to simplify cleanup (deleting a region cascades to rivers, flies, regulations).
- No circular dependencies.

### Indexes

For performance (added to schema.sql):
- `idx_river_region_id` on `rivers(region_id)`
- `idx_fly_river_id` on `recommended_flies(river_id)`
- `idx_regulation_river_id` on `regulations(river_id)`
- `idx_metadata_entity` on `metadata(entity_type, entity_id, crawl_timestamp)`
- `idx_canonical_url_river` on `rivers(canonical_url)`
- `idx_canonical_url_region` on `regions(canonical_url)`

---

## Data Constraints & Validation Rules

### Article 5 & 6 Compliance

1. **Raw Data Immutability**: `raw_html` and `raw_text` fields MUST never be overwritten once set. If re-crawling, update `crawl_timestamp` and optionally insert a new record in `metadata` for versioning.

2. **No Inference**: Parsed fields (`category`, `size`, `color`, `notes`) may be NULL if they cannot be confidently extracted. NULL is preferred over guessing.

3. **Source Tracking**: Always populate `source_url` and `raw_html`/`raw_text` to trace where data came from.

4. **Timestamp Accuracy**: `crawl_timestamp` MUST reflect actual fetch time in UTC; never backfill or estimate.

---

## SQLite Schema (SQL)

```sql
-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Enable WAL mode for better concurrency
PRAGMA journal_mode = WAL;

-- Regions table
CREATE TABLE regions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    canonical_url TEXT NOT NULL UNIQUE,
    source_url TEXT,
    raw_html TEXT,
    description TEXT,
    crawl_timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rivers table
CREATE TABLE rivers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    canonical_url TEXT NOT NULL UNIQUE,
    source_url TEXT,
    raw_html TEXT,
    description TEXT,
    crawl_timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (region_id) REFERENCES regions(id) ON DELETE CASCADE,
    UNIQUE(region_id, slug)
);

-- Sections (reaches) table
CREATE TABLE sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    river_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    canonical_url TEXT,
    raw_html TEXT,
    description TEXT,
    crawl_timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (river_id) REFERENCES rivers(id) ON DELETE CASCADE,
    UNIQUE(river_id, slug)
);

-- Recommended flies table
CREATE TABLE recommended_flies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    river_id INTEGER NOT NULL,
    section_id INTEGER,
    name TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    category TEXT,
    size TEXT,
    color TEXT,
    notes TEXT,
    crawl_timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (river_id) REFERENCES rivers(id) ON DELETE CASCADE,
    FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE
);

-- Regulations table
CREATE TABLE regulations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    river_id INTEGER NOT NULL,
    section_id INTEGER,
    type TEXT NOT NULL,
    value TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    source_section TEXT,
    crawl_timestamp TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (river_id) REFERENCES rivers(id) ON DELETE CASCADE,
    FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE
);

-- Metadata table
CREATE TABLE metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    entity_id INTEGER,
    entity_type TEXT NOT NULL,
    raw_content_hash TEXT,
    parsed_hash TEXT,
    page_version TEXT,
    crawl_timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, entity_id, entity_type)
);

-- Indexes
CREATE INDEX idx_river_region_id ON rivers(region_id);
CREATE INDEX idx_fly_river_id ON recommended_flies(river_id);
CREATE INDEX idx_regulation_river_id ON regulations(river_id);
CREATE INDEX idx_metadata_entity ON metadata(entity_type, entity_id, crawl_timestamp);
CREATE INDEX idx_canonical_url_river ON rivers(canonical_url);
CREATE INDEX idx_canonical_url_region ON regions(canonical_url);
```

---

## Data Flow During Scraping

1. **Discovery (User Story 1)**: Fetch region index → parse → INSERT into `regions` table.
2. **Discovery (User Story 2)**: Fetch region page → parse "Fishing Waters" → INSERT into `rivers` table.
3. **Detail Extraction (User Story 3)**: Fetch river detail page → parse sections → INSERT into `sections`, `recommended_flies`, `regulations` tables.
4. **Versioning**: INSERT into `metadata` table tracking raw content hash and parse hash.

---

## Query Examples

### Find all rivers in Northland
```sql
SELECT r.name, r.canonical_url
FROM rivers r
JOIN regions reg ON r.region_id = reg.id
WHERE reg.slug = 'northland'
ORDER BY r.name;
```

### Find all flies recommended for Waiterere River
```sql
SELECT f.name, f.category, f.raw_text
FROM recommended_flies f
JOIN rivers r ON f.river_id = r.id
WHERE r.slug = 'waiterere-river'
ORDER BY f.name;
```

### Find rivers with catch limits
```sql
SELECT DISTINCT r.name, reg.name as region, reg.slug, reg.canonical_url
FROM rivers r
JOIN regulations reg_data ON r.id = reg_data.river_id
JOIN regions reg ON r.region_id = reg.id
WHERE reg_data.type = 'catch_limit'
ORDER BY reg.name, r.name;
```

### Check if a river has been updated since last run
```sql
SELECT r.name, MAX(m.crawl_timestamp) as last_crawl
FROM rivers r
LEFT JOIN metadata m ON r.id = m.entity_id AND m.entity_type = 'river'
WHERE r.slug = 'waiterere-river'
GROUP BY r.id;
```

---

## Future Enhancements (v1.1+)

- **Versioning table**: Track historical changes to parsed fields (e.g., if conditions change).
- **Full-text search**: Add FTS5 table for searching river names and descriptions.
- **Multi-site support**: Extend schema to include `site_id` and `site_name` for nzfishing.com alternatives.
- **Relationships**: Map rivers to nearby rivers or shared resources (e.g., same catchment).
- **Images/Maps**: Store URLs or local paths to associated images or map snippets.

---

## Phase 1 Completion Checklist

- [x] Entity definitions finalized.
- [x] Schema relationships documented (1:M, cascading deletes).
- [x] Raw data storage strategy aligned with Article 6.
- [x] Indexes designed for common queries.
- [x] SQL schema generated.
- [x] Data flow from discovery → detail extraction → storage defined.
- [x] Example queries provided.

**Next Phase**: Generate `contracts/` (module interfaces) and `quickstart.md`.
