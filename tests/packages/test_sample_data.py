"""Tests for the sample-data generator package."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tidyforge.core.models import FileEntry
from tidyforge.fs_indexer import scan_directory
from tidyforge.sample_data import (
    JPEG_MAGIC,
    PNG_MAGIC,
    FileSpec,
    clean_directory,
    create_rename_playground_samples,
    generate_files,
    rename_playground_specs,
)


class TestFileSpec:
    def test_defaults(self) -> None:
        spec = FileSpec(name="test.txt")
        assert spec.size == 8
        assert spec.content is None
        assert spec.mtime is None
        assert spec.subdir is None

    def test_all_fields(self) -> None:
        dt = datetime(2024, 1, 1, tzinfo=UTC)
        spec = FileSpec(name="a.jpg", size=16, content=b"abc", mtime=dt, subdir="sub")
        assert spec.name == "a.jpg"
        assert spec.content == b"abc"
        assert spec.mtime == dt
        assert spec.subdir == "sub"


class TestGenerateFiles:
    def test_creates_files(self, tmp_path: Path) -> None:
        specs = [FileSpec(name="a.txt"), FileSpec(name="b.jpg")]
        paths = generate_files(tmp_path, specs)
        assert len(paths) == 2
        assert all(p.exists() for p in paths)
        assert {p.name for p in paths} == {"a.txt", "b.jpg"}

    def test_writes_zero_bytes_by_default(self, tmp_path: Path) -> None:
        paths = generate_files(tmp_path, [FileSpec(name="f.bin", size=16)])
        assert paths[0].read_bytes() == b"\x00" * 16

    def test_writes_content_when_provided(self, tmp_path: Path) -> None:
        paths = generate_files(tmp_path, [FileSpec(name="f.jpg", content=JPEG_MAGIC)])
        assert paths[0].read_bytes() == JPEG_MAGIC

    def test_content_overrides_size(self, tmp_path: Path) -> None:
        paths = generate_files(tmp_path, [FileSpec(name="f.png", size=999, content=PNG_MAGIC)])
        assert len(paths[0].read_bytes()) == len(PNG_MAGIC)

    def test_sets_mtime(self, tmp_path: Path) -> None:
        dt = datetime(2023, 6, 15, 12, 0, 0, tzinfo=UTC)
        paths = generate_files(tmp_path, [FileSpec(name="f.txt", mtime=dt)])
        actual_mtime = os.path.getmtime(paths[0])
        assert abs(actual_mtime - dt.timestamp()) < 2  # 2s tolerance for filesystem

    def test_creates_subdirectories(self, tmp_path: Path) -> None:
        specs = [
            FileSpec(name="a.jpg", subdir="Vacation"),
            FileSpec(name="b.jpg", subdir="Food"),
        ]
        paths = generate_files(tmp_path, specs)
        assert (tmp_path / "Vacation" / "a.jpg").exists()
        assert (tmp_path / "Food" / "b.jpg").exists()
        assert len(paths) == 2

    def test_creates_target_if_missing(self, tmp_path: Path) -> None:
        target = tmp_path / "new" / "nested" / "dir"
        generate_files(target, [FileSpec(name="f.txt")])
        assert (target / "f.txt").exists()

    def test_clean_removes_old_files(self, tmp_path: Path) -> None:
        # Create an initial file
        (tmp_path / "old.txt").write_bytes(b"old")

        # Generate with clean=True should remove old.txt
        generate_files(tmp_path, [FileSpec(name="new.txt")], clean=True)
        assert not (tmp_path / "old.txt").exists()
        assert (tmp_path / "new.txt").exists()

    def test_no_clean_preserves_old_files(self, tmp_path: Path) -> None:
        (tmp_path / "old.txt").write_bytes(b"old")
        generate_files(tmp_path, [FileSpec(name="new.txt")], clean=False)
        assert (tmp_path / "old.txt").exists()
        assert (tmp_path / "new.txt").exists()


class TestCleanDirectory:
    def test_removes_files_and_dirs(self, tmp_path: Path) -> None:
        (tmp_path / "file.txt").write_bytes(b"x")
        sub = tmp_path / "subdir"
        sub.mkdir()
        (sub / "nested.txt").write_bytes(b"x")

        clean_directory(tmp_path)

        assert tmp_path.exists()  # directory itself preserved
        assert list(tmp_path.iterdir()) == []  # contents removed

    def test_noop_on_missing_dir(self, tmp_path: Path) -> None:
        missing = tmp_path / "does_not_exist"
        clean_directory(missing)  # should not raise

    def test_noop_on_empty_dir(self, tmp_path: Path) -> None:
        clean_directory(tmp_path)
        assert tmp_path.exists()


class TestRenamePlaygroundPreset:
    def test_specs_count(self) -> None:
        specs = rename_playground_specs()
        assert len(specs) >= 35  # ~40 files expected

    def test_specs_have_unique_paths(self) -> None:
        """Each (subdir, name) pair should be unique."""
        specs = rename_playground_specs()
        keys = [(s.subdir, s.name) for s in specs]
        assert len(keys) == len(set(keys))

    def test_specs_cover_subdirs(self) -> None:
        specs = rename_playground_specs()
        subdirs = {s.subdir for s in specs if s.subdir}
        assert len(subdirs) >= 2  # at least Vacation and Food

    def test_specs_cover_mtimes(self) -> None:
        specs = rename_playground_specs()
        with_mtime = [s for s in specs if s.mtime is not None]
        assert len(with_mtime) >= 4  # several files need meaningful dates

    def test_create_convenience(self, tmp_path: Path) -> None:
        paths = create_rename_playground_samples(tmp_path)
        assert len(paths) == len(rename_playground_specs())
        assert all(p.exists() for p in paths)

    def test_scannable_by_fs_indexer(self, tmp_path: Path) -> None:
        """Generated files should be discoverable via scan_directory."""
        create_rename_playground_samples(tmp_path)
        entries = list(scan_directory(tmp_path, max_depth=1))
        assert len(entries) >= 35

    def test_usable_with_rename_operations(self, tmp_path: Path) -> None:
        """Generated files can be passed through rename operations."""
        from tidyforge.rename_engine import change_case, replace_text

        create_rename_playground_samples(tmp_path)
        entries = [FileEntry.from_path(p) for p in sorted(tmp_path.rglob("*")) if p.is_file()]

        # replace_text should find IMG_ files
        plan = replace_text(entries, old="IMG", new="PHOTO")
        assert len(plan.actions) > 0

        # change_case should produce actions for mixed-case files
        plan = change_case(entries, case="lower", scope="stem")
        assert len(plan.actions) > 0


class TestFuturePresetStubs:
    """Ensure stubs raise NotImplementedError with helpful messages."""

    def test_rename_strip_specs(self) -> None:
        from tidyforge.sample_data.presets import rename_strip_specs

        with pytest.raises(NotImplementedError, match="future phase"):
            rename_strip_specs()

    def test_organize_playground_specs(self) -> None:
        from tidyforge.sample_data.presets import organize_playground_specs

        with pytest.raises(NotImplementedError, match="future phase"):
            organize_playground_specs()

    def test_organize_by_app_specs(self) -> None:
        from tidyforge.sample_data.presets import organize_by_app_specs

        with pytest.raises(NotImplementedError, match="future phase"):
            organize_by_app_specs()

    def test_scanning_and_filtering_specs(self) -> None:
        from tidyforge.sample_data.presets import scanning_and_filtering_specs

        with pytest.raises(NotImplementedError, match="future phase"):
            scanning_and_filtering_specs()
