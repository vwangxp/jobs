"""Command-line interface for the jobs pipeline."""

import argparse
import os
import sys
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.table import Table

from jobs.config import settings
from jobs.runner import PipelineRunner
from jobs.io import load_master_list, load_json, load_csv

console = Console()


def cmd_scrape(args):
    """Scrape BLS pages."""
    console.print("[bold cyan]Scraping BLS pages...[/bold cyan]")
    runner = PipelineRunner()
    runner.run_scrape(
        start=args.start,
        end=args.end,
        force=args.force,
        delay=args.delay
    )
    console.print("[green]Scraping complete![/green]")


def cmd_parse(args):
    """Parse HTML to Markdown."""
    console.print("[bold cyan]Parsing HTML to Markdown...[/bold cyan]")
    runner = PipelineRunner()
    runner.run_parse(force=args.force)
    console.print("[green]Parsing complete![/green]")


def cmd_csv(args):
    """Generate CSV summary."""
    console.print("[bold cyan]Generating CSV summary...[/bold cyan]")
    runner = PipelineRunner()
    runner.run_csv()
    console.print("[green]CSV generation complete![/green]")


def cmd_score(args):
    """Score AI exposure."""
    console.print(f"[bold cyan]Scoring AI exposure with {args.model}...[/bold cyan]")
    runner = PipelineRunner()
    runner.config.LLM_MODEL = args.model
    runner.run_score(
        start=args.start,
        end=args.end,
        force=args.force,
        delay=args.delay
    )
    console.print("[green]Scoring complete![/green]")


def cmd_build(args):
    """Build site data."""
    console.print("[bold cyan]Building site data...[/bold cyan]")
    runner = PipelineRunner()
    runner.run_build_site()
    console.print("[green]Site data build complete![/green]")


def cmd_all(args):
    """Run complete pipeline."""
    console.print("[bold cyan]Running complete pipeline...[/bold cyan]")
    runner = PipelineRunner()
    runner.run(force=args.force)
    console.print("[green]Pipeline complete![/green]")


def cmd_status(args):
    """Check data completeness."""
    console.print("\n[bold blue]Data Status Check[/bold blue]")
    console.print("=" * 50)

    # Create a table for results
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="white")

    # Check master list
    try:
        occupations = load_master_list()
        table.add_row("Master list", "[green]OK[/green]", f"{len(occupations)} occupations")
    except Exception as e:
        table.add_row("Master list", "[red]FAIL[/red]", str(e))

    # Check HTML files
    html_dir = settings.HTML_DIR
    if html_dir.exists():
        html_files = list(html_dir.glob("*.html"))
        table.add_row("HTML files", "[green]OK[/green]", f"{len(html_files)} files")
    else:
        table.add_row("HTML files", "[red]FAIL[/red]", "Directory not found")

    # Check Markdown files
    pages_dir = settings.PAGES_DIR
    if pages_dir.exists():
        md_files = list(pages_dir.glob("*.md"))
        table.add_row("Markdown files", "[green]OK[/green]", f"{len(md_files)} files")
    else:
        table.add_row("Markdown files", "[red]FAIL[/red]", "Directory not found")

    # Check CSV
    csv_path = settings.PROCESSED_DIR / "occupations.csv"
    if csv_path.exists():
        rows = load_csv(csv_path)
        table.add_row("CSV", "[green]OK[/green]", f"{len(rows)} rows")
    else:
        table.add_row("CSV", "[red]FAIL[/red]", "File not found")

    # Check scores
    scores_path = settings.PROCESSED_DIR / "scores.json"
    if scores_path.exists():
        scores = load_json(scores_path)
        with_exposure = sum(1 for s in scores if s.get("exposure") is not None)
        table.add_row("Scores", "[green]OK[/green]", f"{len(scores)} entries ({with_exposure} with exposure)")
    else:
        table.add_row("Scores", "[red]FAIL[/red]", "File not found")

    # Check site data
    site_data_path = settings.SITE_DIR / "data.json"
    if site_data_path.exists():
        site_data = load_json(site_data_path)
        with_exposure = sum(1 for d in site_data if d.get("exposure") is not None)
        table.add_row("Site data", "[green]OK[/green]", f"{len(site_data)} entries ({with_exposure} with exposure)")
    else:
        table.add_row("Site data", "[red]FAIL[/red]", "File not found")

    console.print(table)


def cmd_test(args):
    """Run tests."""
    import subprocess
    import sys

    console.print("[bold cyan]Running tests...[/bold cyan]")

    # Run pytest with the correct PYTHONPATH
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.parent)

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v"],
        env=env,
        cwd=Path.cwd()
    )

    if result.returncode == 0:
        console.print("[green]All tests passed![/green]")
    else:
        console.print("[red]Some tests failed![/red]")
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(
        description="US Job Market Visualizer Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m jobs.cli scrape              # Scrape all pages
  python -m jobs.cli scrape --start 0 --end 10  # Scrape first 10
  python -m jobs.cli parse               # Parse all HTML
  python -m jobs.cli csv                 # Generate CSV
  python -m jobs.cli score               # Score all occupations
  python -m jobs.cli build               # Build site data
  python -m jobs.cli all                 # Run complete pipeline
  python -m jobs.cli status              # Check data status
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape BLS pages")
    scrape_parser.add_argument("--start", type=int, default=0, help="Start index")
    scrape_parser.add_argument("--end", type=int, default=None, help="End index")
    scrape_parser.add_argument("--force", action="store_true", help="Re-scrape even if cached")
    scrape_parser.add_argument("--delay", type=float, default=1.0, help="Seconds between requests")
    scrape_parser.set_defaults(func=cmd_scrape)

    # parse command
    parse_parser = subparsers.add_parser("parse", help="Parse HTML to Markdown")
    parse_parser.add_argument("--force", action="store_true", help="Re-parse even if cached")
    parse_parser.set_defaults(func=cmd_parse)

    # csv command
    csv_parser = subparsers.add_parser("csv", help="Generate CSV summary")
    csv_parser.set_defaults(func=cmd_csv)

    # score command
    score_parser = subparsers.add_parser("score", help="Score AI exposure")
    score_parser.add_argument("--model", default="google/gemini-3-flash-preview", help="LLM model")
    score_parser.add_argument("--start", type=int, default=0, help="Start index")
    score_parser.add_argument("--end", type=int, default=None, help="End index")
    score_parser.add_argument("--force", action="store_true", help="Re-score even if cached")
    score_parser.add_argument("--delay", type=float, default=0.5, help="Seconds between requests")
    score_parser.set_defaults(func=cmd_score)

    # build command
    build_parser = subparsers.add_parser("build", help="Build site data")
    build_parser.set_defaults(func=cmd_build)

    # all command
    all_parser = subparsers.add_parser("all", help="Run complete pipeline")
    all_parser.add_argument("--force", action="store_true", help="Force re-run even if cached")
    all_parser.set_defaults(func=cmd_all)

    # status command
    status_parser = subparsers.add_parser("status", help="Check data status")
    status_parser.set_defaults(func=cmd_status)

    # test command
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.set_defaults(func=cmd_test)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
