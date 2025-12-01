"""
Data models for NZ Flyfishing Web Scraper.
Article 6 Compliance: Raw data immutability, validation rules.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Region:
    """Represents a fly-fishing region."""

    name: str
    slug: str
    canonical_url: str
    source_url: Optional[str] = None
    raw_html: Optional[str] = None
    description: Optional[str] = None
    crawl_timestamp: Optional[datetime] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate required fields."""
        if not self.name:
            raise ValueError("Region name cannot be empty")
        if not self.canonical_url:
            raise ValueError("Region canonical_url cannot be empty")
        if not self.canonical_url.startswith("http"):
            raise ValueError("Region canonical_url must be a valid HTTP(S) URL")


@dataclass
class River:
    """Represents a river within a region."""

    name: str
    slug: str
    canonical_url: str
    region_id: int
    source_url: Optional[str] = None
    raw_html: Optional[str] = None
    description: Optional[str] = None
    crawl_timestamp: Optional[datetime] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate required fields."""
        if not self.name:
            raise ValueError("River name cannot be empty")
        if not self.canonical_url:
            raise ValueError("River canonical_url cannot be empty")
        if not self.region_id:
            raise ValueError("River must have a region_id")


@dataclass
class Section:
    """Represents a section/reach of a river."""

    name: str
    slug: str
    river_id: int
    canonical_url: Optional[str] = None
    raw_html: Optional[str] = None
    description: Optional[str] = None
    crawl_timestamp: Optional[datetime] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate required fields."""
        if not self.name:
            raise ValueError("Section name cannot be empty")
        if not self.river_id:
            raise ValueError("Section must have a river_id")


@dataclass
class Fly:
    """Represents a recommended fly pattern."""

    name: str
    raw_text: str
    river_id: int
    section_id: Optional[int] = None
    category: Optional[str] = None  # Article 5.2: May be null if unclassified
    size: Optional[str] = None
    color: Optional[str] = None
    notes: Optional[str] = None
    crawl_timestamp: Optional[datetime] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate required fields."""
        if not self.name:
            raise ValueError("Fly name cannot be empty")
        if not self.raw_text:
            raise ValueError("Fly raw_text cannot be empty (Article 6 compliance)")
        if not self.river_id:
            raise ValueError("Fly must have a river_id")


@dataclass
class Regulation:
    """Represents a regulation or condition for a river."""

    type: str
    value: str
    raw_text: str
    river_id: int
    section_id: Optional[int] = None
    source_section: Optional[str] = None
    crawl_timestamp: Optional[datetime] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate required fields."""
        if not self.type:
            raise ValueError("Regulation type cannot be empty")
        if not self.value:
            raise ValueError("Regulation value cannot be empty")
        if not self.raw_text:
            raise ValueError("Regulation raw_text cannot be empty (Article 6 compliance)")
        if not self.river_id:
            raise ValueError("Regulation must have a river_id")


@dataclass
class Metadata:
    """Represents crawl metadata for change detection."""

    session_id: str
    entity_type: str
    crawl_timestamp: datetime
    entity_id: Optional[int] = None
    raw_content_hash: Optional[str] = None
    parsed_hash: Optional[str] = None
    page_version: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate required fields."""
        if not self.session_id:
            raise ValueError("Metadata session_id cannot be empty")
        if not self.entity_type:
            raise ValueError("Metadata entity_type cannot be empty")
        if not self.crawl_timestamp:
            raise ValueError("Metadata crawl_timestamp cannot be empty (Article 6.3)")
