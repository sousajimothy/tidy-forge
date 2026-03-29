"""Filesystem metadata extraction (cross-platform)."""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def extract_fs_metadata(path: Path) -> dict[str, Any]:
    """Extract filesystem metadata from a path.

    Returns a dict with keys: size, modified, accessed, created, is_readonly,
    is_hidden, owner (POSIX only).

    Args:
        path: File or directory path.
    """
    path = Path(path)
    stat = path.stat()

    result: dict[str, Any] = {
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime, tz=UTC),
        "accessed": datetime.fromtimestamp(stat.st_atime, tz=UTC),
        "is_readonly": not os.access(path, os.W_OK),
    }

    # Creation time: st_birthtime on macOS, st_ctime on Windows (creation),
    # st_ctime on Linux (inode change, not true creation).
    if hasattr(stat, "st_birthtime"):
        result["created"] = datetime.fromtimestamp(stat.st_birthtime, tz=UTC)
    else:
        result["created"] = datetime.fromtimestamp(stat.st_ctime, tz=UTC)

    # Hidden file detection
    if sys.platform == "win32":
        try:
            import ctypes

            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))  # type: ignore[union-attr]
            result["is_hidden"] = bool(attrs & 0x2) if attrs != -1 else False
        except (AttributeError, OSError):
            result["is_hidden"] = path.name.startswith(".")
    else:
        result["is_hidden"] = path.name.startswith(".")

    return result
