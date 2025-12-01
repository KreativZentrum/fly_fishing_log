#!/usr/bin/env python3
"""
CLI entry point for NZ Flyfishing Web Scraper.
Article 7.1 Compliance: Source-agnostic (database-first design).
"""

import argparse
import sys

from .config import Config
from .logger import ScraperLogger
from .storage import Storage
from .fetcher import Fetcher
from .parser import Parser
from .exceptions import ConfigError, HaltError


def scrape_command(args, config: Config, logger: ScraperLogger):
    """
    Execute scraping workflow.

    US1: Region discovery workflow.
    US2: River discovery workflow (to be implemented in Phase 4).
    US3: River detail extraction (to be implemented in Phase 5).

    Args:
        args: Parsed CLI arguments (--all, --refresh, --region)
        config: Configuration instance
        logger: Logger instance
    """
    from datetime import datetime

    storage = Storage(config.database_path, logger)
    storage.initialize_schema()

    fetcher = Fetcher(config, logger)
    parser = Parser(config)

    try:
        # US1: Region Discovery
        if args.all or not args.region:
            logger.info("Starting region discovery...")
            print("Discovering regions from index page...")

            # Fetch index page
            index_url = config.base_url + config.discovery_rules.get("index_path", "/index.html")

            try:
                html = fetcher.fetch(index_url, use_cache=not args.refresh, refresh=args.refresh)
            except Exception as e:
                logger.error(f"Failed to fetch index page: {e}")
                print(f"Error: Could not fetch index page: {e}")
                return

            # Parse regions
            regions = parser.parse_region_index(html)
            logger.info(f"Discovered {len(regions)} regions")
            print(f"Found {len(regions)} regions")

            # Store regions
            crawl_timestamp = datetime.utcnow().isoformat() + "Z"

            for region in regions:
                # Check if region exists
                existing = storage.get_regions()
                existing_urls = {r["canonical_url"] for r in existing}

                action = "UPDATE" if region["canonical_url"] in existing_urls else "INSERT"

                # Insert/update region
                region_id = storage.insert_region(
                    name=region["name"],
                    slug=region["slug"],
                    canonical_url=region["canonical_url"],
                    source_url=index_url,
                    raw_html=html,  # Store index page HTML
                    description=region.get("description", ""),
                    crawl_timestamp=crawl_timestamp,
                )

                # Log discovery
                logger.log_discovery(
                    entity_type="region", entity_name=region["name"], action=action
                )

                print(f"  [{action}] {region['name']} (ID: {region_id})")

            print(f"\nRegion discovery complete: {len(regions)} regions stored")

        # US2: River Discovery
        if args.region or args.all:
            # Determine which regions to process
            if args.region:
                # Query specific region by slug or ID
                try:
                    region_id = int(args.region)
                    region = storage.get_region(region_id)
                    if not region:
                        logger.error(f"Region ID {region_id} not found")
                        print(f"Error: Region ID {region_id} not found")
                        return
                    regions_to_process = [region]
                except ValueError:
                    # Assume it's a slug
                    all_regions = storage.get_regions()
                    matching = [r for r in all_regions if r["slug"] == args.region]
                    if not matching:
                        logger.error(f"Region slug '{args.region}' not found")
                        print(f"Error: Region slug '{args.region}' not found")
                        return
                    regions_to_process = matching
            else:
                # Process all regions
                regions_to_process = storage.get_regions()

            logger.info(f"Starting river discovery for {len(regions_to_process)} region(s)...")
            print(f"\nDiscovering rivers from {len(regions_to_process)} region(s)...")

            total_rivers = 0

            for region in regions_to_process:
                print(f"\n  Processing region: {region['name']}...")

                # Fetch region page
                region_url = region["canonical_url"]

                try:
                    html = fetcher.fetch(
                        region_url, use_cache=not args.refresh, refresh=args.refresh
                    )
                except Exception as e:
                    logger.error(f"Failed to fetch region page {region_url}: {e}")
                    print(f"    Error: Could not fetch region page: {e}")
                    continue  # Graceful handling (Article 4.4)

                # Parse rivers from region page
                try:
                    rivers = parser.parse_region_page(html, region)
                except Exception as e:
                    logger.error(f"Failed to parse region page {region_url}: {e}")
                    print(f"    Error: Could not parse region page: {e}")
                    continue

                logger.info(f"Discovered {len(rivers)} rivers in {region['name']}")
                print(f"    Found {len(rivers)} rivers")

                # Store rivers
                crawl_timestamp = datetime.utcnow().isoformat() + "Z"

                for river in rivers:
                    # Check if river exists (by canonical URL)
                    existing = storage.get_rivers()
                    existing_urls = {r["canonical_url"] for r in existing}

                    action = "UPDATE" if river["canonical_url"] in existing_urls else "INSERT"

                    # Insert/update river
                    river_id = storage.insert_river(
                        region_id=region["id"],
                        name=river["name"],
                        slug=river["slug"],
                        canonical_url=river["canonical_url"],
                        raw_html="",  # Empty for now, will be populated in US3
                        crawl_timestamp=crawl_timestamp,
                    )

                    # Log discovery
                    logger.log_discovery(
                        entity_type="river", entity_name=river["name"], action=action
                    )

                    print(f"      [{action}] {river['name']} (ID: {river_id})")
                    total_rivers += 1

            print(f"\nRiver discovery complete: {total_rivers} rivers processed")

        # US3: River Detail Extraction
        if args.all or args.details:
            logger.info("Starting river detail extraction...")
            print(f"\nExtracting river details...")

            # Get all rivers that need detail extraction
            rivers_to_extract = storage.get_rivers()

            # Filter rivers that need refresh (optional: crawl_timestamp older than 24hr)
            if not args.refresh:
                from datetime import datetime, timedelta

                cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat() + "Z"
                rivers_to_extract = [
                    r
                    for r in rivers_to_extract
                    if not r.get("crawl_timestamp") or r["crawl_timestamp"] < cutoff
                ]

            print(f"  Processing {len(rivers_to_extract)} rivers...")

            total_extracted = 0
            total_flies = 0
            total_regulations = 0

            for river in rivers_to_extract:
                print(f"\n  River: {river['name']}...")

                # Fetch river detail page
                try:
                    html = fetcher.fetch(
                        river["canonical_url"], use_cache=not args.refresh, refresh=args.refresh
                    )
                except Exception as e:
                    logger.error(f"Failed to fetch river {river['canonical_url']}: {e}")
                    print(f"    Error: Could not fetch river page: {e}")
                    continue  # Article 4.4: graceful handling

                # Parse river details
                try:
                    details = parser.parse_river_detail(html, river)
                except Exception as e:
                    logger.error(f"Failed to parse river {river['canonical_url']}: {e}")
                    print(f"    Error: Could not parse river page: {e}")
                    continue

                # Store flies
                flies_stored = 0
                for fly_data in details["flies"]:
                    try:
                        storage.insert_fly(
                            river_id=river["id"],
                            name=fly_data["name"],
                            raw_text=fly_data["raw_text"],
                            category=fly_data.get("category"),
                            size=fly_data.get("size"),
                            color=fly_data.get("color"),
                            crawl_timestamp=datetime.utcnow().isoformat() + "Z",
                        )
                        flies_stored += 1
                    except Exception as e:
                        logger.error(f"Failed to store fly '{fly_data['name']}': {e}")

                # Store regulations
                regs_stored = 0
                for reg_data in details["regulations"]:
                    try:
                        storage.insert_regulation(
                            river_id=river["id"],
                            type=reg_data["type"],
                            value=reg_data["value"],
                            raw_text=reg_data["raw_text"],
                            crawl_timestamp=datetime.utcnow().isoformat() + "Z",
                        )
                        regs_stored += 1
                    except Exception as e:
                        logger.error(f"Failed to store regulation: {e}")

                # Update river with new crawl timestamp and description
                try:
                    description = details.get("fish_type", {}).get("raw_text", "")
                    storage.insert_river(
                        region_id=river["region_id"],
                        name=river["name"],
                        slug=river["slug"],
                        canonical_url=river["canonical_url"],
                        raw_html=html,
                        description=description,
                        crawl_timestamp=datetime.utcnow().isoformat() + "Z",
                    )
                except Exception as e:
                    logger.error(f"Failed to update river: {e}")

                # Store metadata for change detection
                try:
                    import hashlib

                    raw_hash = hashlib.md5(html.encode()).hexdigest()
                    storage.insert_metadata(
                        session_id=f"scrape-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
                        entity_id=river["id"],
                        entity_type="river",
                        raw_content_hash=raw_hash,
                        crawl_timestamp=datetime.utcnow().isoformat() + "Z",
                    )
                except Exception as e:
                    logger.error(f"Failed to store metadata: {e}")

                # Count fields with data vs null (Article 5.2 compliance)
                fields_with_data = sum(
                    [
                        1 if details.get("fish_type") else 0,
                        1 if details.get("conditions") else 0,
                        len(details.get("flies", [])),
                    ]
                )
                fields_null = sum(
                    [
                        1 if not details.get("fish_type") else 0,
                        1 if not details.get("conditions") else 0,
                    ]
                )

                # Log extraction
                logger.log_extraction(
                    river_name=river["name"],
                    flies_count=flies_stored,
                    regulations_count=regs_stored,
                    fields_with_data=fields_with_data,
                    fields_null=fields_null,
                )

                print(f"    Extracted: {flies_stored} flies, {regs_stored} regulations")

                total_extracted += 1
                total_flies += flies_stored
                total_regulations += regs_stored

            print(
                f"\nDetail extraction complete: {total_extracted} rivers, {total_flies} flies, {total_regulations} regulations"
            )

    finally:
        fetcher.close()
        storage.close()


