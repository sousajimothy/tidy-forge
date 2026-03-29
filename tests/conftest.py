"""Shared test fixtures for TidyForge."""

from __future__ import annotations

from pathlib import Path

import pytest

from tidyforge.core.models import FileEntry

FIXTURES_DIR = Path(__file__).parent.parent / "data" / "fixtures" / "sample_tree"


@pytest.fixture
def sample_tree() -> Path:
    """Path to the static sample_tree fixture directory."""
    assert FIXTURES_DIR.is_dir(), f"Fixture directory missing: {FIXTURES_DIR}"
    return FIXTURES_DIR


@pytest.fixture
def tmp_tree(tmp_path: Path) -> Path:
    """Create a temporary directory tree for testing.

    Structure:
        tmp_path/
            file_a.txt (100 bytes)
            file_b.jpg (200 bytes)
            file_c.png (150 bytes)
            sub/
                file_d.txt (50 bytes)
                file_e.jpg (200 bytes)  # same size as file_b, for duplicate tests
    """
    (tmp_path / "file_a.txt").write_bytes(b"a" * 100)
    (tmp_path / "file_b.jpg").write_bytes(b"b" * 200)
    (tmp_path / "file_c.png").write_bytes(b"c" * 150)

    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "file_d.txt").write_bytes(b"d" * 50)
    (sub / "file_e.jpg").write_bytes(b"b" * 200)  # same content as file_b.jpg

    return tmp_path


@pytest.fixture
def sample_entries(tmp_tree: Path) -> list[FileEntry]:
    """List of FileEntry objects from the tmp_tree fixture."""
    entries = []
    for p in sorted(tmp_tree.rglob("*")):
        if p.is_file():
            entries.append(FileEntry.from_path(p))
    return entries


def make_files(directory: Path, spec: dict[str, int]) -> list[Path]:
    """Create files in a directory from a spec dict.

    Args:
        directory: Target directory (must exist).
        spec: Mapping of filename to size in bytes.

    Returns:
        List of created file paths.
    """
    paths = []
    for name, size in spec.items():
        p = directory / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"\x00" * size)
        paths.append(p)
    return paths
