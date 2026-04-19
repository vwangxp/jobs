"""BLS OOH scraper module."""

import argparse
import json
import os
import time
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from playwright.sync_api import sync_playwright

from jobs.config import Settings, settings
from jobs.io import load_master_list, ensure_dirs, is_cached
from jobs.web import fetch_with_retry


@dataclass
class ScrapingStats:
    """Statistics from scraping operations."""
    total: int = 0
    success: int = 0
    cached: int = 0
    failed: int = 0
    errors: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class BLSScraper:
    """Scraper for BLS Occupational Outlook Handbook pages."""

    def __init__(self, config: Optional[Settings] = None):
        self.config = config or settings
        self.stats = ScrapingStats()

    def scrape_occupation(
        self,
        occ: dict,
        force: bool = False,
        delay: float = 1.0
    ) -> bool:
        """Scrape a single occupation page.

        Returns True if successful, False otherwise.
        """
        slug = occ["slug"]
        url = occ["url"]
        html_path = self.config.HTML_DIR / f"{slug}.html"

        self.stats.total += 1

        # Check cache
        if not force and is_cached(html_path):
            self.stats.cached += 1
            return True

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                page = browser.new_page()

                html_content = fetch_with_retry(page, url, self.config.REQUEST_TIMEOUT)

                # Save HTML
                html_path.parent.mkdir(parents=True, exist_ok=True)
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_content)

                self.stats.success += 1
                browser.close()
                return True

        except Exception as e:
            self.stats.failed += 1
            self.stats.errors.append(f"{slug}: {e}")
            return False

    def scrape_batch(
        self,
        occupations: list[dict],
        start: int = 0,
        end: Optional[int] = None,
        force: bool = False,
        delay: float = 1.0
    ) -> ScrapingStats:
        """Scrape a batch of occupations.

        Args:
            occupations: List of occupation dicts
            start: Start index (inclusive)
            end: End index (exclusive)
            force: Re-scrape even if cached
            delay: Seconds between requests

        Returns:
            ScrapingStats with results
        """
        subset = occupations[start:end]
        ensure_dirs(self.config.HTML_DIR, self.config.DATA_DIR, self.config.PAGES_DIR)

        print(f"Scraping {len(subset)} occupations...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            for i, occ in enumerate(subset, start=start):
                slug = occ["slug"]
                url = occ["url"]
                html_path = self.config.HTML_DIR / f"{slug}.html"

                self.stats.total += 1

                # Check cache
                if not force and is_cached(html_path):
                    print(f"  [{i}] CACHED {occ['title']}")
                    self.stats.cached += 1
                    continue

                print(f"  [{i}] {occ['title']}...", end=" ", flush=True)

                try:
                    html_content = fetch_with_retry(page, url, self.config.REQUEST_TIMEOUT)

                    html_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(html_content)

                    print(f"OK ({len(html_content):,} bytes)")
                    self.stats.success += 1

                except Exception as e:
                    print(f"ERROR: {e}")
                    self.stats.failed += 1
                    self.stats.errors.append(f"{slug}: {e}")

                # Be polite
                if i < len(subset) - 1:
                    time.sleep(delay)

            browser.close()

        return self.stats


def main():
    parser = argparse.ArgumentParser(description="Scrape BLS OOH pages")
    parser.add_argument("--start", type=int, default=0, help="Start index")
    parser.add_argument("--end", type=int, default=None, help="End index")
    parser.add_argument("--force", action="store_true", help="Re-scrape even if cached")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds between requests")
    args = parser.parse_args()

    occupations = load_master_list()
    end = args.end if args.end is not None else len(occupations)

    scraper = BLSScraper()
    stats = scraper.scrape_batch(
        occupations,
        start=args.start,
        end=end,
        force=args.force,
        delay=args.delay
    )

    print(f"\nDone. {stats.success} scraped, {stats.cached} cached, {stats.failed} failed")
    if stats.errors:
        print(f"Errors: {stats.errors[:5]}")  # Show first 5 errors


if __name__ == "__main__":
    main()
