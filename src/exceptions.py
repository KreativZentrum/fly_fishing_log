"""
Custom exceptions for NZ Flyfishing Web Scraper.
Article 9 Compliance: Clear error handling and halt conditions.
"""


class FetchError(Exception):
    """HTTP fetch operation failed."""

    def __init__(self, message: str, url: str, status_code: int = None, retry_after: int = None):
        super().__init__(message)
        self.url = url
        self.status_code = status_code
        self.retry_after = retry_after


class HaltError(Exception):
    """Fatal error requiring scraper halt (Article 3.3, 9.2)."""

    def __init__(self, message: str, reason: str):
        super().__init__(message)
        self.reason = reason


class ConfigError(Exception):
    """Configuration validation failed."""

    pass


class StorageError(Exception):
    """Database operation failed."""

    pass


class ParserError(Exception):
    """HTML parsing failed."""

    pass


class PDFError(Exception):
    """PDF generation failed."""

    pass
