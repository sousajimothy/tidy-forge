"""Aggregation helpers for file entries."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from tidyforge.core.models import FileEntry


@dataclass
class ExtensionStats:
    """Statistics for a single file extension."""

    extension: str
    count: int = 0
    total_size: int = 0

    @property
    def avg_size(self) -> float:
        return self.total_size / self.count if self.count else 0.0


@dataclass
class DirStats:
    """Statistics for a single directory."""

    path: Path
    file_count: int = 0
    total_size: int = 0
    extensions: set[str] = field(default_factory=set)


def aggregate_by_extension(entries: list[FileEntry]) -> dict[str, ExtensionStats]:
    """Group file entries by extension and compute stats.

    Args:
        entries: List of file entries to aggregate.

    Returns:
        Dict mapping extension (e.g. ``".jpg"``) to ExtensionStats.
    """
    stats: dict[str, ExtensionStats] = {}
    for entry in entries:
        if entry.is_dir:
            continue
        ext = entry.suffix or "(no extension)"
        if ext not in stats:
            stats[ext] = ExtensionStats(extension=ext)
        stats[ext].count += 1
        stats[ext].total_size += entry.size
    return stats


def aggregate_by_directory(
    entries: list[FileEntry],
    depth: int | None = None,
) -> dict[Path, DirStats]:
    """Group file entries by parent directory and compute stats.

    Args:
        entries: List of file entries to aggregate.
        depth: If set, truncate directory paths to this many components
            relative to the common root.

    Returns:
        Dict mapping directory path to DirStats.
    """
    buckets: dict[Path, DirStats] = defaultdict(lambda: DirStats(path=Path()))
    for entry in entries:
        if entry.is_dir:
            continue
        parent = entry.path.parent
        if depth is not None and len(parent.parts) > depth:
            parent = Path(*parent.parts[:depth])
        if parent not in buckets:
            buckets[parent] = DirStats(path=parent)
        else:
            buckets[parent].path = parent
        buckets[parent].file_count += 1
        buckets[parent].total_size += entry.size
        buckets[parent].extensions.add(entry.suffix)
    return dict(buckets)


def top_n(
    entries: list[FileEntry],
    n: int = 10,
    *,
    key: str = "size",
    reverse: bool = True,
) -> list[FileEntry]:
    """Return the top N entries sorted by the given attribute.

    Args:
        entries: Entries to sort.
        n: Number of entries to return.
        key: Attribute name to sort by (``"size"``, ``"modified"``, ``"name"``).
        reverse: If True, return largest/newest first.

    Returns:
        A sorted list of up to *n* entries.
    """
    files = [e for e in entries if not e.is_dir]
    return sorted(files, key=lambda e: getattr(e, key), reverse=reverse)[:n]
