"""Data validation utilities."""

from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

from jobs.config import settings
from jobs.io import load_master_list, load_json, load_csv


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    message: str
    details: dict = field(default_factory=dict)


class DataValidator:
    """Validator for pipeline data integrity."""

    def __init__(self):
        self.results = []

    def validate_master_list(self) -> ValidationResult:
        """Validate the master occupation list."""
        try:
            occupations = load_master_list()
            if not occupations:
                return ValidationResult(False, "Master list is empty")

            # Check required fields
            for occ in occupations:
                if not all(k in occ for k in ["title", "slug", "category", "url"]):
                    return ValidationResult(
                        False,
                        f"Missing required fields in occupation: {occ.get('slug', 'unknown')}"
                    )

            return ValidationResult(
                True,
                f"Master list valid: {len(occupations)} occupations",
                {"count": len(occupations)}
            )
        except Exception as e:
            return ValidationResult(False, f"Failed to load master list: {e}")

    def validate_html_files(self) -> ValidationResult:
        """Validate HTML files exist and are not empty."""
        html_dir = settings.HTML_DIR
        if not html_dir.exists():
            return ValidationResult(False, "HTML directory not found")

        html_files = list(html_dir.glob("*.html"))
        if not html_files:
            return ValidationResult(False, "No HTML files found")

        # Check for empty files
        empty_files = [f for f in html_files if f.stat().st_size == 0]
        if empty_files:
            return ValidationResult(
                False,
                f"Found {len(empty_files)} empty HTML files",
                {"empty_files": [f.name for f in empty_files[:5]]}
            )

        return ValidationResult(
            True,
            f"HTML files valid: {len(html_files)} files",
            {"count": len(html_files)}
        )

    def validate_markdown_files(self) -> ValidationResult:
        """Validate Markdown files exist and are not empty."""
        pages_dir = settings.PAGES_DIR
        if not pages_dir.exists():
            return ValidationResult(False, "Pages directory not found")

        md_files = list(pages_dir.glob("*.md"))
        if not md_files:
            return ValidationResult(False, "No Markdown files found")

        # Check for empty files
        empty_files = [f for f in md_files if f.stat().st_size == 0]
        if empty_files:
            return ValidationResult(
                False,
                f"Found {len(empty_files)} empty Markdown files",
                {"empty_files": [f.name for f in empty_files[:5]]}
            )

        return ValidationResult(
            True,
            f"Markdown files valid: {len(md_files)} files",
            {"count": len(md_files)}
        )

    def validate_csv(self) -> ValidationResult:
        """Validate CSV file."""
        csv_path = settings.PROCESSED_DIR / "occupations.csv"
        if not csv_path.exists():
            return ValidationResult(False, "CSV file not found")

        try:
            rows = load_csv(csv_path)
            if not rows:
                return ValidationResult(False, "CSV is empty")

            # Check required columns
            required_cols = ["title", "slug", "category"]
            first_row = rows[0]
            missing_cols = [col for col in required_cols if col not in first_row]
            if missing_cols:
                return ValidationResult(
                    False,
                    f"CSV missing required columns: {missing_cols}"
                )

            return ValidationResult(
                True,
                f"CSV valid: {len(rows)} rows",
                {"count": len(rows), "columns": list(first_row.keys())}
            )
        except Exception as e:
            return ValidationResult(False, f"Failed to parse CSV: {e}")

    def validate_scores(self) -> ValidationResult:
        """Validate scores JSON file."""
        scores_path = settings.PROCESSED_DIR / "scores.json"
        if not scores_path.exists():
            return ValidationResult(False, "Scores file not found")

        try:
            scores = load_json(scores_path)
            if not scores:
                return ValidationResult(False, "Scores is empty")

            # Check score values are in valid range
            invalid_scores = [
                s for s in scores
                if s.get("exposure") is not None and not (0 <= s.get("exposure") <= 10)
            ]
            if invalid_scores:
                return ValidationResult(
                    False,
                    f"Found {len(invalid_scores)} scores with invalid exposure values",
                    {"invalid": [s["slug"] for s in invalid_scores[:5]]}
                )

            with_exposure = sum(1 for s in scores if s.get("exposure") is not None)
            return ValidationResult(
                True,
                f"Scores valid: {len(scores)} entries ({with_exposure} with exposure)",
                {"count": len(scores), "with_exposure": with_exposure}
            )
        except Exception as e:
            return ValidationResult(False, f"Failed to parse scores: {e}")

    def validate_site_data(self) -> ValidationResult:
        """Validate site data JSON file."""
        site_data_path = settings.SITE_DIR / "data.json"
        if not site_data_path.exists():
            return ValidationResult(False, "Site data file not found")

        try:
            site_data = load_json(site_data_path)
            if not site_data:
                return ValidationResult(False, "Site data is empty")

            # Check required fields
            required_fields = ["title", "slug", "category"]
            missing_fields = []
            for item in site_data:
                for field in required_fields:
                    if field not in item:
                        missing_fields.append(f"{item.get('slug', 'unknown')}: {field}")

            if missing_fields:
                return ValidationResult(
                    False,
                    f"Site data missing required fields: {len(missing_fields)} items",
                    {"missing": missing_fields[:5]}
                )

            with_exposure = sum(1 for d in site_data if d.get("exposure") is not None)
            return ValidationResult(
                True,
                f"Site data valid: {len(site_data)} entries ({with_exposure} with exposure)",
                {"count": len(site_data), "with_exposure": with_exposure}
            )
        except Exception as e:
            return ValidationResult(False, f"Failed to parse site data: {e}")

    def validate_all(self) -> dict[str, ValidationResult]:
        """Run all validations."""
        return {
            "master_list": self.validate_master_list(),
            "html_files": self.validate_html_files(),
            "markdown_files": self.validate_markdown_files(),
            "csv": self.validate_csv(),
            "scores": self.validate_scores(),
            "site_data": self.validate_site_data(),
        }

    def generate_report(self) -> str:
        """Generate a human-readable validation report."""
        results = self.validate_all()

        lines = ["Data Validation Report", "=" * 50]

        for name, result in results.items():
            status = "[OK]" if result.is_valid else "[FAIL]"
            lines.append(f"{status} {name.replace('_', ' ').title()}: {result.message}")

            if result.details:
                for key, value in result.details.items():
                    lines.append(f"    {key}: {value}")

        return "\n".join(lines)
