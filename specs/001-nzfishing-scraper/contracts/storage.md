# Contract: Storage Module

**Purpose**: Define the interface for SQLite database operations.  
**Compliance**: Article 6 (data storage with raw + structured separation).

---

## Module: `src/storage.py`

### Responsibility

Manage SQLite database for storing regions, rivers, sections, flies, regulations, and metadata. Ensure:
- Raw data is never overwritten
- Schema is initialized on first run
- CRUD operations are atomic
- Queries support discovery, filtering, and change detection

### Interface

```python
class Storage:
    """SQLite storage for scraper data."""
    
    def __init__(self, db_path: str, logger: Logger):
        """
        Initialize storage and connect to database.
        
        Args:
            db_path (str): Path to SQLite database file
            logger: Logger instance
        
        Side effects:
            - Creates database file if it doesn't exist
            - Initializes schema (regions, rivers, etc.)
            - Enables foreign keys and WAL mode
        """
        pass
    
    def initialize_schema(self) -> None:
        """
        Create database schema (idempotent).
        
        Side effects:
            - Reads schema.sql from database/ directory
            - Executes CREATE TABLE statements (only if tables don't exist)
            - Logs initialization
        """
        pass
    
    # Region operations
    
    def insert_region(self, region: dict) -> int:
        """
        Insert or update a region.
        
        Args:
            region (dict): Region record with keys:
                - name (str, required)
                - slug (str, required)
                - canonical_url (str, required)
                - source_url (str, optional)
                - raw_html (str, optional)
                - description (str, optional)
                - crawl_timestamp (datetime, required)
        
        Returns:
            int: Region ID (new or existing)
        
        Side effects:
            - Inserts new row or updates existing (by canonical_url)
            - Updates crawl_timestamp, updated_at
            - Logs operation
        
        Raises:
            StorageError: On database error
        """
        pass
    
    def get_region(self, region_id: int) -> dict or None:
        """Get a region by ID."""
        pass
    
    def get_regions(self, limit: int = 1000) -> list[dict]:
        """Get all regions."""
        pass
    
    # River operations
    
    def insert_river(self, river: dict) -> int:
        """
        Insert or update a river.
        
        Args:
            river (dict): River record with keys:
                - region_id (int, required, FK)
                - name (str, required)
                - slug (str, required)
                - canonical_url (str, required)
                - source_url (str, optional)
                - raw_html (str, optional)
                - description (str, optional)
                - crawl_timestamp (datetime, required)
        
        Returns:
            int: River ID
        
        Side effects:
            - Inserts or updates (by canonical_url)
            - Never overwrites raw_html if already set
            - Logs operation
        
        Raises:
            StorageError: On FK violation or database error
        """
        pass
    
    def get_river(self, river_id: int) -> dict or None:
        """Get a river by ID."""
        pass
    
    def get_rivers_by_region(self, region_id: int) -> list[dict]:
        """Get all rivers in a region."""
        pass
    
    def get_rivers(self, limit: int = 1000) -> list[dict]:
        """Get all rivers."""
        pass
    
    # Section operations
    
    def insert_section(self, section: dict) -> int:
        """
        Insert a section/reach.
        
        Args:
            section (dict): Section record with keys:
                - river_id (int, required)
                - name (str, required)
                - slug (str, required)
                - canonical_url (str, optional)
                - raw_html (str, optional)
                - crawl_timestamp (datetime, required)
        
        Returns:
            int: Section ID
        """
        pass
    
    def get_sections_by_river(self, river_id: int) -> list[dict]:
        """Get all sections for a river."""
        pass
    
    # Recommended fly operations
    
    def insert_fly(self, fly: dict) -> int:
        """
        Insert a recommended fly.
        
        Args:
            fly (dict): Fly record with keys:
                - river_id (int, required)
                - section_id (int, optional)
                - name (str, required)
                - raw_text (str, required)
                - category (str, optional)
                - size (str, optional)
                - color (str, optional)
                - notes (str, optional)
                - crawl_timestamp (datetime, required)
        
        Returns:
            int: Fly ID
        """
        pass
    
    def get_flies_by_river(self, river_id: int, section_id: int or None = None) -> list[dict]:
        """Get flies for a river (optionally filtered by section)."""
        pass
    
    # Regulation operations
    
    def insert_regulation(self, regulation: dict) -> int:
        """
        Insert a regulation.
        
        Args:
            regulation (dict): Regulation record with keys:
                - river_id (int, required)
                - section_id (int, optional)
                - type (str, required)  # e.g., 'catch_limit', 'season_dates'
                - value (str, required)
                - raw_text (str, required)
                - source_section (str, optional)
                - crawl_timestamp (datetime, required)
        
        Returns:
            int: Regulation ID
        """
        pass
    
    def get_regulations_by_river(self, river_id: int, reg_type: str or None = None) -> list[dict]:
        """Get regulations for a river (optionally filtered by type)."""
        pass
    
    # Metadata operations (change detection)
    
    def insert_metadata(self, metadata: dict) -> int:
        """
        Insert crawl metadata for change detection.
        
        Args:
            metadata (dict): Metadata record with keys:
                - session_id (str, required)
                - entity_id (int, required)
                - entity_type (str, required)  # 'region', 'river', etc.
                - raw_content_hash (str, optional)
                - parsed_hash (str, optional)
                - crawl_timestamp (datetime, required)
        
        Returns:
            int: Metadata ID
        """
        pass
    
    def get_latest_crawl_for_entity(self, entity_id: int, entity_type: str) -> dict or None:
        """Get the most recent crawl metadata for an entity."""
        pass
    
    # Batch operations (transactions)
    
    def begin_transaction(self) -> None:
        """Start a transaction."""
        pass
    
    def commit(self) -> None:
        """Commit current transaction."""
        pass
    
    def rollback(self) -> None:
        """Rollback current transaction."""
        pass
    
    def batch_insert_regions(self, regions: list[dict]) -> list[int]:
        """Batch insert regions within a transaction."""
        pass
    
    def batch_insert_rivers(self, rivers: list[dict]) -> list[int]:
        """Batch insert rivers within a transaction."""
        pass
    
    # Utility queries
    
    def count_regions(self) -> int:
        """Total number of regions."""
        pass
    
    def count_rivers(self, region_id: int or None = None) -> int:
        """Total number of rivers (optionally filtered by region)."""
        pass
    
    def has_changed(self, entity_id: int, entity_type: str, content_hash: str) -> bool:
        """Check if content has changed since last crawl."""
        pass
    
    def get_uncrawled_regions(self, since: datetime or None = None) -> list[dict]:
        """Get regions that have never been crawled or not crawled since a date."""
        pass
    
    def close(self) -> None:
        """Close database connection and cleanup."""
        pass
```

