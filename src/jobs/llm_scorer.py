"""LLM scorer for AI exposure rating."""

import argparse
import json
import os
import time
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv

from jobs.config import Settings, settings
from jobs.io import load_master_list, save_json, load_json, is_cached

load_dotenv()

SYSTEM_PROMPT = """\
You are an expert analyst evaluating how exposed different occupations are to \
AI. You will be given a detailed description of an occupation from the Bureau \
of Labor Statistics.

Rate the occupation's overall **AI Exposure** on a scale from 0 to 10.

AI Exposure measures: how much will AI reshape this occupation? Consider both \
direct effects (AI automating tasks currently done by humans) and indirect \
effects (AI making each worker so productive that fewer are needed).

A key signal is whether the job's work product is fundamentally digital. If \
the job can be done entirely from a home office on a computer — writing, \
coding, analyzing, communicating — then AI exposure is inherently high (7+), \
because AI capabilities in digital domains are advancing rapidly. Conversely, \
jobs requiring physical presence, manual skill, or real-time human \
interaction in the physical world have a natural barrier to AI exposure.

Use these anchors to calibrate your score:

- **0–1: Minimal exposure.** The work is almost entirely physical, hands-on, \
or requires real-time human presence in unpredictable environments. AI has \
essentially no impact on daily work. \
Examples: roofer, landscaper, commercial diver.

- **2–3: Low exposure.** Mostly physical or interpersonal work. AI might help \
with minor peripheral tasks (scheduling, paperwork) but doesn't touch the \
core job. \
Examples: electrician, plumber, firefighter, dental hygienist.

- **4–5: Moderate exposure.** A mix of physical/interpersonal work and \
knowledge work. AI can meaningfully assist with the information-processing \
parts but a substantial share of the job still requires human presence. \
Examples: registered nurse, police officer, veterinarian.

- **6–7: High exposure.** Predominantly knowledge work with some need for \
human judgment, relationships, or physical presence. AI tools are already \
useful and workers using AI may be substantially more productive. \
Examples: teacher, manager, accountant, journalist.

- **8–9: Very high exposure.** The job is almost entirely done on a computer. \
All core tasks — writing, coding, analyzing, designing, communicating — are \
in domains where AI is rapidly improving. The occupation faces major \
restructuring. \
Examples: software developer, graphic designer, translator, data analyst, \
paralegal, copywriter.

- **10: Maximum exposure.** Routine information processing, fully digital, \
with no physical component. AI can already do most of it today. \
Examples: data entry clerk, telemarketer.

Respond with ONLY a JSON object in this exact format, no other text:
{
  "exposure": <0-10>,
  "rationale": "<2-3 sentences explaining the key factors>"
}\
"""


@dataclass
class ScoringStats:
    """Statistics from scoring operations."""
    total: int = 0
    scored: int = 0
    cached: int = 0
    failed: int = 0
    errors: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class LLMScorer:
    """LLM-based scorer for AI exposure."""

    API_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, config: Optional[Settings] = None):
        self.config = config or settings
        self.stats = ScoringStats()
        self.client = httpx.Client(timeout=60)
        self.OUTPUT_FILE = self.config.PROCESSED_DIR / "scores.json"

    def score_occupation(self, occ: dict, text: str) -> Optional[dict]:
        """Score a single occupation.

        Returns dict with 'exposure' and 'rationale', or None on failure.
        """
        try:
            response = self.client.post(
                self.API_URL,
                headers={
                    "Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY', self.config.OPENROUTER_API_KEY)}",
                },
                json={
                    "model": self.config.LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": text},
                    ],
                    "temperature": self.config.LLM_TEMPERATURE,
                },
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]

            # Strip markdown code fences
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

            return json.loads(content)

        except Exception as e:
            self.stats.failed += 1
            self.stats.errors.append(f"{occ['slug']}: {e}")
            return None

    def score_batch(
        self,
        occupations: list[dict],
        start: int = 0,
        end: Optional[int] = None,
        force: bool = False,
        delay: float = 0.5
    ) -> ScoringStats:
        """Score a batch of occupations.

        Args:
            occupations: List of occupation dicts
            start: Start index (inclusive)
            end: End index (exclusive)
            force: Re-score even if cached
            delay: Seconds between requests

        Returns:
            ScoringStats with results
        """
        subset = occupations[start:end]

        # Load existing scores
        scores = {}
        if self.OUTPUT_FILE.exists() and not force:
            for entry in load_json(self.OUTPUT_FILE):
                scores[entry["slug"]] = entry

        print(f"Scoring {len(subset)} occupations with {self.config.LLM_MODEL}")
        print(f"Already cached: {len(scores)}")

        for i, occ in enumerate(subset, start=start):
            slug = occ["slug"]

            if slug in scores:
                self.stats.cached += 1
                continue

            md_path = self.config.PAGES_DIR / f"{slug}.md"
            if not is_cached(md_path):
                print(f"  [{i+1}] SKIP {slug} (no markdown)")
                continue

            with open(md_path, "r", encoding="utf-8") as f:
                text = f.read()

            print(f"  [{i+1}/{len(subset)}] {occ['title']}...", end=" ", flush=True)

            result = self.score_occupation(occ, text)
            if result:
                scores[slug] = {
                    "slug": slug,
                    "title": occ["title"],
                    **result,
                }
                print(f"exposure={result['exposure']}")
                self.stats.scored += 1

            # Save after each one (incremental checkpoint)
            save_json(list(scores.values()), self.OUTPUT_FILE)

            if i < len(subset) - 1:
                time.sleep(delay)

        self.stats.total = len(subset)
        return self.stats


def main():
    parser = argparse.ArgumentParser(description="Score AI exposure")
    parser.add_argument("--model", default="google/gemini-3-flash-preview")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=None)
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    occupations = load_master_list()
    end = args.end if args.end is not None else len(occupations)

    scorer = LLMScorer()
    scorer.config.LLM_MODEL = args.model
    stats = scorer.score_batch(
        occupations,
        start=args.start,
        end=end,
        force=args.force,
        delay=args.delay
    )

    print(f"\nDone. Scored {stats.scored} occupations, {stats.cached} cached, {stats.failed} failed")
    if stats.errors:
        print(f"Errors: {stats.errors[:5]}")


if __name__ == "__main__":
    main()
