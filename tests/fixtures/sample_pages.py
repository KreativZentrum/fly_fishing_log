"""
Static HTML sample pages for offline unit tests.
Article 5 Compliance: Minimal, complete, unambiguous test data.
"""

# Minimal valid index page
MINIMAL_INDEX = """
<!DOCTYPE html>
<html>
<body>
    <div class="region-list">
        <a href="/region/test">Test Region</a>
    </div>
</body>
</html>
"""

# Minimal valid region page
MINIMAL_REGION = """
<!DOCTYPE html>
<html>
<body>
    <div class="fishing-waters">
        <a href="/river/test-river">Test River</a>
    </div>
</body>
</html>
"""

# Minimal valid river detail page
MINIMAL_RIVER = """
<!DOCTYPE html>
<html>
<body>
    <h1 class="river-name">Test River</h1>
    <div class="description">A test river.</div>
</body>
</html>
"""

# Complete river detail with all fields
COMPLETE_RIVER = """
<!DOCTYPE html>
<html>
<head><title>Complete River Example</title></head>
<body>
    <h1 class="river-name">Complete River</h1>
    <div class="description">
        <p>This is a complete river detail page for testing.</p>
    </div>
    
    <h2>Sections</h2>
    <div class="sections">
        <div class="section" data-slug="upper">
            <h3>Upper Section</h3>
        </div>
        <div class="section" data-slug="lower">
            <h3>Lower Section</h3>
        </div>
    </div>
    
    <h2>Recommended Flies</h2>
    <div class="flies">
        <ul>
            <li>Nymph - Hare's Ear size 12</li>
            <li>Dry - Royal Wulff size 14</li>
        </ul>
    </div>
    
    <h2>Regulations</h2>
    <div class="regulations">
        <p><strong>Bag Limit:</strong> 2 fish</p>
        <p><strong>Season:</strong> Year-round</p>
    </div>
</body>
</html>
"""

# Ambiguous river detail (missing fields)
AMBIGUOUS_RIVER = """
<!DOCTYPE html>
<html>
<body>
    <h1 class="river-name">Ambiguous River</h1>
    <!-- Missing description -->
    <!-- Missing sections -->
    <!-- Missing flies -->
    <!-- Missing regulations -->
</body>
</html>
"""

# Malformed HTML (for error handling tests)
MALFORMED_HTML = """
<!DOCTYPE html>
<html>
<body>
    <h1 class="river-name">Malformed River
    <!-- Unclosed tags -->
    <div class="description">
        <p>Missing closing tags
</body>
"""

# Empty HTML (edge case)
EMPTY_HTML = """
<!DOCTYPE html>
<html>
<body>
</body>
</html>
"""

# HTML with special characters (Article 5.3 - no encoding assumptions)
SPECIAL_CHARS_HTML = """
<!DOCTYPE html>
<html>
<body>
    <h1 class="river-name">River with Māori name</h1>
    <div class="description">
        <p>Contains special characters: āēīōū</p>
        <p>And symbols: &lt;tag&gt; &amp; &quot;quotes&quot;</p>
    </div>
    <div class="flies">
        <ul>
            <li>Fly #1 - Size 12–14 (en dash)</li>
            <li>Fly "Royal" (smart quotes)</li>
        </ul>
    </div>
</body>
</html>
"""

# Nested structure (complex parsing test)
NESTED_HTML = """
<!DOCTYPE html>
<html>
<body>
    <div class="content">
        <div class="main">
            <h1 class="river-name">Nested River</h1>
            <div class="description">
                <div class="inner">
                    <p>Nested description text</p>
                </div>
            </div>
        </div>
    </div>
    <div class="sidebar">
        <div class="flies">
            <div class="fly-section">
                <ul>
                    <li><span>Fly 1</span></li>
                    <li><span>Fly 2</span></li>
                </ul>
            </div>
        </div>
    </div>
</body>
</html>
"""

# Multiple regions (batch discovery test)
MULTIPLE_REGIONS = """
<!DOCTYPE html>
<html>
<body>
    <div class="region-list">
        <a href="/region/north-island">North Island</a>
        <a href="/region/south-island">South Island</a>
        <a href="/region/stewart-island">Stewart Island</a>
    </div>
</body>
</html>
"""

# Multiple rivers (batch discovery test)
MULTIPLE_RIVERS = """
<!DOCTYPE html>
<html>
<body>
    <div class="river-list">
        <a href="/river/tongariro">Tongariro</a>
        <a href="/river/rangitikei">Rangitikei</a>
        <a href="/river/manawatu">Manawatu</a>
        <a href="/river/whanganui">Whanganui</a>
    </div>
</body>
</html>
"""

# Duplicate links (de-duplication test)
DUPLICATE_LINKS = """
<!DOCTYPE html>
<html>
<body>
    <div class="region-list">
        <a href="/region/test">Test Region</a>
        <a href="/region/test">Test Region (duplicate)</a>
        <a href="/region/other">Other Region</a>
    </div>
</body>
</html>
"""

# Invalid URLs (validation test)
INVALID_URLS = """
<!DOCTYPE html>
<html>
<body>
    <div class="region-list">
        <a href="not-a-url">Invalid</a>
        <a href="">Empty</a>
        <a href="/region/valid">Valid</a>
    </div>
</body>
</html>
"""

# No matching selectors (empty result test)
NO_MATCHES = """
<!DOCTYPE html>
<html>
<body>
    <div class="other-content">
        <p>This page has no region-list or river-list divs</p>
    </div>
</body>
</html>
"""

# Sample region page with multiple rivers (US2 testing)
SAMPLE_REGION_HTML = """
<!DOCTYPE html>
<html>
<head><title>Test Region - Fishing Waters</title></head>
<body>
    <h1>Test Region</h1>
    <div class="fishing-waters">
        <h2>Fishing Waters</h2>
        <ul>
            <li><a href="/river/tongariro">Tongariro River</a></li>
            <li><a href="/river/rangitikei">Rangitikei River</a></li>
        </ul>
    </div>
</body>
</html>
"""

# Multiple rivers page (US2 testing)
MULTIPLE_RIVERS = """
<!DOCTYPE html>
<html>
<body>
    <div class="fishing-waters">
        <a href="/river/tongariro">Tongariro River</a>
        <a href="/river/rangitikei">Rangitikei River</a>
        <a href="/river/manawatu">Manawatu River</a>
        <a href="/river/whanganui">Whanganui River</a>
    </div>
</body>
</html>
"""

# Duplicate river links (deduplication test)
DUPLICATE_LINKS = """
<!DOCTYPE html>
<html>
<body>
    <div class="fishing-waters">
        <a href="/river/test">Test River</a>
        <a href="/river/test">Test River</a>
        <a href="/river/other">Other River</a>
    </div>
</body>
</html>
"""

# Nested HTML structure (robustness test)
NESTED_HTML = """
<!DOCTYPE html>
<html>
<body>
    <div class="content">
        <div class="fishing-waters">
            <div class="section">
                <h3>Main Rivers</h3>
                <div class="list">
                    <a href="/river/nested">Nested River</a>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

# Empty HTML (edge case)
EMPTY_HTML = """
<!DOCTYPE html>
<html>
<body>
</body>
</html>
"""