### Expected Behavior

**Atomicity**:
- Each insert/update is wrapped in a transaction.
- Batch operations use explicit transactions.
- Failures roll back changes; logs indicate failure reason.

**Raw Data Immutability**:
- Once `raw_html` is set, it is never overwritten.
- Updates only change `crawl_timestamp`, `updated_at`, and parsed fields.

**Concurrency**:
- SQLite WAL mode enables read-while-write capability.
- For single-threaded scraper, concurrency is not critical but WAL improves reliability.

**Change Detection**:
- Store content hash in `metadata` table.
- `has_changed()` compares new hash with latest metadata; helps detect if re-crawl is needed.

### Data Contracts

**Input**:
- Dicts matching entity schemas (regions, rivers, flies, regulations)
- Database path (string)

**Output**:
- Entity IDs (integers)
- Query result lists (dicts with all columns)

**Invariants**:
- Foreign keys are enforced (Article 6)
- Timestamps are UTC and accurate
- Raw data is preserved

### Testing Strategy

- Unit tests: Mock SQLite connection; test insert/update/query logic.
- Integration tests: Use in-memory SQLite database (`:memory:`); verify schema and operations.
- Test change detection logic (hash comparison).
- Test batch inserts with transactions.
- Test FK constraints (try inserting river with invalid region_id; expect error).

---

## Exception Hierarchy

```python
class StorageError(Exception):
    """Database operation error."""
    pass

class IntegrityError(StorageError):
    """FK violation or constraint error."""
    pass
```

---

## Database Initialization

```python
# On first run:
storage = Storage('nzfishing.db', logger)
storage.initialize_schema()  # Idempotent; reads database/schema.sql
```

---

## Usage Example

```python
# Insert a region
region_id = storage.insert_region({
    'name': 'Northland',
    'slug': 'northland',
    'canonical_url': 'https://nzfishing.com/northland',
    'source_url': 'https://nzfishing.com/where-to-fish',
    'raw_html': '<div class="region">...',
    'crawl_timestamp': datetime.utcnow()
})

# Get all rivers in a region
rivers = storage.get_rivers_by_region(region_id)

# Batch insert rivers
river_ids = storage.batch_insert_rivers([
    {
        'region_id': region_id,
        'name': 'Waiterere River',
        'slug': 'waiterere-river',
        'canonical_url': 'https://nzfishing.com/northland/waiterere-river',
        'raw_html': '<div>...',
        'crawl_timestamp': datetime.utcnow()
    },
    # ... more rivers
])

# Query regulations
catch_limits = storage.get_regulations_by_river(123, reg_type='catch_limit')
```

---

## Compliance Notes

- **Article 6 (Data Storage Principles)**: Raw data never overwritten; schema distinguishes entities; metadata tracks versions.
- **Article 8 (Predictability)**: Deterministic queries; consistent schema; transactional integrity.
