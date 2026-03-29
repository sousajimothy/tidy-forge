"""Tests for tidyforge.duplicate_detection."""

from __future__ import annotations

from pathlib import Path

from tidyforge.core.models import FileEntry
from tidyforge.duplicate_detection import find_duplicates, hash_file


class TestHashFile:
    def test_sha256(self, tmp_path: Path) -> None:
        f = tmp_path / "test.bin"
        f.write_bytes(b"hello world")
        digest = hash_file(f, algorithm="sha256")
        assert len(digest) == 64  # SHA-256 hex digest length

    def test_same_content_same_hash(self, tmp_path: Path) -> None:
        content = b"identical content"
        f1 = tmp_path / "a.bin"
        f2 = tmp_path / "b.bin"
        f1.write_bytes(content)
        f2.write_bytes(content)
        assert hash_file(f1) == hash_file(f2)

    def test_different_content_different_hash(self, tmp_path: Path) -> None:
        f1 = tmp_path / "a.bin"
        f2 = tmp_path / "b.bin"
        f1.write_bytes(b"content A")
        f2.write_bytes(b"content B")
        assert hash_file(f1) != hash_file(f2)


class TestFindDuplicates:
    def test_finds_duplicates(self, tmp_tree: Path) -> None:
        entries = [FileEntry.from_path(p) for p in tmp_tree.rglob("*") if p.is_file()]
        report = find_duplicates(entries)

        # file_b.jpg and sub/file_e.jpg have identical content
        assert report.total_groups >= 1
        assert report.total_duplicate_count >= 1
        assert report.total_wasted_space > 0

    def test_no_duplicates(self, tmp_path: Path) -> None:
        (tmp_path / "a.txt").write_bytes(b"unique_a")
        (tmp_path / "b.txt").write_bytes(b"unique_b")
        entries = [FileEntry.from_path(p) for p in tmp_path.iterdir() if p.is_file()]
        report = find_duplicates(entries)
        assert report.total_groups == 0

    def test_size_prefilter(self, tmp_path: Path) -> None:
        # Different sizes -> no hash computation needed
        (tmp_path / "small.txt").write_bytes(b"a")
        (tmp_path / "big.txt").write_bytes(b"a" * 1000)
        entries = [FileEntry.from_path(p) for p in tmp_path.iterdir() if p.is_file()]
        report = find_duplicates(entries, use_size_prefilter=True)
        assert report.total_groups == 0
