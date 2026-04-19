"""Data models for occupations."""

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

from jobs.config import settings


class Occupation(BaseModel):
    """Represents a single occupation from BLS OOH."""

    title: str
    slug: str
    category: str
    url: str
    soc_code: Optional[str] = None
    median_pay_annual: Optional[int] = None
    median_pay_hourly: Optional[float] = None
    entry_education: Optional[str] = None
    work_experience: Optional[str] = None
    training: Optional[str] = None
    num_jobs_2024: Optional[int] = None
    projected_employment_2034: Optional[int] = None
    outlook_pct: Optional[int] = None
    outlook_desc: Optional[str] = None
    employment_change: Optional[int] = None
    ai_exposure: Optional[int] = Field(None, ge=0, le=10)
    ai_rationale: Optional[str] = None

    @property
    def html_path(self) -> Path:
        """Path to the HTML file for this occupation."""
        return settings.HTML_DIR / f"{self.slug}.html"

    @property
    def md_path(self) -> Path:
        """Path to the Markdown file for this occupation."""
        return settings.PAGES_DIR / f"{self.slug}.md"
