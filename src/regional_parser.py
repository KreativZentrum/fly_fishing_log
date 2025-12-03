"""
Regional page parser extension for NZ Flyfishing Web Scraper.

This module adds support for parsing regional 'where-to-fish' pages like:
https://nzfishing.com/auckland-waikato/where-to-fish/

These pages have a different structure than the main regions index, with
rivers mentioned inline within paragraph text.
"""

from typing import Dict, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .exceptions import ParserError


class RegionalParser:
    """Parser for regional where-to-fish pages."""

    def __init__(self, config):
        """
        Initialize parser with configuration.
        
        Args:
            config: Configuration instance
        """
        self.config = config

    def parse_regional_page(
        self, html: str, page_url: str, region_name: str
    ) -> List[Dict]:
        """
        Parse a regional 'where-to-fish' page to extract river links.
        
        Regional pages like /auckland-waikato/where-to-fish/ contain
        inline links to rivers within paragraph text, such as:
        "the <a href='/region/river-name'>River Name</a> river"
        
        Args:
            html: Raw HTML content
            page_url: URL of the page being parsed (for resolving relative links)
            region_name: Name of the region (e.g., "Auckland-Waikato")
            
        Returns:
            List of river dicts with keys: name, canonical_url, region, slug
            
        Raises:
            ParserError: If parsing fails
        """
        try:
            soup = BeautifulSoup(html, "lxml")
            rivers = []
            seen_urls = set()

            # Find main content area
            content = self._find_content_area(soup)

            # Extract all links from content
            links = content.find_all("a", href=True)

            for link in links:
                href = link.get("href", "").strip()
                text = link.get_text().strip()

                # Skip invalid links
                if not href or href in ["#", ""]:
                    continue

                # Convert relative URLs to absolute
                canonical_url = urljoin(page_url, href)

                # Filter to only river/water body links
                if not self._is_river_link(canonical_url, region_name):
                    continue

                # Skip duplicates
                if canonical_url in seen_urls:
                    continue
                seen_urls.add(canonical_url)

                # Extract river name
                name = self._extract_river_name(link, canonical_url)

                # Extract slug from URL
                slug = canonical_url.rstrip("/").split("/")[-1]

                rivers.append(
                    {
                        "name": name,
                        "canonical_url": canonical_url,
                        "region": region_name,
                        "slug": slug,
                    }
                )

            return rivers

        except Exception as e:
            raise ParserError(f"Failed to parse regional page: {e}") from e

    def _find_content_area(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        Find the main content area of the page.
        
        Tries multiple selectors in order of preference.
        Falls back to entire document if none found.
        """
        content_selectors = [
            lambda: soup.find("div", class_=lambda c: c and "builder" in c.lower()),
            lambda: soup.find("div", class_=lambda c: c and "content" in c.lower()),
            lambda: soup.find("article"),
            lambda: soup.find("main"),
        ]

        for selector in content_selectors:
            content = selector()
            if content:
                return content

        return soup  # Fall back to entire document

    def _is_river_link(self, url: str, region_name: str) -> bool:
        """
        Check if a URL appears to be a river/water body page.
        
        Args:
            url: Canonical URL to check
            region_name: Region name to match against
            
        Returns:
            True if URL looks like a river page
        """
        # Normalize region name for URL matching
        region_slug = region_name.lower().replace(" – ", "-").replace(" ", "-")

        # Must contain region name
        if region_slug not in url.lower():
            return False

        # Skip navigation pages
        if "/where-to-fish/" in url:
            return False

        return True

    def _extract_river_name(self, link_element, url: str) -> str:
        """
        Extract the river name from link text or URL.
        
        Args:
            link_element: BeautifulSoup link element
            url: Canonical URL of the river page
            
        Returns:
            Cleaned river name
        """
        # Start with link text
        name = link_element.get_text().strip()

        # If name is too short or generic, extract from URL
        if len(name) < 3 or name.lower() in ["river", "stream", "creek", "lake"]:
            # Extract from URL: /auckland-waikato/waipa-river -> Waipa River
            url_parts = url.rstrip("/").split("/")
            if url_parts:
                slug = url_parts[-1]
                # Handle .htm files
                if slug.endswith(".htm"):
                    slug = slug[:-4]
                name = slug.replace("-", " ").title()

        # Add type suffix if not present (River, Stream, Creek, Lake)
        if not any(
            t in name.lower() for t in ["river", "stream", "creek", "lake", "reservoir"]
        ):
            # Check surrounding context for type
            parent_text = link_element.parent.get_text() if link_element.parent else ""
            parent_lower = parent_text.lower()

            if "river" in parent_lower:
                name = name + " River"
            elif "stream" in parent_lower:
                name = name + " Stream"
            elif "creek" in parent_lower:
                name = name + " Creek"
            elif "lake" in parent_lower:
                name = name + " Lake"
            else:
                # Default to River for water bodies
                name = name + " River"

        return name
