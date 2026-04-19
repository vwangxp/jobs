"""Tests for utility functions."""

import pytest
import json
import csv
from pathlib import Path
from jobs.io import save_json, load_json, save_csv, load_csv, is_cached
from jobs.soup import clean_text, parse_html, safe_find, extract_table


def test_clean_text():
    """Test text cleaning."""
    assert clean_text("  hello  world  ") == "hello world"
    assert clean_text("hello\nworld") == "hello world"
    assert clean_text("hello\tworld") == "hello world"


def test_json_io(tmp_path):
    """Test JSON save/load."""
    data = {"test": "value", "number": 42}
    path = tmp_path / "test.json"

    save_json(data, path)
    assert path.exists()

    loaded = load_json(path)
    assert loaded == data


def test_csv_io(tmp_path):
    """Test CSV save/load."""
    data = [
        {"name": "Alice", "age": "30"},
        {"name": "Bob", "age": "25"}
    ]
    path = tmp_path / "test.csv"

    save_csv(data, path)
    assert path.exists()

    loaded = load_csv(path)
    assert len(loaded) == 2
    assert loaded[0]["name"] == "Alice"


def test_is_cached(tmp_path):
    """Test cache checking."""
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("")
    assert not is_cached(empty_file)

    non_empty = tmp_path / "non_empty.txt"
    non_empty.write_text("content")
    assert is_cached(non_empty)

    non_existent = tmp_path / "non_existent.txt"
    assert not is_cached(non_existent)


def test_safe_find():
    """Test safe_find utility."""
    from bs4 import BeautifulSoup

    html = "<div><p>test</p></div>"
    soup = BeautifulSoup(html, "html.parser")

    # Should find the element
    p = safe_find(soup, "p")
    assert p is not None
    assert p.get_text() == "test"

    # Should return None for non-existent element
    h1 = safe_find(soup, "h1")
    assert h1 is None
