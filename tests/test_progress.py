"""Tests for progress tracker."""

import pytest
from pathlib import Path
from jobs.progress import ProgressTracker


def test_progress_tracker_initialization():
    """Test progress tracker initialization."""
    tracker = ProgressTracker()
    # Now uses absolute path to project root
    assert tracker.state_file.name == ".pipeline_state.json"
    assert tracker.state_file.suffix == ".json"


def test_save_and_load_checkpoint():
    """Test saving and loading checkpoints."""
    tracker = ProgressTracker(Path("test_state.json"))

    # Save checkpoint
    completed = {"item1", "item2", "item3"}
    tracker.save_checkpoint("test_step", completed)

    # Load checkpoint
    loaded = tracker.load_checkpoint("test_step")
    assert loaded == completed

    # Cleanup
    Path("test_state.json").unlink(missing_ok=True)


def test_get_step_count():
    """Test getting step count."""
    tracker = ProgressTracker(Path("test_state.json"))

    # Save checkpoint
    completed = {"item1", "item2", "item3"}
    tracker.save_checkpoint("test_step", completed)

    # Get count
    count = tracker.get_step_count("test_step")
    assert count == 3

    # Cleanup
    Path("test_state.json").unlink(missing_ok=True)


def test_is_completed():
    """Test checking if item is completed."""
    tracker = ProgressTracker(Path("test_state.json"))

    # Save checkpoint
    completed = {"item1", "item2", "item3"}
    tracker.save_checkpoint("test_step", completed)

    # Check completed items
    assert tracker.is_completed("test_step", "item1") is True
    assert tracker.is_completed("test_step", "item2") is True
    assert tracker.is_completed("test_step", "item4") is False

    # Cleanup
    Path("test_state.json").unlink(missing_ok=True)


def test_clear_step():
    """Test clearing a step."""
    tracker = ProgressTracker(Path("test_state.json"))

    # Save checkpoint
    completed = {"item1", "item2"}
    tracker.save_checkpoint("test_step", completed)

    # Clear step
    tracker.clear_step("test_step")

    # Should be empty
    assert tracker.load_checkpoint("test_step") == set()
    assert tracker.get_step_count("test_step") == 0

    # Cleanup
    Path("test_state.json").unlink(missing_ok=True)


def test_clear_all():
    """Test clearing all steps."""
    tracker = ProgressTracker(Path("test_state.json"))

    # Save multiple checkpoints
    tracker.save_checkpoint("step1", {"item1"})
    tracker.save_checkpoint("step2", {"item2"})

    # Clear all
    tracker.clear_all()

    # Should be empty
    assert tracker.state == {}

    # Cleanup
    Path("test_state.json").unlink(missing_ok=True)


def test_get_summary():
    """Test getting summary."""
    tracker = ProgressTracker(Path("test_state.json"))

    # Save checkpoints
    tracker.save_checkpoint("step1", {"item1", "item2"})
    tracker.save_checkpoint("step2", {"item3"})

    # Get summary
    summary = tracker.get_summary()
    assert "step1" in summary
    assert "step2" in summary
    assert summary["step1"]["completed"] == 2
    assert summary["step2"]["completed"] == 1

    # Cleanup
    Path("test_state.json").unlink(missing_ok=True)


def test_empty_checkpoint():
    """Test loading empty checkpoint."""
    tracker = ProgressTracker(Path("test_state.json"))

    # Load non-existent step
    loaded = tracker.load_checkpoint("non_existent")
    assert loaded == set()

    # Get count for non-existent step
    count = tracker.get_step_count("non_existent")
    assert count == 0
