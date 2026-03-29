"""Core file generation engine."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from tidyforge.sample_data.specs import FileSpec


def generate_files(
    target: Path,
    specs: list[FileSpec],
    *,
    clean: bool = False,
) -> list[Path]:
    """Create dummy files on disk from a list of specifications.

    Args:
        target: Root directory where files will be created.
        specs: List of :class:`FileSpec` objects describing each file.
        clean: If ``True``, remove all existing contents of *target* first.

    Returns:
        List of absolute paths to the created files.
    """
    target = Path(target).resolve()

    if clean and target.exists():
        clean_directory(target)

    target.mkdir(parents=True, exist_ok=True)

    created: list[Path] = []
    for spec in specs:
        parent = target / spec.subdir if spec.subdir else target
        parent.mkdir(parents=True, exist_ok=True)

        path = parent / spec.name
        data = spec.content if spec.content is not None else b"\x00" * spec.size
        path.write_bytes(data)

        if spec.mtime is not None:
            epoch = spec.mtime.timestamp()
            os.utime(path, (epoch, epoch))

        created.append(path)

    return created


def clean_directory(target: Path) -> None:
    """Remove all contents of *target* without removing the directory itself.

    Args:
        target: Directory whose contents should be deleted.
    """
    target = Path(target).resolve()
    if not target.is_dir():
        return

    for child in target.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
