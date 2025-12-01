# Contract: Parser Module

**Purpose**: Define the interface for HTML parsing and structured data extraction.  
**Compliance**: Articles 4–5 (page discovery rules, parsing without inference).

---

## Module: `src/parser.py`

### Responsibility

Parse HTML from nzfishing.com pages and extract structured data:
- Discover regions from the index page
- Discover rivers from region pages
- Extract details (fish type, conditions, flies, regulations) from river detail pages
- Store raw HTML alongside parsed data
- Never infer or fabricate data not explicitly on the page

### Interface

```python
class Parser:
    """HTML parser for nzfishing.com pages."""
    
    def __init__(self, config: dict, logger: Logger):
        """
        Initialize parser.
        
        Args:
            config: Configuration dict with keys:
                - index_url (str): URL of region index (e.g., "where-to-fish")
                - region_list_selector (str): CSS selector for regions in index
                - river_list_selector (str): CSS selector for rivers in region page
                - detail_selectors (dict): CSS selectors for detail page sections
            logger: Logger instance
        """
        pass
    
    # Discovery methods (Article 4)
    
    def parse_region_index(self, html: str) -> list[dict]:
        """
        Parse the "Where to Fish" index to discover regions.
        
        Args:
            html (str): HTML content of the index page
        
        Returns:
            list[dict]: List of region records, each with:
                {
                    'name': str,
                    'slug': str,
                    'canonical_url': str,
                    'source_url': str (URL of the index),
                    'raw_html': str (HTML snippet)
                }
        
        Side effects:
            - Logs successful and failed parsing attempts
            - Logs any malformed or missing regions
        
        Raises:
            ParseError: If HTML structure is unexpectedly different
        """
        pass
    
    def parse_region_page(self, html: str, region: dict) -> list[dict]:
        """
        Parse a region page to discover rivers in the "Fishing Waters" section.
        
        Args:
            html (str): HTML content of the region page
            region (dict): Parent region record (for FK reference)
        
        Returns:
            list[dict]: List of river records, each with:
                {
                    'region_id': int (FK),
                    'name': str,
                    'slug': str,
                    'canonical_url': str,
                    'source_url': str (URL of the region page),
                    'raw_html': str (HTML snippet from Fishing Waters section)
                }
        
        Side effects:
            - Logs discovered rivers
            - Logs missing or malformed "Fishing Waters" sections
        
        Raises:
            ParseError: If HTML structure is unexpectedly different
        """
        pass
    
    # Detail extraction methods (Article 5)
    
    def parse_river_detail(self, html: str, river: dict) -> dict:
        """
        Parse a river detail page to extract structured information.
        
        Args:
            html (str): HTML content of the river detail page
            river (dict): Parent river record (for FK reference)
        
        Returns:
            dict with keys:
                {
                    'river_id': int,
                    'raw_html': str (full raw content),
                    'description': str or None,
                    'sections': list[dict],  # If river has multiple reaches
                    'recommended_flies': list[dict],
                    'regulations': list[dict],
                    'metadata': dict  # Crawl info
                }
            
            Each recommended_fly dict:
                {
                    'name': str,
                    'raw_text': str,
                    'category': str or None,
                    'size': str or None,
                    'color': str or None,
                    'notes': str or None
                }
            
            Each regulation dict:
                {
                    'type': str,  # 'catch_limit', 'season_dates', 'method', etc.
                    'value': str,
                    'raw_text': str,
                    'source_section': str  # Which page section this came from
                }
        
        Side effects:
            - Logs parsed fields
            - Logs missing or unclassifiable fields (logs but does not infer)
        
        Raises:
            ParseError: If HTML structure is unexpectedly different
        
        Important (Article 5):
            - MUST NOT infer missing fields (leave as None)
            - MUST NOT fabricate values not explicitly on the page
            - MUST store raw HTML/text for every field
            - Category, size, color are OPTIONAL and may be None if unclear
        """
        pass
    
    # Utility methods
    
    def extract_text(self, html: str, selector: str) -> str or None:
        """
        Extract text content from an HTML element (utility).
        
        Args:
            html (str): HTML content
            selector (str): CSS selector
        
        Returns:
            str or None: Text content (stripped), or None if element not found
        """
        pass
    
    def classify_fly(self, name: str, raw_text: str) -> dict:
        """
        Attempt to classify a fly pattern (optional helper).
        
        Args:
            name (str): Fly name
            raw_text (str): Full raw text
        
        Returns:
            dict: {'category': str or None, 'size': str or None, 'color': str or None}
        
        Important (Article 5):
            - MUST NOT guess; only classify if pattern is clear
            - Return None for uncertain fields
        """
        pass
```

