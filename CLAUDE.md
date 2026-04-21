# US Job Market Visualizer - Project Documentation

## Overview

This project visualizes Bureau of Labor Statistics (BLS) Occupational Outlook Handbook data with a focus on AI exposure across 342 US occupations. It provides an interactive treemap visualization where rectangle area represents employment size and color represents various metrics including AI exposure.

**Live Demo:** https://karpathy.ai/jobs/

## Architecture

### Data Pipeline

```
BLS Website → bls.py → data/html/ → html_parser.py → data/pages/ → runner.py → data/processed/occupations.csv
                                                              ↓
                                                        llm_scorer.py → data/processed/scores.json
                                                              ↓
                                                        runner.py → site/data.json
                                                              ↓
                                                        site/index.html (visualization)
```

### Key Components

| Component | Module | Purpose |
|-----------|--------|---------|
| **Configuration** | `config.py` | Centralized settings management with Pydantic |
| **Data Models** | `occupation.py` | Pydantic models with validation |
| **Utilities** | `io.py`, `soup.py`, `web.py`, `progress.py`, `validator.py` | Reusable I/O, parsing, web, progress tracking, and validation functions |
| **Scraper** | `bls.py` | Downloads raw HTML from BLS OOH using Playwright |
| **Parser** | `html_parser.py` | Converts HTML to clean Markdown |
| **Scorer** | `llm_scorer.py` | Uses LLM to rate AI exposure (0-10) for each occupation |
| **Pipeline** | `runner.py` | Orchestrates the complete data processing pipeline |
| **CLI** | `cli.py` | Unified command-line interface |
| **Prompt Generator** | `old_py/make_prompt.py` | Creates single-file LLM prompt with all data (legacy) |
| **Visualization** | `site/index.html` | Interactive treemap frontend |

## Data Sources

