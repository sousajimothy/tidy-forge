"""Tests for tidyforge.fs_indexer."""

from __future__ import annotations

from pathlib import Path

import pytest

from tidyforge.core.exceptions import ScanError
from tidyforge.core.models import FileEntry
from tidyforge.fs_indexer import (
    ExtensionFilter,
    PatternFilter,
    SizeFilter,
    aggregate_by_extension,
    scan_directory,
    top_n,
)


class TestScanDirectory:
    def test_scan_basic(self, tmp_tree: Path) -> None:
        entries = list(scan_directory(tmp_tree))
        names = {e.name for e in entries}
        assert "file_a.txt" in names
        assert "file_b.jpg" in names
        assert "file_d.txt" in names  # in sub/

    def test_scan_max_depth_zero(self, tmp_tree: Path) -> None:
        entries = list(scan_directory(tmp_tree, max_depth=0))
        names = {e.name for e in entries}
        assert "file_a.txt" in names
        assert "file_d.txt" not in names  # sub/ is depth 1

    def test_scan_with_filter(self, tmp_tree: Path) -> None:
        entries = list(scan_directory(tmp_tree, filters=[ExtensionFilter(include={".txt"})]))
        assert all(e.suffix == ".txt" for e in entries)
        assert len(entries) == 2

    def test_scan_nonexistent(self, tmp_path: Path) -> None:
        with pytest.raises(ScanError):
            list(scan_directory(tmp_path / "nonexistent"))

    def test_scan_include_dirs(self, tmp_tree: Path) -> None:
        entries = list(scan_directory(tmp_tree, include_dirs=True))
        has_dir = any(e.is_dir for e in entries)
        assert has_dir


class TestFilters:
    def test_extension_include(self, sample_entries: list[FileEntry]) -> None:
        f = ExtensionFilter(include={".txt"})
        result = [e for e in sample_entries if f(e)]
        assert all(e.suffix == ".txt" for e in result)

    def test_extension_exclude(self, sample_entries: list[FileEntry]) -> None:
        f = ExtensionFilter(exclude={".txt"})
        result = [e for e in sample_entries if f(e)]
        assert all(e.suffix != ".txt" for e in result)

    def test_size_filter(self, sample_entries: list[FileEntry]) -> None:
        f = SizeFilter(min_size=100, max_size=200)
        result = [e for e in sample_entries if f(e)]
        assert all(100 <= e.size <= 200 for e in result)

    def test_pattern_filter(self, sample_entries: list[FileEntry]) -> None:
        f = PatternFilter(pattern=r"file_[ab]")
        result = [e for e in sample_entries if f(e)]
        assert len(result) == 2

    def test_pattern_invert(self, sample_entries: list[FileEntry]) -> None:
        f = PatternFilter(pattern=r"\.txt$", invert=True)
        result = [e for e in sample_entries if f(e)]
        assert all(not e.name.endswith(".txt") for e in result)


class TestAggregator:
    def test_aggregate_by_extension(self, sample_entries: list[FileEntry]) -> None:
        stats = aggregate_by_extension(sample_entries)
        assert ".txt" in stats
        assert ".jpg" in stats
        assert stats[".txt"].count == 2

    def test_top_n(self, sample_entries: list[FileEntry]) -> None:
        top = top_n(sample_entries, n=2, key="size")
        assert len(top) == 2
        assert top[0].size >= top[1].size

    def test_top_n_by_name(self, sample_entries: list[FileEntry]) -> None:
        top = top_n(sample_entries, n=3, key="name", reverse=False)
        assert len(top) <= 3
