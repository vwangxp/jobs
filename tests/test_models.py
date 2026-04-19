"""Tests for jobs package."""

import pytest
from pathlib import Path
from jobs.occupation import Occupation


def test_occupation_creation():
    """Test creating an Occupation model."""
    occ = Occupation(
        title="Test Occupation",
        slug="test-occupation",
        category="test",
        url="https://example.com/test"
    )
    assert occ.title == "Test Occupation"
    assert occ.slug == "test-occupation"
    assert occ.ai_exposure is None


def test_occupation_validation():
    """Test Occupation field validation."""
    # Valid exposure
    occ = Occupation(
        title="Test",
        slug="test",
        category="test",
        url="https://example.com",
        ai_exposure=5
    )
    assert occ.ai_exposure == 5

    # Invalid exposure (should raise ValidationError)
    with pytest.raises(Exception):
        Occupation(
            title="Test",
            slug="test",
            category="test",
            url="https://example.com",
            ai_exposure=11  # Out of range
        )


def test_occupation_paths():
    """Test Occupation path properties."""
    occ = Occupation(
        title="Test",
        slug="test-occupation",
        category="test",
        url="https://example.com"
    )
    # Paths are now absolute paths from settings
    assert occ.html_path.name == "test-occupation.html"
    assert occ.html_path.suffix == ".html"
    assert occ.md_path.name == "test-occupation.md"
    assert occ.md_path.suffix == ".md"


def test_occupation_serialization():
    """Test Occupation serialization."""
    occ = Occupation(
        title="Test",
        slug="test",
        category="test",
        url="https://example.com",
        median_pay_annual=50000,
        ai_exposure=7
    )
    data = occ.model_dump()
    assert data["title"] == "Test"
    assert data["median_pay_annual"] == 50000
    assert data["ai_exposure"] == 7
