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
    append_folder_name,
    auto_date,
    change_case,
    change_extension,
    change_name,
    insert_at,
    regex_replace,
    remove_chars,
    replace_text,
    sanitize_filename,
    sequential_name,
    strip_text,
    word_space,
)


def _make_entry(tmp_path: Path, name: str, content: bytes = b"data") -> FileEntry:
    p = tmp_path / name
    p.write_bytes(content)
    return FileEntry.from_path(p)


def _make_entry_in(directory: Path, name: str) -> FileEntry:
    """Create a file inside *directory* (which must already exist)."""
    p = directory / name
    p.write_bytes(b"data")
    return FileEntry.from_path(p)


# ── RenamePlan ────────────────────────────────────────────────────────────


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


# ── Original operations ───────────────────────────────────────────────────


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


# ── replace_text extensions ───────────────────────────────────────────────


class TestReplaceTextExtensions:
    def test_first_only(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "aa_bb_aa.txt")]
        plan = replace_text(entries, "aa", "XX", first_only=True)
        assert plan.actions[0].destination.name == "XX_bb_aa.txt"

    def test_first_only_case_insensitive(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "AA_bb_AA.txt")]
        plan = replace_text(entries, "aa", "XX", case_sensitive=False, first_only=True)
        assert plan.actions[0].destination.name == "XX_bb_AA.txt"

    def test_replace_all_default(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "aa_bb_aa.txt")]
        plan = replace_text(entries, "aa", "XX")
        assert plan.actions[0].destination.name == "XX_bb_XX.txt"


# ── regex_replace extensions ──────────────────────────────────────────────


class TestRegexReplaceExtensions:
    def test_stem_only(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "IMG_photo.jpg")]
        plan = regex_replace(entries, r"\.jpg", "_X", include_ext=False)
        # Pattern matches extension text but stem_only means only stem is searched
        assert len(plan.actions) == 0

    def test_include_ext_default(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.JPG")]
        plan = regex_replace(entries, r"\.JPG", ".jpg")
        assert plan.actions[0].destination.name == "photo.jpg"

    def test_stem_only_matches_stem(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "IMG_001.jpg")]
        plan = regex_replace(entries, r"IMG", "PHOTO", include_ext=False)
        assert plan.actions[0].destination.name == "PHOTO_001.jpg"


# ── change_case ───────────────────────────────────────────────────────────


