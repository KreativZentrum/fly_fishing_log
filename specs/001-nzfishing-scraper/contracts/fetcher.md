# Contract: Fetcher Module

**Purpose**: Define the interface and behavior of the HTTP fetcher component.  
**Compliance**: Articles 2–3, 9 (robots.txt, rate limiting, logging, error handling).

---

## Module: `src/fetcher.py`

### Responsibility

Fetch HTTP resources from nzfishing.com with:
- Respect for robots.txt
- 3-second minimum delay between requests
- Caching of HTML responses
- Exponential backoff on transient errors
- Comprehensive logging of all requests

### Interface

```python
class Fetcher:
    """HTTP fetcher with polite crawling, caching, and logging."""
    
    def __init__(self, config: dict, logger: Logger):
        """
        Initialize fetcher.
        
        Args:
            config: Configuration dict with keys:
                - base_url (str): e.g., 'https://nzfishing.com'
                - user_agent (str): Identifiable User-Agent string
                - request_delay (float): Seconds to delay between requests (default 3.0)
                - cache_dir (str): Path to cache directory
                - cache_ttl (int): Cache TTL in seconds (default 86400 = 24 hours)
                - max_retries (int): Max retry attempts for transient errors (default 3)
            logger: Logger instance for structured logging
        """
        pass
    
    def fetch(self, url: str, use_cache: bool = True, refresh: bool = False) -> str:
        """
        Fetch a URL with caching, rate limiting, and error handling.
        
        Args:
            url (str): Full URL to fetch
            use_cache (bool): Whether to use cached response if available (default True)
            refresh (bool): Force re-fetch, bypassing cache (default False)
        
        Returns:
            str: HTML content of the page
        
        Raises:
            FetchError: If fetch fails after max retries or on critical error (403, 404 to be handled gracefully)
            HaltError: If 3+ consecutive 5xx errors detected (halt the scraper)
        
        Side effects:
            - Logs request with timestamp, URL, status code, cache hit/miss, delay duration
            - Stores response in cache (if use_cache=True and not already cached)
            - Enforces request_delay (logs actual delay)
            - Updates consecutive error counter
        """
        pass
    
    def get_robots_txt(self) -> str:
        """
        Fetch robots.txt from the site.
        
        Returns:
            str: Content of robots.txt
        
        Raises:
            FetchError: If fetch fails
        
        Side effects:
            - Logs robots.txt fetch
            - Caches result
        """
        pass
    
    def is_allowed(self, url: str) -> bool:
        """
        Check if a URL is allowed by robots.txt.
        
        Args:
            url (str): URL to check
        
        Returns:
            bool: True if allowed, False if disallowed
        
        Side effects:
            - Logs disallow violations
        """
        pass
    
    def clear_cache(self) -> None:
        """Clear all cached HTML files."""
        pass
    
    def get_cache_stats(self) -> dict:
        """
        Return cache statistics.
        
        Returns:
            dict: {'total_cached': int, 'total_size_mb': float, 'oldest_entry': datetime, ...}
        """
        pass
    
    def close(self) -> None:
        """Cleanup (close connections, flush logs)."""
        pass
```

### Expected Behavior

**Rate Limiting**:
- Before each request, sleep for `request_delay` seconds (minimum 3.0).
- Log actual delay (in case of system overhead).
- No concurrent/parallel requests; strictly single-threaded.

**Caching**:
- Cache key: SHA256 hash of URL.
- Store in `cache_dir` with filename like `<hash>.html`.
- Include metadata file (JSON) with `fetch_time`, `content_hash`, `url`.
- Check TTL before using cached entry; re-fetch if expired.
- Support `--refresh` flag to bypass cache on demand.

**Error Handling**:
- Transient errors (connection timeout, 5xx): Retry with exponential backoff (1s, 2s, 4s).
- Permanent errors (403, 404): Log warning; continue to next resource.
- 3+ consecutive 5xx errors on same domain: Raise `HaltError` to stop the scraper.

**Logging**:
- Every request: URL, timestamp (ISO 8601 UTC), HTTP status, cache hit/miss, delay duration.
- Format: JSON lines or structured logging.
- Include User-Agent in all requests (Article 2.4).

### Data Contracts

**Input**:
- `url`: Valid HTTP(S) URL
- `config`: Dict with required keys (see `__init__` Args)

**Output**:
- String (HTML content)
- Exception on failure (FetchError, HaltError)

**Side Effects**:
- Logs to `logs/scraper.log` and console
- Writes to cache directory
- Updates request counter (for error halting logic)

### Testing Strategy

- Mock `requests.get()` to return sample HTML.
- Test cache hit/miss logic with fixtures.
- Test exponential backoff by mocking `time.sleep()`.
- Test 3+ consecutive 5xx halt condition.
- Integration test: Run against mock HTTP server with controlled responses.

---

## Exception Hierarchy

```python
class FetchError(Exception):
    """Generic fetch error (non-halting)."""
    pass

class HaltError(FetchError):
    """Fatal error; halt the scraper."""
    pass
```

---

## Configuration Example

```yaml
fetcher:
  base_url: "https://nzfishing.com"
  user_agent: "NZFlyfishingBot/1.0 (+https://github.com/KreativZentrum/fly_fishing_log)"
  request_delay: 3.0
  request_jitter: 1.0  # Optional random delay 0–1 sec
  cache_dir: ".cache/nzfishing"
  cache_ttl: 86400  # 24 hours
  max_retries: 3
  retry_backoff_base: 1.0  # Exponential base
```

---

## Compliance Notes

- **Article 2 (Scraping Compliance)**: Respects robots.txt; sets clear User-Agent; implements 3-sec delay.
- **Article 3 (Fetching & Request Principles)**: Polite crawling with fixed delay; retry logic; caching; no parallel requests.
- **Article 9 (Safety & Operational Discipline)**: Comprehensive logging; error halt conditions; inspection-friendly logs.
