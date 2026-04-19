"""Tests for data validator."""

import pytest
from pathlib import Path
from jobs.validator import DataValidator, ValidationResult


def test_validator_initialization():
    """Test validator initialization."""
    validator = DataValidator()
    assert validator is not None
    assert validator.results == []


def test_validation_result():
    """Test ValidationResult dataclass."""
    result = ValidationResult(True, "Test message", {"key": "value"})
    assert result.is_valid is True
    assert result.message == "Test message"
    assert result.details == {"key": "value"}


def test_validate_master_list():
    """Test master list validation."""
    validator = DataValidator()
    result = validator.validate_master_list()

    # Should be valid since we have occupations.json
    assert result.is_valid is True
    assert "342" in result.message  # We know there are 342 occupations
    assert result.details.get("count") == 342


def test_validate_html_files():
    """Test HTML files validation."""
    validator = DataValidator()
    result = validator.validate_html_files()

    # Should be valid since we have html/ directory
    assert result.is_valid is True
    assert result.details.get("count") == 342


def test_validate_csv():
    """Test CSV validation."""
    validator = DataValidator()
    result = validator.validate_csv()

    # Should be valid since we have occupations.csv
    assert result.is_valid is True
    assert result.details.get("count") == 342


def test_validate_scores():
    """Test scores validation."""
    validator = DataValidator()
    result = validator.validate_scores()

    # Should be valid since we have scores.json
    assert result.is_valid is True
    assert result.details.get("count") == 342


def test_validate_site_data():
    """Test site data validation."""
    validator = DataValidator()
    result = validator.validate_site_data()

    # Should be valid since we have site/data.json
    assert result.is_valid is True
    assert result.details.get("count") == 342


def test_validate_all():
    """Test running all validations."""
    validator = DataValidator()
    results = validator.validate_all()

    # Should have results for all checks
    assert "master_list" in results
    assert "html_files" in results
    assert "markdown_files" in results
    assert "csv" in results
    assert "scores" in results
    assert "site_data" in results

    # All should be valid
    for name, result in results.items():
        assert result.is_valid is True, f"{name} validation failed: {result.message}"


def test_generate_report():
    """Test report generation."""
    validator = DataValidator()
    report = validator.generate_report()

    assert "Data Validation Report" in report
    assert "master list" in report.lower()
    assert "html files" in report.lower()
