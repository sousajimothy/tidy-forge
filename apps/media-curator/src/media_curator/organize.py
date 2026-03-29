"""Organize plan — move or copy files into date-grouped subdirectories."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from tqdm import tqdm

from tidyforge.core.models import ActionManifest, FileEntry, OperationResult


class OrganizeAction(BaseModel):
    """A single planned organize operation."""

    source: Path
    destination: Path
    status: Literal["pending", "done", "skipped", "error"] = "pending"
    error: str | None = None


class OrganizePlan(BaseModel):
    """A collection of organize actions with validation, preview, and execution."""

    actions: list[OrganizeAction] = Field(default_factory=list)
    mode: Literal["move", "copy"] = "move"

    def detect_collisions(self) -> list[str]:
        """Find destination paths that appear more than once."""
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
        """Find destinations that already exist on disk and are not sources."""
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
            if not action.source.exists():
                issues.append(f"Missing: source '{action.source}' does not exist")
        return issues

    def preview(self) -> list[tuple[str, str]]:
        """Return (source_name, destination_relative) pairs for display."""
        return [
            (action.source.name, str(action.destination))
            for action in self.actions
        ]

    def execute(self, *, dry_run: bool = True) -> ActionManifest:
        """Execute or simulate the organize plan.

        Args:
            dry_run: If True, do not actually move/copy files (default).

        Returns:
            ActionManifest recording all operations.
        """
        verb = "copy" if self.mode == "copy" else "move"
        manifest = ActionManifest(created_at=datetime.now(UTC), dry_run=dry_run)

        show_progress = not dry_run and len(self.actions) > 0
        actions_iter = (
            tqdm(
                self.actions,
                desc=f"{verb.capitalize()}ing files",
                unit="file",
                bar_format=(
                    "{l_bar}{bar}| {n_fmt}/{total_fmt}"
                    " [{elapsed}<{remaining}, {rate_fmt}]"
                ),
            )
            if show_progress
            else self.actions
        )

        for action in actions_iter:
            if dry_run:
                manifest.operations.append(
                    OperationResult(
                        success=True,
                        source=action.source,
                        destination=action.destination,
                        message=(
                            f"Would {verb} '{action.source.name}'"
                            f" -> '{action.destination}'"
                        ),
                    )
                )
                action.status = "done"
            else:
                try:
                    action.destination.parent.mkdir(parents=True, exist_ok=True)
                    if self.mode == "copy":
                        shutil.copy2(action.source, action.destination)
                    else:
                        shutil.move(str(action.source), action.destination)
                    action.status = "done"
                    manifest.operations.append(
                        OperationResult(
                            success=True,
                            source=action.source,
                            destination=action.destination,
                            message=(
                                f"{verb.capitalize()}d '{action.source.name}'"
                                f" -> '{action.destination}'"
                            ),
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


def build_organize_plan(
    entries: list[FileEntry],
    dest_dir: Path,
    date_format: str = "%Y%m",
    mode: Literal["move", "copy"] = "move",
    group_fn: Callable[[FileEntry], str] | None = None,
    skip_unmatched: bool = False,
) -> OrganizePlan:
    """Build an OrganizePlan mapping each entry to dest_dir/<group>/<filename>.

    Args:
        entries: Files to organise.
        dest_dir: Root destination directory. Group subdirectories are
            created inside it.
        date_format: strftime format for the subfolder name (default ``"%Y%m"``
            produces e.g. ``"202601"``). Ignored when *group_fn* is provided.
        mode: ``"move"`` (default) or ``"copy"``.
        group_fn: Optional callable that takes a :class:`FileEntry` and returns
            the subfolder name. When provided, this overrides *date_format*.
        skip_unmatched: When True, entries whose group resolves to
            ``"unmatched"`` are left out of the plan entirely.

    Returns:
        An OrganizePlan with one action per file entry.
    """
    actions = []
    for entry in entries:
        if entry.is_dir:
            continue
        group = group_fn(entry) if group_fn is not None else entry.modified.strftime(date_format)
        if skip_unmatched and group == "unmatched":
            continue
        destination = dest_dir / group / entry.name
        actions.append(OrganizeAction(source=entry.path, destination=destination))
    return OrganizePlan(actions=actions, mode=mode)
