"""Grouping engine that applies strategies to file entries."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from tidyforge.core.models import FileEntry
from tidyforge.media_grouping.strategies import GroupingStrategy


@dataclass
class GroupSummary:
    """Summary of a single group."""

    key: str
    count: int
    total_size: int
    extensions: set[str]

    @property
    def size_human(self) -> str:
        """Human-readable total size."""
        if self.total_size == 0:
            return "0 B"
        import math

        units = ("B", "KB", "MB", "GB", "TB")
        i = min(int(math.floor(math.log(self.total_size, 1024))), len(units) - 1)
        value = self.total_size / (1024**i)
        return f"{value:.1f} {units[i]}"


class GroupingEngine:
    """Apply a grouping strategy to a collection of file entries.

    Args:
        strategy: The grouping strategy to use.
    """

    def __init__(self, strategy: GroupingStrategy) -> None:
        self.strategy = strategy

    def group(self, entries: list[FileEntry]) -> dict[str, list[FileEntry]]:
        """Group entries using the configured strategy.

        Args:
            entries: File entries to group.

        Returns:
            Dict mapping group key to list of entries in that group.
        """
        groups: dict[str, list[FileEntry]] = defaultdict(list)
        for entry in entries:
            if entry.is_dir:
                continue
            key = self.strategy.group_key(entry)
            groups[key].append(entry)
        return dict(groups)

    def group_summary(self, entries: list[FileEntry]) -> list[GroupSummary]:
        """Group entries and return a list of summaries, sorted by count descending.

        Args:
            entries: File entries to group.

        Returns:
            List of GroupSummary objects.
        """
        groups = self.group(entries)
        summaries = []
        for key, group_entries in groups.items():
            summaries.append(
                GroupSummary(
                    key=key,
                    count=len(group_entries),
                    total_size=sum(e.size for e in group_entries),
                    extensions={e.suffix for e in group_entries if e.suffix},
                )
            )
        return sorted(summaries, key=lambda s: s.count, reverse=True)
