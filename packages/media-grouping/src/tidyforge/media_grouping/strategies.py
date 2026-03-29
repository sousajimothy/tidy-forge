"""Grouping strategies for media files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from tidyforge.core.models import FileEntry
from tidyforge.metadata.categories import categorize_file


@runtime_checkable
class GroupingStrategy(Protocol):
    """Protocol for file grouping strategies.

    Each strategy computes a group key from a FileEntry. Files with the same
    key belong to the same group.
    """

    name: str

    def group_key(self, entry: FileEntry) -> str:
        """Return the group key for the given entry."""
        ...


@dataclass
class ByExtension:
    """Group files by their lowercase extension."""

    name: str = "extension"

    def group_key(self, entry: FileEntry) -> str:
        return entry.suffix if entry.suffix else "(no extension)"


@dataclass
class ByCategory:
    """Group files by their category (image, video, audio, document, etc.)."""

    name: str = "category"

    def group_key(self, entry: FileEntry) -> str:
        return categorize_file(entry.path)


@dataclass
class ByDate:
    """Group files by their modification date.

    Args:
        granularity: One of ``"year"``, ``"month"``, or ``"day"``.
    """

    granularity: str = "month"
    name: str = "date"

    def group_key(self, entry: FileEntry) -> str:
        dt = entry.modified
        if self.granularity == "year":
            return dt.strftime("%Y")
        elif self.granularity == "day":
            return dt.strftime("%Y-%m-%d")
        return dt.strftime("%Y-%m")


@dataclass
class ByParentFolder:
    """Group files by their immediate parent folder name."""

    name: str = "parent_folder"

    def group_key(self, entry: FileEntry) -> str:
        return entry.path.parent.name


@dataclass
class ByFilenamePattern:
    """Group files by a regex pattern applied to the filename.

    If the pattern contains a capture group, the first group match is used
    as the key. Otherwise, the full match is used. Files that don't match
    are placed in the ``"unmatched"`` group.

    Args:
        pattern: Regular expression pattern.
    """

    pattern: str
    name: str = "filename_pattern"

    def __post_init__(self) -> None:
        self._compiled = re.compile(self.pattern, re.IGNORECASE)

    def group_key(self, entry: FileEntry) -> str:
        match = self._compiled.search(entry.name)
        if not match:
            return "unmatched"
        if match.groups():
            return match.group(1)
        return match.group(0)