class TestChangeCase:
    def test_lower(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "PHOTO.jpg")]
        plan = change_case(entries, "lower", scope="stem")
        assert plan.actions[0].destination.name == "photo.jpg"

    def test_upper(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = change_case(entries, "upper", scope="stem")
        assert plan.actions[0].destination.name == "PHOTO.jpg"

    def test_title(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "hello world.txt")]
        plan = change_case(entries, "title", scope="stem")
        assert plan.actions[0].destination.name == "Hello World.txt"

    def test_sentence(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "hELLO WORLD.txt")]
        plan = change_case(entries, "sentence", scope="stem")
        assert plan.actions[0].destination.name == "Hello world.txt"

    def test_ext_only(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.JPG")]
        plan = change_case(entries, "lower", scope="ext")
        assert plan.actions[0].destination.name == "photo.jpg"

    def test_both(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "PHOTO.JPG")]
        plan = change_case(entries, "lower", scope="both")
        assert plan.actions[0].destination.name == "photo.jpg"

    def test_no_change(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = change_case(entries, "lower", scope="stem")
        assert len(plan.actions) == 0


# ── change_extension ──────────────────────────────────────────────────────


class TestChangeExtension:
    def test_lower(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.JPG")]
        plan = change_extension(entries, "lower")
        assert plan.actions[0].destination.name == "photo.jpg"

    def test_upper(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = change_extension(entries, "upper")
        assert plan.actions[0].destination.name == "photo.JPG"

    def test_no_change(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = change_extension(entries, "lower")
        assert len(plan.actions) == 0

    def test_fixed(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = change_extension(entries, "fixed", new_ext=".bak")
        assert plan.actions[0].destination.name == "photo.bak"

    def test_extra(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = change_extension(entries, "extra", new_ext=".bak")
        assert plan.actions[0].destination.name == "photo.jpg.bak"

    def test_remove(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = change_extension(entries, "remove")
        assert plan.actions[0].destination.name == "photo"

    def test_title(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = change_extension(entries, "title")
        assert plan.actions[0].destination.name == "photo.Jpg"


# ── remove_chars ──────────────────────────────────────────────────────────


class TestRemoveChars:
    def test_first_n(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "Screenshot_001.png")]
        plan = remove_chars(entries, first_n=11)
        assert plan.actions[0].destination.name == "001.png"

    def test_last_n(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo_edited.jpg")]
        plan = remove_chars(entries, last_n=7)
        assert plan.actions[0].destination.name == "photo.jpg"

    def test_from_to(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "abcdefgh.txt")]
        plan = remove_chars(entries, from_pos=2, to_pos=5)
        assert plan.actions[0].destination.name == "abfgh.txt"

    def test_crop_before(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "prefix_keepme.txt")]
        plan = remove_chars(entries, crop_before="prefix_")
        assert plan.actions[0].destination.name == "keepme.txt"

    def test_crop_after(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "keepme_suffix.txt")]
        plan = remove_chars(entries, crop_after="_suffix")
        assert plan.actions[0].destination.name == "keepme.txt"

    def test_preserves_extension(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "abc.jpg")]
        plan = remove_chars(entries, first_n=1)
        assert plan.actions[0].destination.name == "bc.jpg"

    def test_overcrop_clamps(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "ab.txt")]
        plan = remove_chars(entries, first_n=100)
        # Stem becomes empty -> skipped
        assert len(plan.actions) == 0

    def test_crop_before_not_found(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = remove_chars(entries, crop_before="NOTFOUND")
        assert len(plan.actions) == 0


# ── insert_at ─────────────────────────────────────────────────────────────


class TestInsertAt:
    def test_at_start(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = insert_at(entries, "2024_", 0)
        assert plan.actions[0].destination.name == "2024_photo.jpg"

    def test_at_middle(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = insert_at(entries, "_X_", 3)
        assert plan.actions[0].destination.name == "pho_X_to.jpg"

    def test_at_end(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = insert_at(entries, "_end", 100)
        assert plan.actions[0].destination.name == "photo_end.jpg"

    def test_negative(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = insert_at(entries, "_X", -2)
        assert plan.actions[0].destination.name == "pho_Xto.jpg"


# ── auto_date ─────────────────────────────────────────────────────────────


class TestAutoDate:
    def test_prefix_modified(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = auto_date(entries, fmt="%Y-%m-%d")
        # We can't know the exact date but the name should start with a date
        dest = plan.actions[0].destination.name
        assert dest.endswith("_photo.jpg")
        assert len(dest) > len("photo.jpg")

    def test_suffix(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = auto_date(entries, position="suffix", separator="-")
        dest = plan.actions[0].destination.name
        assert dest.startswith("photo-")

    def test_custom_format(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = auto_date(entries, fmt="%Y%m%d")
        dest = plan.actions[0].destination.name
        # Should be like "20260329_photo.jpg"
        parts = dest.split("_")
        assert len(parts[0]) == 8  # YYYYMMDD

    def test_created_fallback(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = auto_date(entries, date_source="created", fmt="%Y")
        # Falls back to modified since metadata not populated
        assert len(plan.actions) == 1


# ── append_folder_name ────────────────────────────────────────────────────


class TestAppendFolderName:
    def test_prefix_one_level(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = append_folder_name(entries, position="prefix")
        dest = plan.actions[0].destination.name
        assert dest == f"{tmp_path.name}_photo.jpg"

    def test_suffix_one_level(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = append_folder_name(entries, position="suffix")
        dest = plan.actions[0].destination.name
        assert dest == f"photo_{tmp_path.name}.jpg"

    def test_multi_level(self, tmp_path: Path) -> None:
        sub = tmp_path / "a" / "b"
        sub.mkdir(parents=True)
        entries = [_make_entry_in(sub, "photo.jpg")]
        plan = append_folder_name(entries, levels=2)
        dest = plan.actions[0].destination.name
        assert dest == "a_b_photo.jpg"

    def test_custom_separator(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = append_folder_name(entries, separator="-")
        dest = plan.actions[0].destination.name
        assert dest == f"{tmp_path.name}-photo.jpg"


# ── sequential_name enhancements ─────────────────────────────────────────


class TestSequentialNameEnhanced:
    def test_increment(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "a.txt"), _make_entry(tmp_path, "b.txt")]
        plan = sequential_name(entries, start=1, increment=2)
        assert plan.actions[0].destination.name == "001.txt"
        assert plan.actions[1].destination.name == "003.txt"

    def test_hex_base(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, f"{chr(97 + i)}.txt") for i in range(11)]
        plan = sequential_name(entries, start=0, base=16, pad=2)
        assert plan.actions[10].destination.name == "0a.txt"

    def test_prefix_position(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = sequential_name(entries, position="prefix", separator="_")
        assert plan.actions[0].destination.name == "001_photo.jpg"

    def test_suffix_position(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = sequential_name(entries, position="suffix", separator="_")
        assert plan.actions[0].destination.name == "photo_001.jpg"

    def test_reset_per_folder(self, tmp_path: Path) -> None:
        d1 = tmp_path / "dir1"
        d2 = tmp_path / "dir2"
        d1.mkdir()
        d2.mkdir()
        entries = [
            _make_entry_in(d1, "a.txt"),
            _make_entry_in(d1, "b.txt"),
            _make_entry_in(d2, "c.txt"),
        ]
        plan = sequential_name(entries, reset_per_folder=True)
        assert plan.actions[0].destination.name == "001.txt"
        assert plan.actions[1].destination.name == "002.txt"
        assert plan.actions[2].destination.name == "001.txt"  # reset!


# ── change_name ───────────────────────────────────────────────────────────


class TestChangeName:
    def test_fixed(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = change_name(entries, "fixed", fixed_name="image")
        assert plan.actions[0].destination.name == "image.jpg"

    def test_reverse(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "abc.txt")]
        plan = change_name(entries, "reverse")
        assert plan.actions[0].destination.name == "cba.txt"

    def test_remove(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = change_name(entries, "remove")
        # Empty stem + ext = ".jpg" only -> skipped because empty stem
        assert len(plan.actions) == 0

    def test_fixed_no_change(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = change_name(entries, "fixed", fixed_name="photo")
        assert len(plan.actions) == 0


# ── word_space ────────────────────────────────────────────────────────────


class TestWordSpace:
    def test_camel_case(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "MyFileName.txt")]
        plan = word_space(entries)
        assert plan.actions[0].destination.name == "My File Name.txt"

    def test_underscores(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "my_file_name.txt")]
        plan = word_space(entries)
        assert plan.actions[0].destination.name == "my file name.txt"

    def test_hyphens(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "my-file-name.txt")]
        plan = word_space(entries)
        assert plan.actions[0].destination.name == "my file name.txt"

    def test_custom_separator(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "MyFileName.txt")]
        plan = word_space(entries, separator="-")
        assert plan.actions[0].destination.name == "My-File-Name.txt"

    def test_no_change(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = word_space(entries)
        assert len(plan.actions) == 0


# ── strip_text (existing) ────────────────────────────────────────────────


class TestStripText:
    def test_strip_prefix(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "Screenshot_20260329_094302_Reddit.png")]
        plan = strip_text(entries, "Screenshot_", position="prefix")
        assert plan.actions[0].destination.name == "20260329_094302_Reddit.png"

    def test_strip_prefix_no_match(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "IMG_001.jpg")]
        plan = strip_text(entries, "Screenshot_", position="prefix")
        assert len(plan.actions) == 0

    def test_strip_suffix(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo_edited.jpg")]
        plan = strip_text(entries, "_edited", position="suffix")
        assert plan.actions[0].destination.name == "photo.jpg"

    def test_strip_suffix_no_match(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "photo.jpg")]
        plan = strip_text(entries, "_edited", position="suffix")
        assert len(plan.actions) == 0

    def test_strip_any(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "IMG-20260329-photo.jpg")]
        plan = strip_text(entries, "IMG-", position="any")
        assert plan.actions[0].destination.name == "20260329-photo.jpg"

    def test_strip_any_multiple(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "aa_bb_aa.txt")]
        plan = strip_text(entries, "aa", position="any")
        assert plan.actions[0].destination.name == "_bb_.txt"

    def test_strip_case_insensitive(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "SCREENSHOT_001.png")]
        plan = strip_text(entries, "screenshot_", position="prefix", case_sensitive=False)
        assert plan.actions[0].destination.name == "001.png"

    def test_strip_case_sensitive_no_match(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "SCREENSHOT_001.png")]
        plan = strip_text(entries, "screenshot_", position="prefix", case_sensitive=True)
        assert len(plan.actions) == 0

    def test_strip_skips_dirs(self, tmp_path: Path) -> None:
        d = tmp_path / "Screenshot_subdir"
        d.mkdir()
        entry = FileEntry.from_path(d)
        plan = strip_text([entry], "Screenshot_", position="prefix")
        assert len(plan.actions) == 0

    def test_strip_skips_empty_result(self, tmp_path: Path) -> None:
        entries = [_make_entry(tmp_path, "abc.txt")]
        plan = strip_text(entries, "abc.txt", position="any")
        assert len(plan.actions) == 0


# ── TemplateRenderer ──────────────────────────────────────────────────────


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


# ── SanitizeFilename ──────────────────────────────────────────────────────


class TestSanitizeFilename:
    def test_removes_unsafe(self) -> None:
        assert sanitize_filename('file<>:"/\\|?*.txt') == "file_________.txt"

    def test_strips_dots_spaces(self) -> None:
        assert sanitize_filename("...file...") == "file"

    def test_empty_becomes_unnamed(self) -> None:
        assert sanitize_filename("...") == "unnamed"
