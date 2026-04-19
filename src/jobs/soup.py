"""BeautifulSoup utilities."""

import re
from bs4 import BeautifulSoup, Tag
from typing import Optional


def clean_text(text: str) -> str:
    """Clean up whitespace from extracted text."""
    return re.sub(r"\s+", " ", text).strip()


def parse_html(html_path: str) -> BeautifulSoup:
    """Parse HTML file into BeautifulSoup object."""
    with open(html_path, "r", encoding="utf-8") as f:
        return BeautifulSoup(f.read(), "html.parser")


def safe_find(soup: BeautifulSoup, *args, **kwargs) -> Optional[Tag]:
    """Safely find an element, returning None if not found."""
    try:
        return soup.find(*args, **kwargs)
    except Exception:
        return None


def extract_table(soup: BeautifulSoup, table_id: str) -> list[dict]:
    """Extract table data as list of dicts."""
    table = soup.find("table", id=table_id)
    if not table:
        return []

    tbody = table.find("tbody")
    if not tbody:
        return []

    rows = []
    for tr in tbody.find_all("tr"):
        th = tr.find("th")
        td = tr.find("td")
        if th and td:
            rows.append({
                "field": clean_text(th.get_text()),
                "value": clean_text(td.get_text())
            })
    return rows