### Expected Behavior

**Discovery (Article 4)**:
- Parse region index via CSS selector; extract name, URL, description.
- Parse region page to find "Fishing Waters" section; extract river names, URLs.
- Gracefully handle missing or reformatted sections; log warnings; continue processing.
- No hardcoded river or region lists (except hotfixes).

**Detail Extraction (Article 5)**:
- Parse predictable sections: "Fish type", "Situation", "Recommended lures", "Catch regulations", "Season dates", "Flow status".
- Extract and store both raw HTML/text AND parsed fields.
- For optional fields (category, size, color): Leave as None if classification uncertain.
- Never infer or fill in missing values.

**Error Handling**:
- ParseError on structural mismatch (e.g., no "Where to Fish" section).
- Log warnings for partial extraction (e.g., missing field) but continue.
- Log all extraction attempts and results for auditability.

### Data Contracts

**Input**:
- `html`: String (from Fetcher)
- `config`: Dict with CSS selectors
- `region`/`river`: Parent records for FK reference

**Output**:
- Structured dict with parsed fields and raw content

**Invariants**:
- `raw_html` or `raw_text` is always populated
- Parsed fields may be None but never fabricated
- Source URLs and timestamps are preserved

### Testing Strategy

- Unit tests: Mock HTML with `BeautifulSoup` fixtures; test parsing logic.
- Test missing/malformed sections; verify graceful handling.
- Test that no inference occurs (e.g., missing field = None, not guessed).
- Test classification logic (classify_fly) with various patterns.
- Integration test: Use sample pages from nzfishing.com; verify full extraction.

---

## Exception Hierarchy

```python
class ParseError(Exception):
    """Parsing error (e.g., unexpected HTML structure)."""
    pass
```

---

## Configuration Example

```yaml
parser:
  selectors:
    region_index: "div.region-list a"  # CSS selector for regions
    region_name: "h2.region-name"
    river_list: "section#fishing-waters ul li"  # CSS selector for rivers in Fishing Waters
    river_name: "a.river-link"
    detail_sections:
      fish_type: "div.fish-type p"
      situation: "div.situation p"
      recommended_lures: "div.recommended-lures ul"
      catch_regulations: "div.catch-limit"
      season_dates: "div.season-dates"
      flow_status: "div.flow-status"
```

---

## Sample Parsing Output

```python
{
    'river_id': 123,
    'raw_html': '<div class="river-detail">...',
    'description': 'A scenic river in the North Island...',
    'sections': [
        {
            'name': 'Upper Waikato',
            'raw_html': '<div class="upper">...',
            'crawl_timestamp': '2025-11-30T12:00:00Z'
        }
    ],
    'recommended_flies': [
        {
            'name': 'Pheasant Tail Nymph',
            'raw_text': 'Pheasant Tail Nymph (size 12-16) - excellent in summer',
            'category': 'nymph',
            'size': '12-16',
            'color': 'brown',
            'notes': 'Excellent in summer'
        },
        {
            'name': 'Woolly Bugger',
            'raw_text': 'Woolly Bugger - black or olive',
            'category': 'streamer',
            'size': None,  # Not specified; not inferred
            'color': None,  # Could be 'black' or 'olive', ambiguous; left as None
            'notes': 'Black or olive'
        }
    ],
    'regulations': [
        {
            'type': 'catch_limit',
            'value': '12 fish per day',
            'raw_text': 'Catch limit: 12 fish per day',
            'source_section': 'Catch regulations'
        },
        {
            'type': 'season_dates',
            'value': 'November–April',
            'raw_text': 'Open season: November–April',
            'source_section': 'Season dates'
        }
    ],
    'metadata': {
        'crawl_timestamp': '2025-11-30T12:00:00Z',
        'raw_content_hash': 'abc123...'
    }
}
```

---

## Compliance Notes

- **Article 4 (Page Discovery Rules)**: Regions discovered from index; rivers discovered from region pages; no hardcoding.
- **Article 5 (Parsing & Data Interpretation)**: Extracts only explicit content; no inference; raw data stored alongside parsed fields.
