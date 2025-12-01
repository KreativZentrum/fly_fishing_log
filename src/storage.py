"""
Storage module for NZ Flyfishing Web Scraper.
Article 6 Compliance: Raw data immutability, atomic operations, metadata tracking.
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from .exceptions import StorageError
from .logger import ScraperLogger


class Storage:
    """SQLite storage for scraper data."""

    def __init__(self, db_path: str, logger: ScraperLogger):
        """
        Initialize storage and connect to database.

        Args:
            db_path: Path to SQLite database file
            logger: Logger instance
        """
        self.db_path = Path(db_path)
        self.logger = logger
        self.conn = None

        # Create database directory if needed
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Connect and initialize
        self._connect()
        self.initialize_schema()

    def _connect(self):
        """Establish database connection with proper settings."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")

    def initialize_schema(self):
        """Create database schema from schema.sql (idempotent)."""
        schema_path = Path("database/schema.sql")

        if not schema_path.exists():
            raise StorageError(f"Schema file not found: {schema_path}")

        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        try:
            self.conn.executescript(schema_sql)
            self.conn.commit()
            self.logger.debug("Database schema initialized")
        except sqlite3.Error as e:
            raise StorageError(f"Failed to initialize schema: {e}")

    def begin_transaction(self):
        """Begin a database transaction."""
        self.conn.execute("BEGIN")

    def commit(self):
        """Commit current transaction."""
        self.conn.commit()

    def rollback(self):
        """Rollback current transaction."""
        self.conn.rollback()

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    # Region operations

    def insert_region(self, region: Dict = None, **kwargs) -> int:
        """
        Insert or update a region.

        Args:
            region: Dict with keys: name, slug, canonical_url, source_url,
                   raw_html, description, crawl_timestamp
            **kwargs: Alternative to passing dict (for backward compatibility)

        Returns:
            Region ID
        """
        if region is None:
            region = kwargs

        try:
            cursor = self.conn.execute(
                """
                INSERT INTO regions (
                    name, slug, canonical_url, source_url, raw_html,
                    description, crawl_timestamp, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(canonical_url) DO UPDATE SET
                    name = excluded.name,
                    slug = excluded.slug,
                    raw_html = excluded.raw_html,
                    description = excluded.description,
                    crawl_timestamp = excluded.crawl_timestamp,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
                """,
                (
                    region["name"],
                    region["slug"],
                    region["canonical_url"],
                    region.get("source_url"),
                    region.get("raw_html"),
                    region.get("description"),
                    region["crawl_timestamp"],
                ),
            )
            region_id = cursor.fetchone()[0]
            self.conn.commit()
            return region_id
        except sqlite3.Error as e:
            self.conn.rollback()
            raise StorageError(f"Failed to insert region: {e}")

    def get_region(self, region_id: int) -> Optional[Dict]:
        """Get region by ID."""
        cursor = self.conn.execute("SELECT * FROM regions WHERE id = ?", (region_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_regions(self, limit: int = 1000) -> List[Dict]:
        """Get all regions."""
        cursor = self.conn.execute("SELECT * FROM regions ORDER BY name LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def get_uncrawled_regions(self) -> List[Dict]:
        """Get regions with null crawl_timestamp."""
        cursor = self.conn.execute("SELECT * FROM regions WHERE crawl_timestamp IS NULL")
        return [dict(row) for row in cursor.fetchall()]

    # River operations

    def insert_river(self, river: Dict = None, **kwargs) -> int:
        """
        Insert or update a river.

        Args:
            river: Dict with keys: region_id, name, slug, canonical_url,
                  source_url, raw_html, description, crawl_timestamp
            **kwargs: Alternative to passing dict (for backward compatibility)

        Returns:
            River ID
        """
        if river is None:
            river = kwargs

        try:
            cursor = self.conn.execute(
                """
                INSERT INTO rivers (
                    region_id, name, slug, canonical_url, source_url,
                    raw_html, description, crawl_timestamp, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(canonical_url) DO UPDATE SET
                    name = excluded.name,
                    slug = excluded.slug,
                    raw_html = excluded.raw_html,
                    description = excluded.description,
                    crawl_timestamp = excluded.crawl_timestamp,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
                """,
                (
                    river["region_id"],
                    river["name"],
                    river["slug"],
                    river["canonical_url"],
                    river.get("source_url"),
                    river.get("raw_html"),
                    river.get("description"),
                    river["crawl_timestamp"],
                ),
            )
            river_id = cursor.fetchone()[0]
            self.conn.commit()
            return river_id
        except sqlite3.Error as e:
            self.conn.rollback()
            raise StorageError(f"Failed to insert river: {e}")

    def get_river(self, river_id: int) -> Optional[Dict]:
        """Get river by ID."""
        cursor = self.conn.execute("SELECT * FROM rivers WHERE id = ?", (river_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_rivers(self, limit: int = 10000) -> List[Dict]:
        """Get all rivers."""
        cursor = self.conn.execute("SELECT * FROM rivers ORDER BY name LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def get_rivers_by_region(self, region_id: int) -> List[Dict]:
        """Get all rivers in a region."""
        cursor = self.conn.execute(
            "SELECT * FROM rivers WHERE region_id = ? ORDER BY name", (region_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    # Section operations

    def insert_section(self, section: Dict) -> int:
        """Insert or update a section."""
        try:
            cursor = self.conn.execute(
                """
                INSERT INTO sections (
                    river_id, name, slug, canonical_url, raw_html,
                    description, crawl_timestamp, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(river_id, slug) DO UPDATE SET
                    crawl_timestamp = excluded.crawl_timestamp,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
                """,
                (
                    section["river_id"],
                    section["name"],
                    section["slug"],
                    section.get("canonical_url"),
                    section.get("raw_html"),
                    section.get("description"),
                    section["crawl_timestamp"],
                ),
            )
            section_id = cursor.fetchone()[0]
            self.conn.commit()
            return section_id
        except sqlite3.Error as e:
            self.conn.rollback()
            raise StorageError(f"Failed to insert section: {e}")

    def get_sections_by_river(self, river_id: int) -> List[Dict]:
        """Get all sections for a river."""
        cursor = self.conn.execute(
            "SELECT * FROM sections WHERE river_id = ? ORDER BY name", (river_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    # Fly operations

    def insert_fly(self, fly: Dict = None, **kwargs) -> int:
        """Insert a recommended fly."""
        if fly is None:
            fly = kwargs

        try:
            cursor = self.conn.execute(
                """
                INSERT INTO recommended_flies (
                    river_id, section_id, name, raw_text, category,
                    size, color, notes, crawl_timestamp, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                RETURNING id
                """,
                (
                    fly["river_id"],
                    fly.get("section_id"),
                    fly["name"],
                    fly["raw_text"],
                    fly.get("category"),
                    fly.get("size"),
                    fly.get("color"),
                    fly.get("notes"),
                    fly["crawl_timestamp"],
                ),
            )
            fly_id = cursor.fetchone()[0]
            self.conn.commit()
            return fly_id
        except sqlite3.Error as e:
            self.conn.rollback()
            raise StorageError(f"Failed to insert fly: {e}")

    def get_flies_by_river(self, river_id: int) -> List[Dict]:
        """Get all flies for a river."""
        cursor = self.conn.execute(
            "SELECT * FROM recommended_flies WHERE river_id = ? ORDER BY name", (river_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    # Regulation operations

    def insert_regulation(self, regulation: Dict = None, **kwargs) -> int:
        """Insert a regulation."""
        if regulation is None:
            regulation = kwargs

        try:
            cursor = self.conn.execute(
                """
                INSERT INTO regulations (
                    river_id, section_id, type, value, raw_text,
                    source_section, crawl_timestamp, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                RETURNING id
                """,
                (
                    regulation["river_id"],
                    regulation.get("section_id"),
                    regulation["type"],
                    regulation["value"],
                    regulation["raw_text"],
                    regulation.get("source_section"),
                    regulation["crawl_timestamp"],
                ),
            )
            reg_id = cursor.fetchone()[0]
            self.conn.commit()
            return reg_id
        except sqlite3.Error as e:
            self.conn.rollback()
            raise StorageError(f"Failed to insert regulation: {e}")

    def get_regulations_by_river(self, river_id: int) -> List[Dict]:
        """Get all regulations for a river."""
        cursor = self.conn.execute(
            "SELECT * FROM regulations WHERE river_id = ? ORDER BY type", (river_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    # Metadata operations

    def insert_metadata(self, metadata: Dict = None, **kwargs) -> int:
        """Insert crawl metadata."""
        if metadata is None:
            metadata = kwargs

        try:
            cursor = self.conn.execute(
                """
                INSERT INTO metadata (
                    session_id, entity_id, entity_type, raw_content_hash,
                    parsed_hash, page_version, crawl_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id, entity_id, entity_type) DO UPDATE SET
                    raw_content_hash = excluded.raw_content_hash,
                    parsed_hash = excluded.parsed_hash,
                    crawl_timestamp = excluded.crawl_timestamp
                RETURNING id
                """,
                (
                    metadata["session_id"],
                    metadata.get("entity_id"),
                    metadata["entity_type"],
                    metadata.get("raw_content_hash"),
                    metadata.get("parsed_hash"),
                    metadata.get("page_version"),
                    metadata["crawl_timestamp"],
                ),
            )
            meta_id = cursor.fetchone()[0]
            self.conn.commit()
            return meta_id
        except sqlite3.Error as e:
            self.conn.rollback()
            raise StorageError(f"Failed to insert metadata: {e}")

    def get_latest_crawl_for_entity(self, entity_type: str, entity_id: int) -> Optional[Dict]:
        """Get latest metadata for an entity."""
        cursor = self.conn.execute(
            """
            SELECT * FROM metadata
            WHERE entity_type = ? AND entity_id = ?
            ORDER BY crawl_timestamp DESC LIMIT 1
            """,
            (entity_type, entity_id),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_metadata_by_entity(self, entity_type: str, entity_id: int) -> Optional[Dict]:
        """Get metadata for an entity (alias for get_latest_crawl_for_entity)."""
        return self.get_latest_crawl_for_entity(entity_type, entity_id)

    # Batch operations

    def batch_insert_regions(self, regions: List[Dict]) -> List[int]:
        """Insert multiple regions in a transaction."""
        region_ids = []
        try:
            self.begin_transaction()
            for region in regions:
                region_id = self.insert_region(region)
                region_ids.append(region_id)
            self.commit()
            return region_ids
        except Exception as e:
            self.rollback()
            raise StorageError(f"Batch insert failed: {e}")

    def batch_insert_rivers(self, rivers: List[Dict]) -> List[int]:
        """Insert multiple rivers in a transaction."""
        river_ids = []
        try:
            self.begin_transaction()
            for river in rivers:
                river_id = self.insert_river(river)
                river_ids.append(river_id)
            self.commit()
            return river_ids
        except Exception as e:
            self.rollback()
            raise StorageError(f"Batch insert failed: {e}")

    # Utility queries

    def count_regions(self) -> int:
        """Count total regions."""
        cursor = self.conn.execute("SELECT COUNT(*) FROM regions")
        return cursor.fetchone()[0]

    def count_rivers(self) -> int:
        """Count total rivers."""
        cursor = self.conn.execute("SELECT COUNT(*) FROM rivers")
        return cursor.fetchone()[0]

    def has_changed(self, entity_type: str, entity_id: int, content_hash: str) -> bool:
        """Check if entity content has changed since last crawl."""
        cursor = self.conn.execute(
            """
            SELECT raw_content_hash FROM metadata
            WHERE entity_type = ? AND entity_id = ?
            ORDER BY crawl_timestamp DESC LIMIT 1
            """,
            (entity_type, entity_id),
        )
        row = cursor.fetchone()

        if not row:
            return True  # No previous crawl, consider changed

        return row[0] != content_hash
