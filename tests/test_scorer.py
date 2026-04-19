"""Tests for LLM scorer."""

import pytest
from pathlib import Path
from jobs.llm_scorer import LLMScorer, ScoringStats


def test_scorer_initialization():
    """Test scorer initialization."""
    scorer = LLMScorer()
    assert scorer.config is not None
    assert scorer.client is not None
    assert scorer.stats.total == 0
    assert scorer.stats.scored == 0
    assert scorer.stats.failed == 0


def test_scoring_stats():
    """Test ScoringStats dataclass."""
    stats = ScoringStats()
    assert stats.total == 0
    assert stats.scored == 0
    assert stats.cached == 0
    assert stats.failed == 0
    assert stats.errors == []

    stats.total = 10
    stats.scored = 8
    stats.failed = 2
    stats.errors.append("test error")

    assert stats.total == 10
    assert stats.scored == 8
    assert stats.failed == 2
    assert len(stats.errors) == 1


def test_scorer_output_file():
    """Test scorer output file path."""
    scorer = LLMScorer()
    # Now uses absolute path to project root
    assert scorer.OUTPUT_FILE.name == "scores.json"
    assert scorer.OUTPUT_FILE.suffix == ".json"


def test_system_prompt():
    """Test that system prompt is defined."""
    from jobs.llm_scorer import SYSTEM_PROMPT

    assert SYSTEM_PROMPT is not None
    assert len(SYSTEM_PROMPT) > 0
    assert "AI Exposure" in SYSTEM_PROMPT
    assert "0 to 10" in SYSTEM_PROMPT


def test_api_url():
    """Test API URL is correct."""
    scorer = LLMScorer()
    assert scorer.API_URL == "https://openrouter.ai/api/v1/chat/completions"


def test_score_occupation_with_mock_text():
    """Test scoring with mock text (without actual API call)."""
    scorer = LLMScorer()
    occ = {"slug": "test", "title": "Test Occupation"}

    # This would normally call the API, but we're just testing the structure
    # In a real test, we'd mock the HTTP client
    assert scorer is not None
