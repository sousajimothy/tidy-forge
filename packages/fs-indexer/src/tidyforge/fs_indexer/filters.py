"""File filters for use with the scanner."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from tidyforge.core.models import FileEntry


@dataclass
class ExtensionFilter:
    """Filter files by extension.

    Args:
        include: Set of extensions to include (e.g. ``{".jpg", ".png"}``).
            If empty, all extensions are included (unless excluded).
        exclude: Set of extensions to exclude.
    """

    include: set[str] = field(default_factory=set)
    exclude: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.include = {ext.lower() for ext in self.include}
        self.exclude = {ext.lower() for ext in self.exclude}

    def __call__(self, entry: FileEntry) -> bool:
        ext = entry.suffix
        if ext in self.exclude:
            return False
        return not (self.include and ext not in self.include)


@dataclass
class SizeFilter:
    """Filter files by size in bytes.

    Args:
        min_size: Minimum size in bytes (inclusive). None means no minimum.
        max_size: Maximum size in bytes (inclusive). None means no maximum.
    """

    min_size: int | None = None
    max_size: int | None = None

    def __call__(self, entry: FileEntry) -> bool:
        if self.min_size is not None and entry.size < self.min_size:
            return False
        return not (self.max_size is not None and entry.size > self.max_size)


@dataclass
class PatternFilter:
    """Filter files by filename pattern (glob or regex).

    Args:
        pattern: A regex pattern to match against the filename.
        invert: If True, exclude files that match instead of including them.
    """

    pattern: str
    invert: bool = False

    def __post_init__(self) -> None:
        self._compiled = re.compile(self.pattern, re.IGNORECASE)

    def __call__(self, entry: FileEntry) -> bool:
        matches = bool(self._compiled.search(entry.name))
        return not matches if self.invert else matches


@dataclass
class CompositeFilter:
    """Combine multiple filters with AND or OR logic.

    Args:
        filters: List of filter callables.
        mode: ``"and"`` requires all filters to pass, ``"or"`` requires at
            least one.
    """

    filters: list = field(default_factory=list)
    mode: str = "and"

    def __call__(self, entry: FileEntry) -> bool:
        if not self.filters:
            return True
        if self.mode == "or":
            return any(f(entry) for f in self.filters)
        return all(f(entry) for f in self.filters)


@dataclass
class NameLengthFilter:
    """Filter files by stem (filename without extension) length.

    Args:
        min_length: Minimum stem length (inclusive). None means no minimum.
        max_length: Maximum stem length (inclusive). None means no maximum.
    """

    min_length: int | None = None
    max_length: int | None = None

    def __call__(self, entry: FileEntry) -> bool:
        stem_len = len(entry.path.stem) if hasattr(entry, "path") else len(entry.name)
        if self.min_length is not None and stem_len < self.min_length:
            return False
        return not (self.max_length is not None and stem_len > self.max_length)


@dataclass
class HiddenFileFilter:
    """Filter out hidden files.

    On POSIX systems, hidden files start with a dot. On Windows, the
    ``is_hidden`` key in ``entry.metadata`` is checked (populated by
    :func:`~tidyforge.metadata.fs_metadata.extract_fs_metadata`).

    Args:
        include_hidden: If True, hidden files are *not* filtered out.
    """

    include_hidden: bool = False

    def __call__(self, entry: FileEntry) -> bool:
        if self.include_hidden:
            return True
        # Check metadata first (Windows), fall back to dot-prefix (POSIX)
        if entry.metadata.get("is_hidden"):
            return False
        return not entry.name.startswith(".")
