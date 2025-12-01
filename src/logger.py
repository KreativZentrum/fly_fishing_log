"""
Logging module for NZ Flyfishing Web Scraper.
Article 9 Compliance: Complete request logging, JSON format, no sensitive data.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class ScraperLogger:
    """Structured JSON logger for scraper operations."""

    def __init__(self, log_path: str = "logs/scraper.log", console_level: str = "INFO"):
        """
        Initialize logger with file and console handlers.

        Args:
            log_path: Path to log file (JSON lines format)
            console_level: Console logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # Setup Python logger for console
        self.console_logger = logging.getLogger("nzfishing_scraper")
        self.console_logger.setLevel(getattr(logging, console_level.upper()))

        if not self.console_logger.handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(
                logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            )
            self.console_logger.addHandler(console_handler)

    def _write_json_log(self, event_data: dict):
        """Write structured JSON log entry to file."""
        event_data["timestamp"] = datetime.utcnow().isoformat() + "Z"

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event_data) + "\n")

    def log_request(
        self,
        url: str,
        method: str = "GET",
        status_code: Optional[int] = None,
        delay_seconds: float = 0.0,
        cache_hit: bool = False,
        error: Optional[str] = None,
    ):
        """
        Log HTTP request details (Article 9.3).

        Args:
            url: Full URL requested
            method: HTTP method (GET, POST, etc.)
            status_code: HTTP response status (200, 404, 500, etc.)
            delay_seconds: Time waited before making request (rate limiting)
            cache_hit: Whether request was served from cache
            error: Error message if request failed
        """
        event = {
            "event": "http_request",
            "url": url,
            "method": method,
            "status_code": status_code,
            "delay_seconds": round(delay_seconds, 2),
            "cache_hit": cache_hit,
            "error": error,
        }

        self._write_json_log(event)

        # Console log
        if error:
            self.console_logger.error(f"HTTP {method} {url} - {error}")
        elif cache_hit:
            self.console_logger.debug(f"HTTP {method} {url} - CACHE HIT")
        else:
            self.console_logger.info(
                f"HTTP {method} {url} - {status_code} (delay: {delay_seconds:.2f}s)"
            )

    def log_disallow(self, url: str, reason: str = "robots.txt disallow"):
        """
        Log robots.txt disallow event (Article 9.2).

        Args:
            url: URL that was blocked by robots.txt
            reason: Reason for disallow
        """
        event = {"event": "robots_txt_disallow", "url": url, "reason": reason}

        self._write_json_log(event)
        self.console_logger.warning(f"DISALLOWED: {url} - {reason}")

    def log_halt(self, reason: str):
        """
        Log scraper halt event (Article 9.2).

        Args:
            reason: Reason for halting (e.g., "3+ consecutive 5xx errors")
        """
        event = {"event": "halt", "reason": reason}

        self._write_json_log(event)
        self.console_logger.critical(f"HALT: {reason}")

    def log_discovery(self, entity_type: str, entity_name: str, action: str):
        """
        Log entity discovery (region, river, etc.).

        Args:
            entity_type: Type of entity (region, river, section)
            entity_name: Name of discovered entity
            action: Action taken (INSERT, UPDATE, SKIP)
        """
        event = {
            "event": "discovery",
            "entity_type": entity_type,
            "entity_name": entity_name,
            "action": action,
        }

        self._write_json_log(event)
        self.console_logger.info(f"{action}: {entity_type} '{entity_name}'")

    def log_extraction(
        self,
        river_name: str,
        flies_count: int,
        regulations_count: int,
        fields_with_data: int,
        fields_null: int,
    ):
        """
        Log river detail extraction results.

        Args:
            river_name: Name of river
            flies_count: Number of flies extracted
            regulations_count: Number of regulations extracted
            fields_with_data: Count of non-null parsed fields
            fields_null: Count of null fields (Article 5.2 compliance)
        """
        event = {
            "event": "extraction",
            "river_name": river_name,
            "flies_count": flies_count,
            "regulations_count": regulations_count,
            "fields_with_data": fields_with_data,
            "fields_null": fields_null,
        }

        self._write_json_log(event)
        self.console_logger.info(
            f"Extracted: {river_name} - {flies_count} flies, "
            f"{regulations_count} regulations, {fields_null} null fields"
        )

    def log_pdf_generated(
        self, river_name: str, river_id: int, filename: str, generation_time_ms: int
    ):
        """
        Log PDF generation success.

        Args:
            river_name: Name of river
            river_id: Database ID of river
            filename: Output PDF filename
            generation_time_ms: Time taken to generate PDF in milliseconds
        """
        event = {
            "event": "pdf_generated",
            "river_name": river_name,
            "river_id": river_id,
            "filename": filename,
            "generation_time_ms": generation_time_ms,
        }

        self._write_json_log(event)
        self.console_logger.info(f"PDF generated: {filename} ({generation_time_ms}ms)")

    def log_pdf_batch(self, region_id: int, river_count: int, total_time_ms: int):
        """
        Log batch PDF generation completion.

        Args:
            region_id: Database ID of region
            river_count: Number of PDFs generated
            total_time_ms: Total time in milliseconds
        """
        event = {
            "event": "pdf_batch",
            "region_id": region_id,
            "river_count": river_count,
            "total_time_ms": total_time_ms,
        }

        self._write_json_log(event)
        self.console_logger.info(f"Batch PDF complete: {river_count} PDFs in {total_time_ms}ms")

    def info(self, message: str):
        """Log info message."""
        self.console_logger.info(message)

    def warning(self, message: str):
        """Log warning message."""
        self.console_logger.warning(message)

    def error(self, message: str):
        """Log error message."""
        self.console_logger.error(message)

    def debug(self, message: str):
        """Log debug message."""
        self.console_logger.debug(message)
