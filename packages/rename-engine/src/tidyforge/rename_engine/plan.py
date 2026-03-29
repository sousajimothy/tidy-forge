"""Rename plan model with collision detection and validation."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from tidyforge.core.models import ActionManifest, OperationResult


class RenameAction(BaseModel):
    """A single planned rename operation."""

    source: Path
    destination: Path
    status: Literal["pending", "done", "skipped", "error"] = "pending"
    error: str | None = None


class RenamePlan(BaseModel):
    """A collection of rename actions with validation and preview."""

    actions: list[RenameAction] = Field(default_factory=list)

    def detect_collisions(self) -> list[str]:
        """Find destination paths that appear more than once.

        Returns:
            List of collision error messages.
        """
        dest_counts: dict[Path, int] = {}
        for action in self.actions:
            dest = action.destination.resolve()
            dest_counts[dest] = dest_counts.get(dest, 0) + 1

        return [
            f"Collision: {count:,} files target '{dest}'"
            for dest, count in dest_counts.items()
            if count > 1
        ]

    def detect_overwrites(self) -> list[str]:
        """Find destinations that already exist on disk.

        Returns:
            List of overwrite warning messages.
        """
        sources = {a.source.resolve() for a in self.actions}
        warnings = []
        for action in self.actions:
            dest = action.destination.resolve()
            if dest.exists() and dest not in sources:
                warnings.append(f"Overwrite: '{dest}' already exists")
        return warnings

    def validate(self) -> list[str]:
        """Run all validations and return a list of error/warning messages."""
        issues = []
        issues.extend(self.detect_collisions())
        issues.extend(self.detect_overwrites())

        for action in self.actions:
            if action.source == action.destination:
                issues.append(f"No-op: '{action.source}' renamed to itself")
            if not action.source.exists():
                issues.append(f"Missing: source '{action.source}' does not exist")

        return issues

    def preview(self) -> list[tuple[str, str]]:
        """Return a list of (source_name, destination_name) pairs for display.

        Returns:
            List of (old_name, new_name) tuples.
        """
        return [(action.source.name, action.destination.name) for action in self.actions]

    def execute(self, *, dry_run: bool = True) -> ActionManifest:
        """Execute or simulate the rename plan.

        Args:
            dry_run: If True, do not actually rename files (default).

        Returns:
            ActionManifest recording all operations.
        """
        manifest = ActionManifest(
            created_at=datetime.now(UTC),
            dry_run=dry_run,
        )

        for action in self.actions:
            if dry_run:
                manifest.operations.append(
                    OperationResult(
                        success=True,
                        source=action.source,
                        destination=action.destination,
                        message=f"Would rename '{action.source.name}'"
                        f" -> '{action.destination.name}'",
                    )
                )
                action.status = "done"
            else:
                try:
                    action.destination.parent.mkdir(parents=True, exist_ok=True)
                    action.source.rename(action.destination)
                    action.status = "done"
                    manifest.operations.append(
                        OperationResult(
                            success=True,
                            source=action.source,
                            destination=action.destination,
                            message=f"Renamed '{action.source.name}'"
                            f" -> '{action.destination.name}'",
                        )
                    )
                except OSError as exc:
                    action.status = "error"
                    action.error = str(exc)
                    manifest.operations.append(
                        OperationResult(
                            success=False,
                            source=action.source,
                            destination=action.destination,
                            error=str(exc),
                        )
                    )

        return manifest
