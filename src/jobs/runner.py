"""Pipeline runner for orchestrating the data processing pipeline."""

import csv
import json
import re
from pathlib import Path
from typing import Optional

from jobs.config import Settings, settings
from jobs.io import load_master_list, save_json, load_json, save_csv, load_csv, ensure_dirs
from jobs.soup import clean_text, parse_html
from jobs.html_parser import OOHParser
from jobs.bls import BLSScraper
from jobs.llm_scorer import LLMScorer


class PipelineRunner:
    """Orchestrates the complete data processing pipeline."""

    def __init__(self, config: Optional[Settings] = None):
        self.config = config or settings
        self.parser = OOHParser(config)
        self.scraper = BLSScraper(config)
        self.scorer = LLMScorer(config)

    def run_scrape(
        self,
        start: int = 0,
        end: Optional[int] = None,
        force: bool = False,
        delay: float = 1.0
    ) -> None:
        """Run the scraping step."""
        occupations = load_master_list()
        end = end if end is not None else len(occupations)

        stats = self.scraper.scrape_batch(
            occupations,
            start=start,
            end=end,
            force=force,
            delay=delay
        )

        print(f"\nScraping complete: {stats.success} scraped, {stats.cached} cached, {stats.failed} failed")

    def run_parse(self, force: bool = False) -> None:
        """Run the HTML to Markdown parsing step."""
        occupations = load_master_list()

        ensure_dirs(self.config.PAGES_DIR)

        processed = 0
        skipped = 0
        missing = 0

        for occ in occupations:
            slug = occ["slug"]
            html_path = self.config.HTML_DIR / f"{slug}.html"
            md_path = self.config.PAGES_DIR / f"{slug}.md"

            if not html_path.exists():
                missing += 1
                continue

            if not force and md_path.exists():
                skipped += 1
                continue

            md = self.parser.parse_to_markdown(html_path)
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md)
            processed += 1

        print(f"Parsed: {processed}, Skipped (cached): {skipped}, Missing HTML: {missing}")

    def run_csv(self) -> None:
        """Run the CSV generation step."""
        occupations = load_master_list()

        fieldnames = [
            "title", "category", "slug", "soc_code",
            "median_pay_annual", "median_pay_hourly",
            "entry_education", "work_experience", "training",
            "num_jobs_2024", "projected_employment_2034",
            "outlook_pct", "outlook_desc", "employment_change",
            "url",
        ]

        rows = []
        missing = 0

        for occ in occupations:
            html_path = self.config.HTML_DIR / f"{occ['slug']}.html"
            if not html_path.exists():
                missing += 1
                continue

            row = self._extract_occupation_data(html_path, occ)
            rows.append(row)

        save_csv(rows, self.config.PROCESSED_DIR / "occupations.csv", fieldnames)
        print(f"Wrote {len(rows)} rows to occupations.csv (missing HTML: {missing})")

    def run_score(
        self,
        start: int = 0,
        end: Optional[int] = None,
        force: bool = False,
        delay: float = 0.5
    ) -> None:
        """Run the LLM scoring step."""
        occupations = load_master_list()
        end = end if end is not None else len(occupations)

        stats = self.scorer.score_batch(
            occupations,
            start=start,
            end=end,
            force=force,
            delay=delay
        )

        print(f"\nScoring complete: {stats.scored} scored, {stats.cached} cached, {stats.failed} failed")

    def run_build_site(self) -> None:
        """Run the site data building step."""
        # Load AI exposure scores
        scores_list = load_json(self.config.PROCESSED_DIR / "scores.json")
        scores = {s["slug"]: s for s in scores_list}

        # Load CSV stats
        rows = load_csv(self.config.PROCESSED_DIR / "occupations.csv")

        # Merge
        data = []
        for row in rows:
            slug = row["slug"]
            score = scores.get(slug, {})
            data.append({
                "title": row["title"],
                "slug": slug,
                "category": row["category"],
                "pay": int(row["median_pay_annual"]) if row["median_pay_annual"] else None,
                "jobs": int(row["num_jobs_2024"]) if row["num_jobs_2024"] else None,
                "outlook": int(row["outlook_pct"]) if row["outlook_pct"] else None,
                "outlook_desc": row["outlook_desc"],
                "education": row["entry_education"],
                "exposure": score.get("exposure"),
                "exposure_rationale": score.get("rationale"),
                "url": row.get("url", ""),
            })

        ensure_dirs(self.config.SITE_DIR)
        save_json(data, self.config.SITE_DIR / "data.json")

        print(f"Wrote {len(data)} occupations to site/data.json")
        total_jobs = sum(d["jobs"] for d in data if d["jobs"])
        print(f"Total jobs represented: {total_jobs:,}")

    def run(self, steps: Optional[list[str]] = None, force: bool = False) -> None:
        """Run the complete pipeline or specified steps.

        Args:
            steps: List of steps to run. If None, runs all steps.
                   Valid steps: "scrape", "parse", "csv", "score", "build_site"
            force: Force re-run even if cached
        """
        if steps is None:
            steps = ["scrape", "parse", "csv", "score", "build_site"]

        step_map = {
            "scrape": lambda: self.run_scrape(force=force),
            "parse": lambda: self.run_parse(force=force),
            "csv": self.run_csv,
            "score": lambda: self.run_score(force=force),
            "build_site": self.run_build_site,
        }

        for step in steps:
            if step not in step_map:
                print(f"Unknown step: {step}")
                continue
            print(f"\n{'='*50}")
            print(f"Running step: {step}")
            print(f"{'='*50}")
            step_map[step]()

    def _extract_occupation_data(self, html_path: Path, occ: dict) -> dict:
        """Extract structured data from HTML file."""
        soup = parse_html(str(html_path))

        row = {
            "title": occ["title"],
            "category": occ["category"],
            "slug": occ["slug"],
            "url": occ["url"],
            "soc_code": "",
            "median_pay_annual": "",
            "median_pay_hourly": "",
            "entry_education": "",
            "work_experience": "",
            "training": "",
            "num_jobs_2024": "",
            "outlook_pct": "",
            "outlook_desc": "",
            "employment_change": "",
            "projected_employment_2034": "",
        }

        # Quick Facts table
        qf_table = soup.find("table", id="quickfacts")
        if qf_table:
            tbody = qf_table.find("tbody")
            if tbody:
                for tr in tbody.find_all("tr"):
                    th = tr.find("th")
                    td = tr.find("td")
                    if not th or not td:
                        continue
                    field = clean_text(th.get_text()).lower()
                    value = clean_text(td.get_text())

                    if "median pay" in field:
                        row["median_pay_annual"], row["median_pay_hourly"] = self._parse_pay(value)
                    elif "entry-level education" in field:
                        row["entry_education"] = value
                    elif "work experience" in field:
                        row["work_experience"] = value
                    elif "on-the-job training" in field:
                        row["training"] = value
                    elif "number of jobs" in field:
                        row["num_jobs_2024"] = self._parse_number(value)
                    elif "job outlook" in field:
                        row["outlook_pct"], row["outlook_desc"] = self._parse_outlook(value)
                    elif "employment change" in field:
                        row["employment_change"] = self._parse_number(value)

        # Projections table
        outlook_table = soup.find("table", id="outlook-table")
        if outlook_table:
            tbody = outlook_table.find("tbody")
            if tbody:
                tr = tbody.find("tr")
                if tr:
                    cells = [clean_text(c.get_text()) for c in tr.find_all(["td", "th"])]
                    if len(cells) >= 4:
                        soc = cells[1]
                        if soc != "—":
                            row["soc_code"] = soc
                        row["projected_employment_2034"] = self._parse_number(cells[3])

        # Impute missing pay
        if row["median_pay_annual"] and not row["median_pay_hourly"]:
            row["median_pay_hourly"] = f"{float(row['median_pay_annual']) / 2080:.2f}"
        elif row["median_pay_hourly"] and not row["median_pay_annual"]:
            row["median_pay_annual"] = str(round(float(row["median_pay_hourly"]) * 2080))

        return row

    def _parse_pay(self, value: str) -> tuple[str, str]:
        """Parse pay string into (annual, hourly)."""
        annual = ""
        hourly = ""
        amounts = re.findall(r'\$([\d,]+(?:\.\d+)?)', value)
        if "per year" in value and "per hour" in value and len(amounts) >= 2:
            annual = amounts[0].replace(",", "")
            hourly = amounts[1].replace(",", "")
        elif "per year" in value and amounts:
            annual = amounts[0].replace(",", "")
        elif "per hour" in value and amounts:
            hourly = amounts[0].replace(",", "")
        return annual, hourly

    def _parse_outlook(self, value: str) -> tuple[str, str]:
        """Parse outlook string into (pct, description)."""
        m = re.match(r'(-?\d+)%\s*\((.+)\)', value)
        if m:
            return m.group(1), m.group(2)
        m = re.match(r'(-?\d+)%', value)
        if m:
            return m.group(1), ""
        return "", value

    def _parse_number(self, value: str) -> str:
        """Strip commas and return clean number string."""
        cleaned = value.replace(",", "").strip()
        if re.match(r'^-?\d+$', cleaned):
            return cleaned
        return value.strip()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Run the jobs pipeline")
    parser.add_argument("--steps", nargs="+", help="Steps to run: scrape parse csv score build_site")
    parser.add_argument("--force", action="store_true", help="Force re-run even if cached")
    args = parser.parse_args()

    runner = PipelineRunner()
    runner.run(steps=args.steps, force=args.force)


if __name__ == "__main__":
    main()