### Input Data
- **data/raw/occupations.json**: Master list of 342 occupations with URLs and categories
- **data/html/**: Raw HTML files from BLS (source of truth, ~40MB)
- **data/pages/**: Clean Markdown versions of each occupation

### Output Data
- **data/processed/occupations.csv**: Structured summary (pay, education, jobs, outlook)
- **data/processed/scores.json**: AI exposure scores (0-10) with rationales
- **site/data.json**: Merged data for frontend visualization
- **prompt.md**: Single-file LLM prompt (~45K tokens)

## Key Data Fields

### From BLS (occupations.csv)
- `title`: Occupation name
- `category`: BLS category
- `soc_code`: Standard Occupational Classification code
- `median_pay_annual`: Annual median pay
- `median_pay_hourly`: Hourly median pay
- `entry_education`: Required education level
- `work_experience`: Required work experience
- `training`: Required on-the-job training
- `num_jobs_2024`: Employment count in 2024
- `projected_employment_2034`: Projected employment in 2034
- `outlook_pct`: Percent change 2024-2034
- `outlook_desc`: BLS outlook description
- `employment_change`: Numeric employment change

### From LLM (scores.json)
- `exposure`: AI exposure score (0-10)
- `rationale`: 2-3 sentence explanation

## AI Exposure Scoring

### Methodology

The AI exposure score measures how much AI will reshape an occupation, considering:
- Direct effects (AI automating tasks)
- Indirect effects (AI making workers more productive, reducing headcount)

**Key heuristic:** Jobs that can be done entirely from a home office on a computer have inherently high exposure (7+), as AI capabilities in digital domains advance rapidly.

### Score Anchors

| Score | Level | Examples |
|-------|-------|----------|
| 0-1 | Minimal | Roofer, landscaper, commercial diver |
| 2-3 | Low | Electrician, plumber, firefighter, dental hygienist |
| 4-5 | Moderate | Registered nurse, police officer, veterinarian |
| 6-7 | High | Teacher, manager, accountant, journalist |
| 8-9 | Very high | Software developer, graphic designer, translator, data analyst |
| 10 | Maximum | Data entry clerk, telemarketer |

### LLM Configuration

- **Model:** Google Gemini 3 Flash Preview (via OpenRouter)
- **Temperature:** 0.2 (low variance)
- **System Prompt:** Detailed rubric with calibration anchors
- **Output:** JSON with `exposure` (0-10) and `rationale` (2-3 sentences)

## Development Workflow

### Initial Setup

```bash
# Install dependencies
uv sync

# Install Playwright browser
uv run playwright install chromium

# Set up API key
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

### Running the Pipeline

The refactored pipeline uses a unified CLI:

```bash
# Run complete pipeline
PYTHONPATH=src uv run python -m jobs.cli all

# Run individual steps
PYTHONPATH=src uv run python -m jobs.cli scrape              # Scrape BLS pages
PYTHONPATH=src uv run python -m jobs.cli parse               # Parse HTML to Markdown
PYTHONPATH=src uv run python -m jobs.cli csv                 # Generate CSV summary
PYTHONPATH=src uv run python -m jobs.cli score               # Score AI exposure
PYTHONPATH=src uv run python -m jobs.cli build               # Build site data

# Check data status
PYTHONPATH=src uv run python -m jobs.cli status

# Run tests
PYTHONPATH=src uv run python -m jobs.cli test

# Run with options
PYTHONPATH=src uv run python -m jobs.cli scrape --start 0 --end 10  # Scrape first 10
PYTHONPATH=src uv run python -m jobs.cli scrape --force             # Re-scrape all
PYTHONPATH=src uv run python -m jobs.cli scrape --delay 2.0          # 2 second delay between requests
PYTHONPATH=src uv run python -m jobs.cli score --model google/gemini-3-flash-preview
PYTHONPATH=src uv run python -m jobs.cli score --delay 1.0           # 1 second delay between requests
```

### Legacy Scripts

The original scripts are available in `old_py/` for reference:

```bash
# 1. Scrape BLS pages (cached in data/html/)
uv run python old_py/scrape.py

# 2. Convert HTML to Markdown
uv run python old_py/process.py

# 3. Generate CSV summary
uv run python old_py/make_csv.py

# 4. Score AI exposure (requires API key)
uv run python old_py/score.py

# 5. Build website data
uv run python old_py/build_site_data.py

# 6. Generate LLM prompt
uv run python old_py/make_prompt.py

# 7. Serve locally
cd site && python -m http.server 8000
```

### Partial Runs

```bash
# Scrape specific range
PYTHONPATH=src uv run python -m jobs.cli scrape --start 0 --end 10

# Score specific range
PYTHONPATH=src uv run python -m jobs.cli score --start 0 --end 10

# Force re-scrape
PYTHONPATH=src uv run python -m jobs.cli scrape --force
```

## Known Issues

### Data Completeness
- 2 occupations missing pay data
- 1 occupation missing job count
- 1 occupation missing outlook data

### Encoding
- Recent fixes added `encoding="utf-8"` to file operations to support non-ASCII characters

### Dependencies
- Playwright requires separate browser installation
- OpenRouter API key required for scoring

## File Structure

```
jobs/
├── .env.example             # Environment variable template
├── .env                     # API keys (not committed)
├── .gitignore
├── .python-version
├── .venv/                   # Virtual environment
├── pyproject.toml           # Dependencies
├── uv.lock                  # Lock file
├── README.md                # User documentation
├── CLAUDE.md                # This file
├── prompt.md                # LLM prompt file
├── occupational_outlook_handbook.html  # BLS index page
├── data/                    # Data directory
│   ├── html/                # Raw HTML files (342 files)
│   ├── pages/               # Markdown files (342 files)
│   ├── raw/                 # occupations.json
│   └── processed/            # CSV, scores.json
├── site/                    # Static website
│   ├── index.html           # Treemap visualization
│   └── data.json            # Merged data for frontend
├── src/jobs/                # Python package (flat structure)
│   ├── __init__.py
│   ├── config.py            # Configuration management
│   ├── cli.py               # Unified CLI
│   ├── bls.py               # BLS scraper
│   ├── html_parser.py       # HTML parser
│   ├── io.py                # File I/O utilities
│   ├── llm_scorer.py         # LLM scorer
│   ├── occupation.py         # Data models
│   ├── progress.py          # Progress tracking
│   ├── runner.py            # Pipeline runner
│   ├── soup.py              # BeautifulSoup utilities
│   └── validator.py         # Data validation
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── test_models.py       # Model tests
│   ├── test_parser.py       # Parser tests
│   ├── test_scorer.py       # Scorer tests
│   ├── test_utils.py       # Utility tests
│   ├── test_validator.py     # Validator tests
│   └── test_progress.py     # Progress tracker tests
└── old_py/                  # Legacy scripts (backward compatibility)
    ├── build_site_data.py
    ├── make_csv.py
    ├── make_prompt.py
    ├── parse_detail.py
    ├── parse_occupations.py
    ├── process.py
    ├── score.py
    └── scrape.py
```

## Important Notes

### What AI Exposure is NOT
- Does NOT predict job disappearance
- Does NOT account for demand elasticity, regulatory barriers, or social preferences
- Scores are rough LLM estimates, not rigorous predictions
- High exposure jobs will be reshaped, not necessarily replaced

### Caching Strategy
- HTML files are cached in `data/html/` and reused
- Markdown files are cached in `data/pages/`
- Scores are incrementally saved to `data/processed/scores.json`
- Use `--force` flag to bypass cache

### API Usage
- OpenRouter API is used for LLM scoring
- Default model: `google/gemini-3-flash-preview`
- Can be changed via `--model` flag
- Rate limiting: default 0.5s delay between requests (configurable via `--delay`)
- Request timeout: 15 seconds

## Testing

The project includes a pytest-based test suite:

```bash
# Run all tests
PYTHONPATH=src uv run pytest tests/

# Run with coverage
PYTHONPATH=src uv run pytest tests/ --cov=jobs

# Run specific test file
PYTHONPATH=src uv run pytest tests/test_models.py

# Run tests via CLI
PYTHONPATH=src uv run python -m jobs.cli test
```

### Test Coverage

- `tests/test_models.py`: Pydantic model validation and serialization
- `tests/test_parser.py`: HTML parser tests
- `tests/test_scorer.py`: LLM scorer tests
- `tests/test_utils.py`: Utility function tests (I/O, text cleaning, safe_find, etc.)
- `tests/test_validator.py`: Data validation tests
- `tests/test_progress.py`: Progress tracking tests

### Manual Testing

For end-to-end validation:
1. Verify HTML scraping produces valid files
2. Check Markdown output is clean and readable
3. Validate CSV contains expected fields
4. Confirm scores are within 0-10 range
5. Test website loads and displays correctly

## Deployment

The `site/` directory contains static files that can be deployed to any static hosting service:
- GitHub Pages
- Netlify
- Vercel
- Cloudflare Pages

No build step required - just upload `site/` contents.

## Contributing

### Code Organization

The refactored codebase follows a modular architecture with a flat structure:

- **Configuration**: Centralized in `config.py` using Pydantic Settings
- **Models**: Data validation in `occupation.py` using Pydantic
- **Utilities**: Reusable functions in `io.py`, `soup.py`, `web.py`, `progress.py`, `validator.py`
- **Modules**: Domain-specific logic in `bls.py`, `html_parser.py`, `llm_scorer.py`
- **Pipeline**: Orchestration in `runner.py`
- **CLI**: Unified interface in `cli.py`

### Path Management

All paths are centralized in `config.py` using `Path.cwd()` as the project root:

```python
class Settings(BaseSettings):
    DATA_DIR: Path = get_project_root() / "data"
    HTML_DIR: Path = get_project_root() / "data" / "html"
    PAGES_DIR: Path = get_project_root() / "data" / "pages"
    SITE_DIR: Path = get_project_root() / "site"
    RAW_DIR: Path = get_project_root() / "data" / "raw"
    PROCESSED_DIR: Path = get_project_root() / "data" / "processed"
```

This ensures portability and avoids hardcoded `.parent.parent.parent` patterns.

### Adding New Features

1. **New data field**: Add to `Occupation` model in `occupation.py`
2. **New parsing logic**: Add method to `OOHParser` in `html_parser.py`
3. **New pipeline step**: Add method to `PipelineRunner` in `runner.py`
4. **New CLI command**: Add subparser in `cli.py`
5. **New path**: Update `config.py` settings

### Testing

When modifying the pipeline:
1. Test on a small subset first (`--start 0 --end 5`)
2. Verify output format matches expectations
3. Check for encoding issues with non-ASCII characters
4. Run the test suite: `PYTHONPATH=src uv run pytest tests/`
5. Update this documentation if architecture changes

### Dependencies

- Use `uv` for dependency management
- Add new dependencies to `pyproject.toml`
- Run `uv sync` to update lock file