def query_command(args, config: Config, logger: ScraperLogger):
    """
    Query database and print results.

    Implementation stub.

    Args:
        args: Parsed CLI arguments (regions, rivers, river --river-id)
        config: Configuration instance
        logger: Logger instance
    """
    storage = Storage(config.database_path, logger)

    if args.query_type == "regions":
        regions = storage.get_regions()
        print(f"Found {len(regions)} regions:")
        for r in regions:
            print(f"  [{r['id']}] {r['name']} ({r['slug']})")

    elif args.query_type == "rivers":
        if args.region_id:
            rivers = storage.get_rivers_by_region(args.region_id)
        else:
            rivers = storage.get_rivers()
        print(f"Found {len(rivers)} rivers:")
        for r in rivers:
            print(f"  [{r['id']}] {r['name']} ({r['slug']})")

    elif args.query_type == "river":
        if not args.river_id:
            print("Error: --river-id required for river query")
            sys.exit(1)
        river = storage.get_river(args.river_id)
        if not river:
            print(f"River {args.river_id} not found")
            sys.exit(1)

        print(f"River: {river['name']}")
        print(f"Region ID: {river['region_id']}")
        print(f"Canonical URL: {river['canonical_url']}")
        print(f"Crawled: {river['crawl_timestamp']}")

        # Sections
        sections = storage.get_sections_by_river(args.river_id)
        print(f"\nSections ({len(sections)}):")
        for s in sections:
            print(f"  - {s['name']}")

        # Flies
        flies = storage.get_flies_by_river(args.river_id)
        print(f"\nRecommended Flies ({len(flies)}):")
        for f in flies:
            print(f"  - {f['name']} ({f['raw_text']})")

        # Regulations
        regulations = storage.get_regulations_by_river(args.river_id)
        print(f"\nRegulations ({len(regulations)}):")
        for reg in regulations:
            print(f"  - {reg['type']}: {reg['value']}")

    storage.close()


