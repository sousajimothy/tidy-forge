"""File hashing and duplicate detection."""

from __future__ import annotations

import hashlib
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from tidyforge.core.models import FileEntry

logger = logging.getLogger(__name__)


def hash_file(
    path: Path,
    algorithm: str = "sha256",
    chunk_size: int = 8192,
) -> str:
    """Compute a hex digest hash of a file.

    Args:
        path: File path.
        algorithm: Hash algorithm name (e.g. ``"sha256"``, ``"md5"``).
        chunk_size: Read buffer size in bytes.

    Returns:
        Hex digest string.
    """
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class DuplicateGroup:
    """A group of files that are exact duplicates."""

    hash: str
    size: int
    files: list[Path] = field(default_factory=list)

    @property
    def wasted_space(self) -> int:
        """Space wasted by duplicates (all copies except the first)."""
        return self.size * max(0, len(self.files) - 1)


@dataclass
class DuplicateReport:
    """Report of all duplicate groups found."""

    groups: list[DuplicateGroup] = field(default_factory=list)
    algorithm: str = "sha256"

    @property
    def total_wasted_space(self) -> int:
        return sum(g.wasted_space for g in self.groups)

    @property
    def total_duplicate_count(self) -> int:
        return sum(len(g.files) - 1 for g in self.groups)

    @property
    def total_groups(self) -> int:
        return len(self.groups)


def find_duplicates(
    entries: list[FileEntry],
    algorithm: str = "sha256",
    *,
    use_size_prefilter: bool = True,
) -> DuplicateReport:
    """Find exact duplicate files using a two-pass approach.

    Pass 1: Group files by size. Files with unique sizes cannot be duplicates.
    Pass 2: Hash files that share a size and group by hash.

    Args:
        entries: File entries to check.
        algorithm: Hash algorithm to use.
        use_size_prefilter: If True, skip hashing files with unique sizes.

    Returns:
        DuplicateReport containing all groups of duplicates.
    """
    files = [e for e in entries if not e.is_dir and e.size > 0]

    # Pass 1: size pre-filter
    if use_size_prefilter:
        by_size: dict[int, list[FileEntry]] = defaultdict(list)
        for entry in files:
            by_size[entry.size].append(entry)
        candidates = [e for group in by_size.values() if len(group) > 1 for e in group]
    else:
        candidates = files

    # Pass 2: hash
    by_hash: dict[str, list[Path]] = defaultdict(list)
    sizes: dict[str, int] = {}
    for entry in candidates:
        try:
            digest = hash_file(entry.path, algorithm=algorithm)
            by_hash[digest].append(entry.path)
            sizes[digest] = entry.size
        except OSError as exc:
            logger.warning("Cannot hash %s: %s", entry.path, exc)

    groups = [
        DuplicateGroup(hash=digest, size=sizes[digest], files=paths)
        for digest, paths in by_hash.items()
        if len(paths) > 1
    ]

    return DuplicateReport(groups=groups, algorithm=algorithm)
