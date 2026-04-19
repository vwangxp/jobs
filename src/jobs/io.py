"""File I/O utilities."""

import csv
import json
from pathlib import Path
from typing import Any, Optional

from jobs.config import settings


def load_master_list(path: Optional[Path] = None) -> list[dict]:
    """Load the master occupation list from JSON."""
    if path is None:
        # Default to occupations.json in data/raw/
        path = settings.RAW_DIR / "occupations.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, path: Path, indent: int = 2) -> None:
    """Save data to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def load_json(path: Path) -> Any:
    """Load data from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_csv(rows: list[dict], path: Path, fieldnames: Optional[list[str]] = None) -> None:
    """Save data to CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None and rows:
        fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames or [])
        writer.writeheader()
        writer.writerows(rows)


def load_csv(path: Path) -> list[dict]:
    """Load data from CSV file."""
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ensure_dirs(*paths: Path) -> None:
    """Ensure all directories exist."""
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)


def is_cached(path: Path) -> bool:
    """Check if a file exists and is not empty."""
    return path.exists() and path.stat().st_size > 0
