"""Core data models used across TidyForge packages."""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class FileEntry(BaseModel):
    """Represents a single file or directory found during scanning."""

    path: Path
    name: str
    suffix: str
    size: int
    modified: datetime
    is_dir: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def size_human(self) -> str:
        """Return a human-readable size string (e.g. '4.2 MB')."""
        if self.size == 0:
            return "0 B"
        units = ("B", "KB", "MB", "GB", "TB")
        i = int(math.floor(math.log(self.size, 1024)))
        i = min(i, len(units) - 1)
        value = self.size / (1024**i)
        return f"{value:.1f} {units[i]}"

    @classmethod
    def from_path(cls, p: Path) -> FileEntry:
        """Create a FileEntry from a filesystem path.

        Args:
            p: Path to the file or directory.

        Raises:
            OSError: If the path cannot be stat'd.
        """
        stat = p.stat()
        return cls(
            path=p,
            name=p.name,
            suffix=p.suffix.lower(),
            size=stat.st_size,
            modified=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
            is_dir=p.is_dir(),
        )


class OperationResult(BaseModel):
    """Result of a single file operation (rename, move, copy, etc.)."""

    success: bool
    source: Path
    destination: Path | None = None
    message: str = ""
    error: str | None = None


class ActionManifest(BaseModel):
    """A log of planned or executed file operations."""

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    operations: list[OperationResult] = Field(default_factory=list)
    dry_run: bool = True

    @property
    def success_count(self) -> int:
        """Number of successful operations."""
        return sum(1 for op in self.operations if op.success)

    @property
    def failure_count(self) -> int:
        """Number of failed operations."""
        return sum(1 for op in self.operations if not op.success)

    @property
    def summary(self) -> str:
        """One-line summary: counts of successes and failures."""
        mode = "DRY RUN" if self.dry_run else "EXECUTED"
        return (
            f"[{mode}] {len(self.operations):,} operations: "
            f"{self.success_count:,} succeeded, {self.failure_count:,} failed"
        )

    def to_json(self, path: Path) -> None:
        """Write the manifest to a JSON file.

        Args:
            path: Destination file path.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.model_dump(mode="json"), indent=2, default=str),
            encoding="utf-8",
        )
