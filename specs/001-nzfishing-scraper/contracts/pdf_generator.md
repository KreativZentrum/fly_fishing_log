# Contract: PDF Generator Module

**Purpose**: Define the interface for template-driven PDF generation.  
**Compliance**: Article 7 (PDF generation from database records, no live-scrape).

---

## Module: `src/pdf_generator.py`

### Responsibility

Generate PDF documents from database records using Jinja2 templates and reportlab. No live-scraping; all content sourced from the database.

### Interface

```python
class PDFGenerator:
    """Template-driven PDF generator."""
    
    def __init__(self, config: dict, storage: Storage, logger: Logger):
        """
        Initialize PDF generator.
        
        Args:
            config (dict): Configuration with keys:
                - template_dir (str): Path to Jinja2 templates
                - output_dir (str): Path to write generated PDFs
            storage: Storage instance (read from DB)
            logger: Logger instance
        """
        pass
    
    def generate_river_pdf(self, river_id: int, filename: str or None = None) -> str:
        """
        Generate a PDF for a river from database records.
        
        Args:
            river_id (int): River ID
            filename (str, optional): Output filename; if None, auto-generate from river name
        
        Returns:
            str: Path to generated PDF file
        
        Side effects:
            - Queries storage for river, sections, flies, regulations
            - Renders Jinja2 template with data
            - Generates PDF using reportlab
            - Saves to output_dir
            - Logs operation
        
        Raises:
            PDFError: If river not found or PDF generation fails
        
        Important (Article 7):
            - MUST NOT fetch live page
            - MUST NOT use internet during generation
            - MUST use only data from database
        """
        pass
    
    def generate_batch_pdfs(self, region_id: int or None = None, output_zip: str or None = None) -> list[str]:
        """
        Generate PDFs for all rivers (optionally filtered by region).
        
        Args:
            region_id (int, optional): Filter to single region
            output_zip (str, optional): If provided, zip all PDFs into this file
        
        Returns:
            list[str]: Paths to generated PDF files
        
        Side effects:
            - Queries all rivers (and optionally filters by region)
            - Generates PDF for each
            - Logs progress
        """
        pass
    
    def render_template(self, river_id: int) -> str:
        """
        Render HTML from Jinja2 template (for debugging).
        
        Args:
            river_id (int): River ID
        
        Returns:
            str: Rendered HTML (before PDF conversion)
        """
        pass
    
    def close(self) -> None:
        """Cleanup."""
        pass
```

### Expected Behavior

**Database-Only Content**:
- Query storage for river, sections, flies, regulations, metadata.
- Pass to Jinja2 template.
- No HTTP requests during generation.
- If a river or field is not in the database, render "Not available" or omit section.

**Template Rendering**:
- Use Jinja2 with filters for formatting (dates, lists, etc.).
- Support conditional sections (show regulation section only if regulations exist).
- Auto-escape HTML to prevent injection issues.

**PDF Generation**:
- Use reportlab for simple, lightweight output.
- Support landscape and portrait modes.
- Generate in <5 seconds per river on standard hardware.
- Handle missing fields gracefully (omit section or show placeholder).

**Output**:
- PDF saved to `output_dir` with filename `{river_slug}.pdf` or user-specified name.
- Log path for user reference.

### Data Contracts

**Input**:
- `river_id`: Valid river ID from database
- `config`: Dict with template_dir and output_dir

**Output**:
- PDF file path (string)

**Database Queries**:
- River info (name, description, canonical_url)
- Sections associated with river
- Recommended flies for river
- Regulations for river

### Testing Strategy

- Unit tests: Mock storage queries; verify template rendering.
- Integration tests: Create sample river in test DB; generate PDF; verify content.
- Test missing fields (omit section or render "N/A").
- Test batch generation with multiple rivers.

---

## Exception Hierarchy

```python
class PDFError(Exception):
    """PDF generation error."""
    pass
```

---

## Template Example (Jinja2)

```jinja2
<!DOCTYPE html>
<html>
<head>
    <title>{{ river.name }} - Flyfishing Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        section { margin-top: 20px; page-break-inside: avoid; }
        .regulation { margin: 5px 0; }
    </style>
</head>
<body>
    <h1>{{ river.name }}</h1>
    <p><strong>Region:</strong> {{ region.name }}</p>
    <p><strong>URL:</strong> <a href="{{ river.canonical_url }}">{{ river.canonical_url }}</a></p>
    
    {% if river.description %}
    <section>
        <h2>Description</h2>
        <p>{{ river.description }}</p>
    </section>
    {% endif %}
    
    {% if sections %}
    <section>
        <h2>Sections/Reaches</h2>
        <ul>
        {% for section in sections %}
            <li>{{ section.name }}</li>
        {% endfor %}
        </ul>
    </section>
    {% endif %}
    
    {% if flies %}
    <section>
        <h2>Recommended Flies</h2>
        <ul>
        {% for fly in flies %}
            <li>
                <strong>{{ fly.name }}</strong>
                {% if fly.category %} ({{ fly.category }}){% endif %}
                {% if fly.size %} - Size {{ fly.size }}{% endif %}
                {% if fly.notes %} - {{ fly.notes }}{% endif %}
            </li>
        {% endfor %}
        </ul>
    </section>
    {% endif %}
    
    {% if regulations %}
    <section>
        <h2>Regulations & Conditions</h2>
        <ul>
        {% for reg in regulations %}
            <li>
                <strong>{{ reg.type|replace('_', ' ')|title }}:</strong> {{ reg.value }}
            </li>
        {% endfor %}
        </ul>
    </section>
    {% endif %}
    
    <hr>
    <p style="font-size: 0.85em; color: #666;">
        Generated on {{ now|strftime('%Y-%m-%d %H:%M:%S') }} UTC
    </p>
</body>
</html>
```

---

## Configuration Example

```yaml
pdf_generator:
  template_dir: "templates/"
  output_dir: ".output/"
  page_size: "A4"  # or "Letter"
  orientation: "portrait"  # or "landscape"
```

---

## Compliance Notes

- **Article 7 (PDF Generation Principles)**: Template-driven; database-only; no live-scrape.
