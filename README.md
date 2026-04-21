# US Job Market Visualizer

A research tool for visually exploring Bureau of Labor Statistics [Occupational Outlook Handbook](https://www.bls.gov/ooh/) data. This is not a report, a paper, or a serious economic publication — it is a development tool for exploring BLS data visually.

**Live demo: [karpathy.ai/jobs](https://karpathy.ai/jobs/)**

## What's here

The BLS OOH covers **342 occupations** spanning every sector of the US economy, with detailed data on job duties, work environment, education requirements, pay, and employment projections. We scraped all of it and built an interactive treemap visualization where each rectangle's **area** is proportional to total employment and **color** shows the selected metric — toggle between BLS projected growth outlook, median pay, education requirements, and AI exposure.

## LLM-powered coloring

The repo includes scrapers, parsers, and a pipeline for writing custom LLM prompts to score and color occupations by any criteria. You write a prompt, the LLM scores each occupation, and the treemap colors accordingly. The "Digital AI Exposure" layer is one example — it estimates how much current AI (which is primarily digital) will reshape each occupation. But you could write a different prompt for any question — e.g. exposure to humanoid robotics, offshoring risk, climate impact — and re-run the pipeline to get a different coloring. See `score.py` for the prompt and scoring pipeline.

**What "AI Exposure" is NOT:**
- It does **not** predict that a job will disappear. Software developers score 9/10 because AI is transforming their work — but demand for software could easily *grow* as each developer becomes more productive.
- It does **not** account for demand elasticity, latent demand, regulatory barriers, or social preferences for human workers.
- The scores are rough LLM estimates (Gemini Flash via OpenRouter), not rigorous predictions. Many high-exposure jobs will be reshaped, not replaced.

## Data pipeline

1. **Scrape** (`bls.py`) — Playwright (non-headless, BLS blocks bots) downloads raw HTML for all 342 occupation pages into `data/html/`.
2. **Parse** (`html_parser.py`) — BeautifulSoup converts raw HTML into clean Markdown files in `data/pages/`.
3. **Tabulate** (`runner.py`) — Extracts structured fields (pay, education, job count, growth outlook, SOC code) into `data/processed/occupations.csv`.
4. **Score** (`llm_scorer.py`) — Sends each occupation's Markdown description to an LLM with a scoring rubric. Each occupation gets an AI Exposure score from 0-10 with a rationale. Results saved to `data/processed/scores.json`. Fork this to write your own prompts.
5. **Build site data** (`runner.py`) — Merges CSV stats and AI exposure scores into a compact `site/data.json` for the frontend.
6. **Website** (`site/index.html`) — Interactive treemap visualization with four color layers: BLS Outlook, Median Pay, Education, and Digital AI Exposure.

## Key files

| File | Description |
|------|-------------|
| `occupations.json` | Master list of 342 occupations with title, URL, category, slug |
| `occupations.csv` | Summary stats: pay, education, job count, growth projections |
| `scores.json` | AI exposure scores (0-10) with rationales for all 342 occupations |
| `prompt.md` | All data in a single file, designed to be pasted into an LLM for analysis |
| `html/` | Raw HTML pages from BLS (source of truth, ~40MB) |
| `pages/` | Clean Markdown versions of each occupation page |
| `site/` | Static website (treemap visualization) |

## LLM prompt

[`prompt.md`](prompt.md) packages all the data — aggregate statistics, tier breakdowns, exposure by pay/education, BLS growth projections, and all 342 occupations with their scores and rationales — into a single file (~45K tokens) designed to be pasted into an LLM. This lets you have a data-grounded conversation about AI's impact on the job market without needing to run any code. Regenerate it with `uv run python make_prompt.py`.

## Setup

```bash
# Install dependencies
uv sync

# Install Playwright browser
uv run playwright install chromium

# Set up API key
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

Requires an OpenRouter API key in `.env`:
```
OPENROUTER_API_KEY=your_key_here
```

## Usage

The refactored pipeline uses a unified CLI interface:

```bash
# Run complete pipeline
uv run python -m jobs.cli all

# Run individual steps
uv run python -m jobs.cli scrape              # Scrape BLS pages
uv run python -m jobs.cli parse               # Parse HTML to Markdown
uv run python -m jobs.cli csv                 # Generate CSV summary
uv run python -m jobs.cli score               # Score AI exposure
uv run python -m jobs.cli build               # Build site data

# Check data status
uv run python -m jobs.cli status

# Run with options
uv run python -m jobs.cli scrape --start 0 --end 10  # Scrape first 10
uv run python -m jobs.cli scrape --force             # Re-scrape all
uv run python -m jobs.cli score --model google/gemini-3-flash-preview
```
