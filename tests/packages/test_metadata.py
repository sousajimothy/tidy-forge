"""Tests for tidyforge.metadata."""

from __future__ import annotations

from pathlib import Path

from tidyforge.metadata import categorize_file, extract_fs_metadata, get_extensions_for_category


class TestFsMetadata:
    def test_extract_basic(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        meta = extract_fs_metadata(f)

        assert meta["size"] == 11
        assert "modified" in meta
        assert "created" in meta
        assert isinstance(meta["is_hidden"], bool)

    def test_hidden_dotfile(self, tmp_path: Path) -> None:
        import sys

        f = tmp_path / ".hidden"
        f.write_text("secret")
        meta = extract_fs_metadata(f)
        if sys.platform != "win32":
            # On Unix, dotfiles are hidden by convention
            assert meta["is_hidden"] is True
        else:
            # On Windows, dotfiles are NOT hidden unless the attribute is set
            assert isinstance(meta["is_hidden"], bool)


class TestCategories:
    def test_image(self) -> None:
        assert categorize_file(Path("photo.jpg")) == "image"
        assert categorize_file(Path("photo.PNG")) == "image"

    def test_video(self) -> None:
        assert categorize_file(Path("movie.mp4")) == "video"

    def test_unknown(self) -> None:
        assert categorize_file(Path("data.xyz")) == "other"

    def test_get_extensions(self) -> None:
        exts = get_extensions_for_category("image")
        assert ".jpg" in exts
        assert ".png" in exts

    def test_empty_category(self) -> None:
        exts = get_extensions_for_category("nonexistent")
        assert exts == set()
