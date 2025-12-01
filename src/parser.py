"""
HTML parser module for NZ Flyfishing Web Scraper.
Article 5 Compliance: No inference, raw + structured separation.
"""

from typing import Dict, List, Optional

from bs4 import BeautifulSoup

from .exceptions import ParserError


class Parser:
    """HTML parser for nzfishing.com pages."""

    def __init__(self, config):
        """
        Initialize parser with configuration.

        Args:
            config: Configuration instance with discovery_rules
        """
        self.config = config
        self.discovery_rules = config.discovery_rules

    def parse_region_index(self, html: str) -> List[Dict]:
        """
        Parse region index page to discover regions (Article 4.1).

        Article 5.1: Extract only explicitly stated content (no inference).
        Article 5.3: Accommodate predictable HTML structure.

        Args:
            html: HTML content from "Where to Fish" index page

        Returns:
            List of region dicts with keys: name, canonical_url, slug, description
        """
        soup = BeautifulSoup(html, "lxml")
        regions = []
        seen_urls = set()  # De-duplicate by canonical URL

        # Get selector from config
        selector = self.discovery_rules.get("region_selector", "div.region-list a")

        # Find all region links
        links = soup.select(selector)

        for link in links:
            # Extract canonical URL
            canonical_url = link.get("href", "").strip()

            # Skip invalid URLs (Article 4.4: graceful handling)
            if not canonical_url or canonical_url in ["", "#"]:
                continue

            # Skip duplicates
            if canonical_url in seen_urls:
                continue
            seen_urls.add(canonical_url)

            # Extract name (link text)
            name = link.get_text().strip()
            if not name:
                continue

            # Generate slug from URL or data attribute
            slug = link.get("data-slug")
            if not slug:
                # Extract slug from URL (e.g., /region/north-island -> north-island)
                slug = canonical_url.rstrip("/").split("/")[-1]

            # Extract description (if available in adjacent element)
            # Article 5.2: Only if explicitly present, no inference
            description = ""
            desc_elem = link.find_next_sibling("p") or link.find_next_sibling("div")
            if desc_elem:
                description = desc_elem.get_text().strip()

            regions.append(
                {
                    "name": name,
                    "canonical_url": canonical_url,
                    "slug": slug,
                    "description": description,
                }
            )

        return regions

    def parse_region_page(self, html: str, region: Dict) -> List[Dict]:
        """
        Parse region page to discover rivers (Article 4.2).

        Extract river links from the "Fishing Waters" section of a region page.
        Article 5.1: Extract only explicitly stated content (no inference).
        Article 5.3: Accommodate predictable HTML structure.

        Args:
            html: HTML content from region page
            region: Region dict with at least 'id' and 'name'

        Returns:
            List of river dicts with keys: name, canonical_url, slug
        """
        soup = BeautifulSoup(html, "lxml")
        rivers = []
        seen_urls = set()  # De-duplicate by canonical URL

        # Get selector from config
        selector = self.discovery_rules.get("river_selector", "div.fishing-waters a")

        # Find all river links
        links = soup.select(selector)

        for link in links:
            # Extract canonical URL
            canonical_url = link.get("href", "").strip()

            # Skip invalid URLs (Article 4.4: graceful handling)
            if not canonical_url or canonical_url in ["", "#"]:
                continue

            # Skip duplicates
            if canonical_url in seen_urls:
                continue
            seen_urls.add(canonical_url)

            # Extract name (link text)
            name = link.get_text().strip()
            if not name:
                continue

            # Generate slug from URL or data attribute
            slug = link.get("data-slug")
            if not slug:
                # Extract slug from URL (e.g., /river/tongariro -> tongariro)
                slug = canonical_url.rstrip("/").split("/")[-1]

            # Ensure slug is lowercase and hyphenated
            slug = slug.lower().replace("_", "-")

            rivers.append({"name": name, "canonical_url": canonical_url, "slug": slug})

        return rivers

    def parse_river_detail(self, html: str, river: Dict) -> Dict:
        """
        Parse river detail page to extract structured data (Article 5).

        Extracts fish type, conditions, flies, and regulations from river detail page.
        Article 5.1: Extract only explicitly stated content (no inference).
        Article 5.3: Accommodate predictable HTML structure.

        Args:
            html: HTML content from river detail page
            river: River dict with at least 'id' and 'name'

        Returns:
            Dict with keys: fish_type, conditions, flies (list), regulations (list)
        """
        soup = BeautifulSoup(html, "lxml")

        # Get selectors from config
        detail_selectors = self.discovery_rules.get("detail_selectors", {})
        fish_type_selector = detail_selectors.get("fish_type", ".fish-type")
        situation_selector = detail_selectors.get("situation", ".situation")
        flies_selector = detail_selectors.get("recommended_lures", ".recommended-lures")
        regulations_selector = detail_selectors.get("regulations", ".regulations")

        # Extract fish type
        fish_type = {}
        fish_type_elem = soup.select_one(fish_type_selector)
        if fish_type_elem:
            fish_type["raw_text"] = fish_type_elem.get_text(strip=True)

        # Extract conditions (situation)
        conditions = {}
        situation_elem = soup.select_one(situation_selector)
        if situation_elem:
            raw_text = situation_elem.get_text(strip=True)
            conditions["raw_text"] = raw_text

            # Optionally normalize flow level if explicitly mentioned
            raw_lower = raw_text.lower()
            if "low flow" in raw_lower:
                conditions["flow_level"] = "low"
            elif "medium flow" in raw_lower:
                conditions["flow_level"] = "medium"
            elif "high flow" in raw_lower:
                conditions["flow_level"] = "high"

        # Extract flies
        flies = []
        flies_elem = soup.select_one(flies_selector)
        if flies_elem:
            # Find all list items or direct children
            fly_items = flies_elem.select("li")
            if not fly_items:
                # Try getting all text if no list structure
                fly_items = [flies_elem]

            for item in fly_items:
                fly_text = item.get_text(strip=True)
                if not fly_text:
                    continue

                # Classify fly (returns None for uncertain fields)
                classification = self.classify_fly(fly_text, fly_text)

                flies.append(
                    {
                        "name": fly_text,
                        "raw_text": fly_text,
                        "category": classification.get("category"),
                        "size": classification.get("size"),
                        "color": classification.get("color"),
                    }
                )

        # Extract regulations
        regulations = []
        regs_elem = soup.select_one(regulations_selector)
        if regs_elem:
            # Find all paragraphs or list items
            reg_items = regs_elem.select("p, li")
            if not reg_items:
                # Try getting all text lines
                text = regs_elem.get_text()
                reg_items = [line for line in text.split("\n") if line.strip()]
                # Create mock elements for processing
                reg_items = [
                    type(
                        "obj", (), {"get_text": lambda self=l: l, "strip": lambda self=l: l.strip()}
                    )()
                    for l in reg_items
                    if l.strip()
                ]

            for item in reg_items:
                reg_text = (
                    item.get_text(strip=True) if hasattr(item, "get_text") else str(item).strip()
                )
                if not reg_text:
                    continue

                # Classify regulation type
                reg_lower = reg_text.lower()
                reg_type = "unclassified"
                value = reg_text

                if "catch limit" in reg_lower or "bag limit" in reg_lower:
                    reg_type = "catch_limit"
                    # Extract number if present
                    import re

                    match = re.search(r"(\d+)\s*(fish|trout)", reg_lower)
                    if match:
                        value = match.group(1) + " fish"
                elif "season" in reg_lower:
                    reg_type = "season_dates"
                elif "method" in reg_lower or "fly only" in reg_lower or "artificial" in reg_lower:
                    reg_type = "method"
                elif "permit" in reg_lower or "license" in reg_lower:
                    reg_type = "permit_required"
                elif "flow" in reg_lower and "status" in reg_lower:
                    reg_type = "flow_status"

                regulations.append({"type": reg_type, "value": value, "raw_text": reg_text})

        return {
            "fish_type": fish_type,
            "conditions": conditions,
            "flies": flies,
            "regulations": regulations,
        }

    def extract_text(self, html: str, selector: str) -> Optional[str]:
        """
        Extract text content from HTML using CSS selector.

        Args:
            html: HTML content
            selector: CSS selector string

        Returns:
            Extracted text or None if not found
        """
        try:
            soup = BeautifulSoup(html, "lxml")
            element = soup.select_one(selector)

            if element:
                return element.get_text(strip=True)

            return None
        except Exception as e:
            raise ParserError(f"Failed to extract text with selector '{selector}': {e}")

    def classify_fly(self, name: str, raw_text: str) -> Dict:
        """
        Attempt to classify fly pattern (Article 5.2: no inference).

        Uses simple string matching to extract category, size, and color.
        Article 5.2: Returns None for uncertain fields (no inference/defaults).
        Article 8.1: Deterministic classification (no ML).

        Args:
            name: Fly name (e.g., "Pheasant Tail Nymph #16 Brown")
            raw_text: Raw text from page

        Returns:
            Dict with keys: category, size, color (all optional, None if uncertain)
        """
        import re

        name_lower = name.lower()

        # Classify category using keywords
        category = None
        if any(word in name_lower for word in ["nymph", "hare", "pheasant tail", "prince"]):
            category = "nymph"
        elif any(word in name_lower for word in ["dry", "wulff", "adams", "elk hair", "parachute"]):
            category = "dry"
        elif any(
            word in name_lower for word in ["streamer", "bugger", "woolly", "muddler", "zonker"]
        ):
            category = "streamer"
        elif any(word in name_lower for word in ["wet", "soft hackle"]):
            category = "wet"

        # Extract size (number after # or size indicator)
        size = None
        size_match = re.search(r"#(\d+)", name)
        if size_match:
            size = size_match.group(1)
        else:
            # Try "size 14" format
            size_match = re.search(r"size\s+(\d+)", name_lower)
            if size_match:
                size = size_match.group(1)

        # Extract color (common fly colors)
        color = None
        colors = [
            "black",
            "brown",
            "olive",
            "gray",
            "grey",
            "white",
            "red",
            "yellow",
            "orange",
            "green",
            "blue",
            "purple",
            "pink",
            "tan",
            "gold",
            "silver",
        ]
        for c in colors:
            if c in name_lower:
                color = c
                break

        return {"category": category, "size": size, "color": color}
