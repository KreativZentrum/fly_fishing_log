-- NZ Flyfishing Web Scraper Database Schema
-- SQLite 3.x
-- Created: 2025-11-30
-- Article 6 Compliance: Raw data immutability, source tracking, metadata versioning

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Enable WAL mode for better concurrency
PRAGMA journal_mode = WAL;

-- Regions table
CREATE TABLE IF NOT EXISTS regions (
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
CREATE TABLE IF NOT EXISTS rivers (
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
CREATE TABLE IF NOT EXISTS sections (
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
CREATE TABLE IF NOT EXISTS recommended_flies (
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
CREATE TABLE IF NOT EXISTS regulations (
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

-- Metadata table (for change detection and versioning)
CREATE TABLE IF NOT EXISTS metadata (
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

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_river_region_id ON rivers(region_id);
CREATE INDEX IF NOT EXISTS idx_fly_river_id ON recommended_flies(river_id);
CREATE INDEX IF NOT EXISTS idx_regulation_river_id ON regulations(river_id);
CREATE INDEX IF NOT EXISTS idx_metadata_entity ON metadata(entity_type, entity_id, crawl_timestamp);
CREATE INDEX IF NOT EXISTS idx_canonical_url_river ON rivers(canonical_url);
CREATE INDEX IF NOT EXISTS idx_canonical_url_region ON regions(canonical_url);
