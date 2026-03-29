"""Tests for tidyforge.rename_engine."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from tidyforge.core.models import FileEntry
from tidyforge.rename_engine import (
    RenameAction,
    RenamePlan,
    TemplateRenderer,
    add_prefix,
    add_suffix,
    regex_replace,
    replace_text,
    sanitize_filename,
    sequential_name,
)


def _make_entry(tmp_path: Path, name: str, content: bytes = b"data") -> FileEntry:
    p = tmp_path / name
    p.write_bytes(content)
    return FileEntry.from_path(p)


class TestRenamePlan:
    def test_detect_collisions(self, tmp_path: Path) -> None:
        plan = RenamePlan(
            actions=[
                RenameAction(source=tmp_path / "a.txt", destination=tmp_path / "target.txt"),
                RenameAction(source=tmp_path / "b.txt", destination=tmp_path / "target.txt"),
            ]
        )
        collisions = plan.detect_collisions()
        assert len(collisions) == 1
        assert "Collision" in collisions[0]

    def test_detect_overwrites(self, tmp_path: Path) -> None:
        existing = tmp_path / "existing.txt"
        existing.write_text("original")
        plan = RenamePlan(
            actions=[
                RenameAction(source=tmp_path / "new.txt", destination=existing),
            ]
        )
        warnings = plan.detect_overwrites()
        assert len(warnings) == 1

    def test_validate_noop(self, tmp_path: Path) -> None:
        f = tmp_path / "same.txt"
        f.write_text("x")
        plan = RenamePlan(
            actions=[
                RenameAction(source=f, destination=f),
            ]
        )
        issues = plan.validate()
        assert any("No-op" in i for i in issues)

    def test_preview(self, tmp_path: Path) -> None:
        plan = RenamePlan(
            actions=[
                RenameAction(source=tmp_path / "old.txt", destination=tmp_path / "new.txt"),
            ]
        )
        preview = plan.preview()
        assert preview == [("old.txt", "new.txt")]

    def test_execute_dry_run(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("content")
        plan = RenamePlan(
            actions=[
                RenameAction(source=f, destination=tmp_path / "renamed.txt"),
            ]
        )
        manifest = plan.execute(dry_run=True)
        assert manifest.dry_run is True
        assert manifest.success_count == 1
        assert f.exists()  # File NOT actually renamed

    def test_execute_real(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("content")
        dest = tmp_path / "renamed.txt"
        plan = RenamePlan(
            actions=[
                RenameAction(source=f, destination=dest),
            ]
        )
        manifest = plan.execute(dry_run=False)
        assert manifest.dry_run is False
        assert manifest.success_count == 1
        assert not f.exists()
        assert dest.exists()


class TestOperations:
    def test_add_prefix(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = add_prefix(entries, "2024_")
        assert plan.actions[0].destination.name == "2024_photo.jpg"

    def test_add_suffix(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = add_suffix(entries, "_backup")
        assert plan.actions[0].destination.name == "photo_backup.jpg"

    def test_replace_text(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "IMG_001.jpg")]
        plan = replace_text(entries, "IMG", "PHOTO")
        assert plan.actions[0].destination.name == "PHOTO_001.jpg"

    def test_replace_no_match(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = replace_text(entries, "XYZ", "ABC")
        assert len(plan.actions) == 0  # No rename needed

    def test_regex_replace(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "IMG_20240315_001.jpg")]
        plan = regex_replace(entries, r"IMG_(\d{8})_(\d+)", r"\1-\2")
        assert plan.actions[0].destination.name == "20240315-001.jpg"

    def test_sequential_name(self, tmp_path: Path) -> None:
        entries = [
            _make_entry(tmp_path, "a.txt"),
            _make_entry(tmp_path, "b.txt"),
        ]
        plan = sequential_name(entries)
        assert plan.actions[0].destination.name == "001.txt"
        assert plan.actions[1].destination.name == "002.txt"


class TestTemplateRenderer:
    def test_basic(self) -> None:
        renderer = TemplateRenderer("{name}_{counter}{ext}")
        entry = FileEntry(
            path=Path("/x/photo.jpg"),
            name="photo.jpg",
            suffix=".jpg",
            size=100,
            modified=datetime(2024, 3, 15, tzinfo=UTC),
        )
        result = renderer.render(entry, counter=5)
        assert result == "photo_005.jpg"

    def test_date_template(self) -> None:
        renderer = TemplateRenderer("{date}_{name}{ext}")
        entry = FileEntry(
            path=Path("/x/sunset.png"),
            name="sunset.png",
            suffix=".png",
            size=100,
            modified=datetime(2024, 7, 4, tzinfo=UTC),
        )
        result = renderer.render(entry, counter=1)
        assert result == "2024-07-04_sunset.png"


class TestSanitizeFilename:
    def test_removes_unsafe(self) -> None:
        assert sanitize_filename('file<>:"/\\|?*.txt') == "file_________.txt"

    def test_strips_dots_spaces(self) -> None:
        assert sanitize_filename("...file...") == "file"

    def test_empty_becomes_unnamed(self) -> None:
        assert sanitize_filename("...") == "unnamed"
