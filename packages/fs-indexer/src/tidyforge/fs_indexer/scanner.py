"""Recursive directory scanner with depth control and error resilience."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Protocol, runtime_checkable

from tidyforge.core.models import FileEntry

logger = logging.getLogger(__name__)


@runtime_checkable
class FileFilter(Protocol):
    """Protocol for file filters used during scanning."""

    def __call__(self, entry: FileEntry) -> bool:
        """Return True to include the entry, False to exclude it."""
        ...


def scan_directory(
    root: Path,
    *,
    filters: list[FileFilter] | None = None,
    follow_symlinks: bool = False,
    max_depth: int | None = None,
    include_dirs: bool = False,
) -> Iterator[FileEntry]:
    """Recursively scan a directory and yield FileEntry objects.

    Args:
        root: Directory to scan.
        filters: Optional list of filter callables. An entry is yielded only
            if all filters return True.
        follow_symlinks: Whether to follow symbolic links.
        max_depth: Maximum recursion depth (None for unlimited). Depth 0 means
            only the immediate children of *root*.
        include_dirs: Whether to yield directory entries in addition to files.

    Yields:
        FileEntry for each matching file (and optionally directory).

    Raises:
        tidyforge.core.exceptions.ScanError: If *root* does not exist or is
            not a directory.
    """
    from tidyforge.core.exceptions import ScanError

    root = Path(root).resolve()
    if not root.is_dir():
        raise ScanError(f"Not a directory: {root}")

    yield from _walk(
        root,
        filters=filters or [],
        follow_symlinks=follow_symlinks,
        max_depth=max_depth,
        current_depth=0,
        include_dirs=include_dirs,
    )


def _walk(
    directory: Path,
    *,
    filters: list[FileFilter],
    follow_symlinks: bool,
    max_depth: int | None,
    current_depth: int,
    include_dirs: bool,
) -> Iterator[FileEntry]:
    """Internal recursive walker."""
    try:
        children = sorted(directory.iterdir())
    except PermissionError:
        logger.warning("Permission denied: %s", directory)
        return
    except OSError as exc:
        logger.warning("Error reading %s: %s", directory, exc)
        return

    for child in children:
        if child.is_symlink() and not follow_symlinks:
            continue

        try:
            entry = FileEntry.from_path(child)
        except OSError as exc:
            logger.warning("Cannot stat %s: %s", child, exc)
            continue

        if child.is_dir():
            if include_dirs and _passes_filters(entry, filters):
                yield entry
            if max_depth is None or current_depth < max_depth:
                yield from _walk(
                    child,
                    filters=filters,
                    follow_symlinks=follow_symlinks,
                    max_depth=max_depth,
                    current_depth=current_depth + 1,
                    include_dirs=include_dirs,
                )
        elif _passes_filters(entry, filters):
            yield entry


def _passes_filters(entry: FileEntry, filters: list[FileFilter]) -> bool:
    """Return True if the entry passes all filters."""
    return all(f(entry) for f in filters)
