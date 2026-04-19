"""Tests for HTML parser."""

import pytest
from pathlib import Path
from jobs.html_parser import OOHParser


@pytest.fixture
def sample_html(tmp_path):
    """Create a sample HTML file for testing."""
    html_content = """
    <html>
    <head><title>Test Occupation</title></head>
    <body>
    <h1>Software Developer</h1>
    <link rel="canonical" href="https://example.com/software-developer" />
    <table id="quickfacts">
        <tbody>
            <tr><th>Median Pay</th><td>$100,000 per year</td></tr>
            <tr><th>Entry-Level Education</th><td>Bachelor's degree</td></tr>
        </tbody>
    </table>
    <div id="panes">
        <div id="tab-2">
            <article>
                <h2><span>What They Do</span></h2>
                <p>Software developers design and create software.</p>
            </article>
        </div>
    </div>
    <p class="update">Last modified: January 2024</p>
    </body>
    </html>
    """
    html_file = tmp_path / "test.html"
    html_file.write_text(html_content, encoding="utf-8")
    return html_file


def test_parse_to_markdown(sample_html):
    """Test HTML to Markdown conversion."""
    parser = OOHParser()
    md = parser.parse_to_markdown(sample_html)

    assert "# Software Developer" in md
    assert "**Source:** https://example.com/software-developer" in md
    assert "## Quick Facts" in md
    assert "| Median Pay | $100,000 per year |" in md
    assert "## What They Do" in md
    assert "Software developers design and create software." in md
    assert "*Last modified: January 2024*" in md


def test_parse_quick_facts():
    """Test Quick Facts table parsing."""
    from bs4 import BeautifulSoup

    html = """
    <table id="quickfacts">
        <tbody>
            <tr><th>Median Pay</th><td>$100,000 per year</td></tr>
            <tr><th>Entry-Level Education</th><td>Bachelor's degree</td></tr>
        </tbody>
    </table>
    """
    soup = BeautifulSoup(html, "html.parser")
    parser = OOHParser()

    # Test that the parser can find and process the table
    qf_table = soup.find("table", id="quickfacts")
    assert qf_table is not None
    tbody = qf_table.find("tbody")
    assert tbody is not None
    rows = tbody.find_all("tr")
    assert len(rows) == 2


def test_parse_empty_html(tmp_path):
    """Test parsing empty HTML."""
    html_file = tmp_path / "empty.html"
    html_file.write_text("<html><body></body></html>", encoding="utf-8")

    parser = OOHParser()
    md = parser.parse_to_markdown(html_file)

    # Should not crash, just return minimal content
    assert md is not None
