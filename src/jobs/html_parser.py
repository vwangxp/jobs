"""HTML parser for BLS OOH pages."""

import re
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup, Tag

from jobs.config import Settings, settings
from jobs.soup import clean_text, parse_html, safe_find


class OOHParser:
    """Parser for BLS Occupational Outlook Handbook HTML pages."""

    def __init__(self, config: Optional[Settings] = None):
        self.config = config or settings

    def parse_to_markdown(self, html_path: Path) -> str:
        """Parse HTML file and convert to Markdown."""
        soup = parse_html(str(html_path))
        md = []

        # Title
        h1 = soup.find("h1")
        title = clean_text(h1.get_text()) if h1 else "Unknown Occupation"
        md.append(f"# {title}")
        md.append("")

        # Source URL
        canonical = soup.find("link", rel="canonical")
        if canonical:
            md.append(f"**Source:** {canonical['href']}")
            md.append("")

        # Quick Facts
        qf_table = soup.find("table", id="quickfacts")
        if qf_table:
            md.append("## Quick Facts")
            md.append("")
            md.append("| Field | Value |")
            md.append("|-------|-------|")
            for row in qf_table.find("tbody").find_all("tr"):
                th = row.find("th")
                td = row.find("td")
                if th and td:
                    field = clean_text(th.get_text())
                    value = clean_text(td.get_text())
                    md.append(f"| {field} | {value} |")
            md.append("")

        # Tab sections
        panes = soup.find("div", id="panes")
        if panes:
            self._parse_tabs(panes, md)

        # Last Modified
        update_p = soup.find("p", class_="update")
        if update_p:
            md.append("---")
            md.append(f"*{clean_text(update_p.get_text())}*")
            md.append("")

        return "\n".join(md)

    def _parse_tabs(self, panes: Tag, md: list[str]) -> None:
        """Parse tab content sections."""
        tab_ids = ["tab-1", "tab-2", "tab-3", "tab-4", "tab-5", "tab-6", "tab-7", "tab-8", "tab-9"]
        skip_tabs = ("tab-1", "tab-7", "tab-8", "tab-9")

        for tab_id in tab_ids:
            if tab_id in skip_tabs:
                continue

            tab_div = panes.find("div", id=tab_id)
            if not tab_div:
                continue

            article = tab_div.find("article") or tab_div
            h2 = article.find("h2")
            if not h2:
                continue

            section_title = clean_text(
                h2.find("span").get_text() if h2.find("span") else h2.get_text()
            )

            md.append(f"## {section_title}")
            md.append("")

            self._parse_article_content(article, md, tab_id)

    def _parse_article_content(self, article: Tag, md: list[str], tab_id: str) -> None:
        """Parse content within an article section."""
        # Process pay chart if present
        chart_div = article.find("div", class_="ooh-chart")
        if chart_div:
            self._parse_chart(chart_div, md)

        # Process remaining content
        for elem in article.children:
            if not hasattr(elem, "name"):
                continue

            if elem.name == "h2":
                continue
            if elem.name == "div" and "ooh-chart" in elem.get("class", []):
                continue
            if elem.name == "div" and "ooh_right_img" in elem.get("class", []):
                continue

            if elem.name == "h3":
                md.append(f"### {clean_text(elem.get_text())}")
                md.append("")
            elif elem.name == "p":
                text = clean_text(elem.get_text())
                if text:
                    md.append(text)
                    md.append("")
            elif elem.name == "ul":
                for li in elem.find_all("li"):
                    md.append(f"- {clean_text(li.get_text())}")
                md.append("")
            elif elem.name == "table" and elem.get("id") != "outlook-table":
                self._parse_table(elem, md)

        # Employment projections table
        if tab_id == "tab-6":
            outlook_table = article.find("table", id="outlook-table")
            if outlook_table:
                self._parse_outlook_table(outlook_table, md)

    def _parse_chart(self, chart_div: Tag, md: list[str]) -> None:
        """Parse pay chart data."""
        chart_subtitle = chart_div.find("p")
        dts = chart_div.find("dl")
        if not dts:
            return

        items = []
        dt_list = dts.find_all("dt")
        dd_list = dts.find_all("dd")
        for dt, dd in zip(dt_list, dd_list):
            label = clean_text(dt.get_text())
            val_spans = dd.find_all("span")
            for s in val_spans:
                val_text = clean_text(s.get_text())
                if val_text and (val_text.startswith("$") or val_text.endswith("%")):
                    items.append((label, val_text))
                    break

        if items:
            subtitle = clean_text(chart_subtitle.get_text()) if chart_subtitle else ""
            if subtitle:
                md.append(f"*{subtitle}*")
                md.append("")
            for label, val in items:
                md.append(f"- **{label}**: {val}")
            md.append("")

    def _parse_table(self, table: Tag, md: list[str]) -> None:
        """Parse generic table."""
        rows = table.find_all("tr")
        if not rows:
            return

        table_data = []
        for row in rows:
            cells = row.find_all(["td", "th"])
            row_data = [clean_text(c.get_text()) for c in cells]
            if row_data and any(row_data):
                table_data.append(row_data)

        if table_data:
            max_cols = max(len(r) for r in table_data)
            for r in table_data:
                while len(r) < max_cols:
                    r.append("")
            md.append("| " + " | ".join(["---"] * max_cols) + " |")
            for row_data in table_data:
                md.append("| " + " | ".join(row_data) + " |")
            md.append("")

    def _parse_outlook_table(self, table: Tag, md: list[str]) -> None:
        """Parse employment projections table."""
        md.append("### Employment Projections")
        md.append("")

        tbody = table.find("tbody")
        if not tbody:
            return

        for row in tbody.find_all("tr"):
            cells = row.find_all(["td", "th"])
            values = [clean_text(c.get_text()) for c in cells]
            if values:
                labels = [
                    "Occupational Title", "SOC Code", "Employment 2024",
                    "Projected Employment 2034", "Change % 2024-34",
                    "Change Numeric 2024-34"
                ]
                for label, val in zip(labels, values):
                    if val and val != "Get data":
                        md.append(f"- **{label}:** {val}")
                md.append("")
