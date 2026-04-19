"""Progress tracking for pipeline operations."""

import json
from pathlib import Path
from typing import Optional, Set

from jobs.config import settings


class ProgressTracker:
    """Track progress of pipeline operations with checkpoint support."""

    def __init__(self, state_file: Optional[Path] = None):
        """Initialize progress tracker.

        Args:
            state_file: Path to state file. Defaults to .pipeline_state.json in project root
        """
        if state_file is None:
            state_file = Path.cwd() / ".pipeline_state.json"
        self.state_file = state_file
        self.state = self._load_state()

    def _load_state(self) -> dict:
        """Load state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_state(self) -> None:
        """Save state to file."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)

    def save_checkpoint(self, step: str, completed: Set[str]) -> None:
        """Save a checkpoint for a pipeline step.

        Args:
            step: Name of the pipeline step (e.g., "scrape", "parse")
            completed: Set of item slugs that have been completed
        """
        self.state[step] = {
            "completed": list(completed),
            "count": len(completed),
            "timestamp": str(Path(__file__).stat().st_mtime)
        }
        self._save_state()

    def load_checkpoint(self, step: str) -> Set[str]:
        """Load completed items for a pipeline step.

        Args:
            step: Name of the pipeline step

        Returns:
            Set of completed item slugs
        """
        if step in self.state:
            return set(self.state[step].get("completed", []))
        return set()

    def get_step_count(self, step: str) -> int:
        """Get the count of completed items for a step.

        Args:
            step: Name of the pipeline step

        Returns:
            Number of completed items
        """
        if step in self.state:
            return self.state[step].get("count", 0)
        return 0

    def is_completed(self, step: str, item_slug: str) -> bool:
        """Check if a specific item is completed for a step.

        Args:
            step: Name of the pipeline step
            item_slug: Slug of the item to check

        Returns:
            True if the item is completed
        """
        completed = self.load_checkpoint(step)
        return item_slug in completed

    def clear_step(self, step: str) -> None:
        """Clear checkpoint data for a step.

        Args:
            step: Name of the pipeline step to clear
        """
        if step in self.state:
            del self.state[step]
            self._save_state()

    def clear_all(self) -> None:
        """Clear all checkpoint data."""
        self.state = {}
        self._save_state()

    def get_summary(self) -> dict:
        """Get a summary of all tracked steps.

        Returns:
            Dictionary with step names and completion counts
        """
        summary = {}
        for step, data in self.state.items():
            summary[step] = {
                "completed": data.get("count", 0),
                "timestamp": data.get("timestamp", "unknown")
            }
        return summary