def cache_command(args, config: Config, logger: ScraperLogger):
    """
    Manage HTTP cache.

    Args:
        args: Parsed CLI arguments (--clear, --stats)
        config: Configuration instance
        logger: Logger instance
    """
    fetcher = Fetcher(config, logger)

    if args.cache_action == "clear":
        fetcher.clear_cache()
        print("Cache cleared")

    elif args.cache_action == "stats":
        stats = fetcher.get_cache_stats()
        print("Cache Statistics:")
        print(f"  Hits: {stats['hits']}")
        print(f"  Misses: {stats['misses']}")
        print(f"  Total: {stats['total']}")
        print(f"  Hit Rate: {stats['hit_rate']:.2%}")
        print(f"  Bytes Cached: {stats['bytes_cached']:,}")

    fetcher.close()


def pdf_command(args, config: Config, logger: ScraperLogger):
    """
    Generate PDF exports.

    Implementation stub - will be completed in Phase 8 (US6).

    Args:
        args: Parsed CLI arguments (--river-id, --region)
        config: Configuration instance
        logger: Logger instance
    """
    logger.info("PDF generation not yet implemented")
    print("PDF generation will be implemented in Phase 8")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="NZ Flyfishing Web Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape all regions and rivers
  python -m src.cli scrape --all

  # Refresh existing data
  python -m src.cli scrape --refresh

  # Extract river details for all rivers
  python -m src.cli scrape --details

  # Query all regions
  python -m src.cli query regions

  # Query rivers in a region
  python -m src.cli query rivers --region-id 1

  # View river details
  python -m src.cli query river --river-id 42

  # Cache management
  python -m src.cli cache --stats
  python -m src.cli cache --clear

  # PDF generation (coming in Phase 8)
  python -m src.cli pdf --river-id 42
  python -m src.cli pdf --region 1
        """,
    )

    # Global options
    parser.add_argument(
        "--config", default="config/nzfishing_config.yaml", help="Path to configuration file"
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Run web scraper")
    scrape_parser.add_argument("--all", action="store_true", help="Scrape all regions and rivers")
    scrape_parser.add_argument(
        "--refresh", action="store_true", help="Refresh existing data (ignore cache)"
    )
    scrape_parser.add_argument(
        "--region", type=int, metavar="ID", help="Scrape specific region by ID"
    )
    scrape_parser.add_argument(
        "--details", action="store_true", help="Extract river details for all rivers"
    )

    # Query command
    query_parser = subparsers.add_parser("query", help="Query database")
    query_parser.add_argument(
        "query_type", choices=["regions", "rivers", "river"], help="Type of query to run"
    )
    query_parser.add_argument("--region-id", type=int, metavar="ID", help="Filter by region ID")
    query_parser.add_argument(
        "--river-id", type=int, metavar="ID", help="Query specific river by ID"
    )

    # Cache command
    cache_parser = subparsers.add_parser("cache", help="Manage HTTP cache")
    cache_parser.add_argument(
        "cache_action", choices=["clear", "stats"], help="Cache action to perform"
    )

    # PDF command
    pdf_parser = subparsers.add_parser("pdf", help="Generate PDF exports")
    pdf_parser.add_argument(
        "--river-id", type=int, metavar="ID", help="Generate PDF for specific river"
    )
    pdf_parser.add_argument(
        "--region", type=int, metavar="ID", help="Generate PDFs for all rivers in region"
    )

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Load configuration
    try:
        config = Config(args.config)
    except ConfigError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    # Initialize logger
    logger = ScraperLogger(config.log_path)

    # Route to command handler
    try:
        if args.command == "scrape":
            scrape_command(args, config, logger)
        elif args.command == "query":
            query_command(args, config, logger)
        elif args.command == "cache":
            cache_command(args, config, logger)
        elif args.command == "pdf":
            pdf_command(args, config, logger)
    except HaltError as e:
        logger.log_halt(str(e))
        print(f"Scraper halted: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
