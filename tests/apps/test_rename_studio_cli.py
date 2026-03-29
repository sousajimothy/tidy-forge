"""CLI smoke tests for rename-studio."""

from __future__ import annotations

from typer.testing import CliRunner

from rename_studio.cli import app

runner = CliRunner()


class TestRenameStudioCLI:
    def test_help(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "rename" in result.output.lower()

    def test_preview_help(self) -> None:
        result = runner.invoke(app, ["preview", "--help"])
        assert result.exit_code == 0

    def test_preview_nonexistent(self, tmp_path) -> None:
        result = runner.invoke(app, ["preview", str(tmp_path / "nope")])
        assert result.exit_code != 0

    def test_preview_with_files(self, tmp_tree) -> None:
        result = runner.invoke(app, ["preview", str(tmp_tree), "--template", "{name}_copy{ext}"])
        assert result.exit_code == 0

    def test_prefix(self, tmp_tree) -> None:
        result = runner.invoke(app, ["prefix", str(tmp_tree), "--prefix", "test_"])
        assert result.exit_code == 0
        assert "dry-run" in result.output.lower() or "Dry-run" in result.output


class TestStripCLI:
    """Tests for the strip command."""

    def test_strip_help(self) -> None:
        result = runner.invoke(app, ["strip", "--help"])
        assert result.exit_code == 0
        assert "strip" in result.output.lower()

    def test_strip_nonexistent(self, tmp_path) -> None:
        result = runner.invoke(
            app, ["strip", str(tmp_path / "nope"), "--text", "foo"],
        )
        assert result.exit_code != 0

    def test_strip_prefix_dryrun(self, tmp_path) -> None:
        (tmp_path / "Screenshot_001.png").write_bytes(b"x")
        (tmp_path / "Screenshot_002.png").write_bytes(b"x")
        (tmp_path / "IMG_003.jpg").write_bytes(b"x")

        result = runner.invoke(
            app,
            ["strip", str(tmp_path), "--text", "Screenshot_", "--position", "prefix"],
        )
        assert result.exit_code == 0
        assert "001.png" in result.output
        assert "002.png" in result.output
        assert "Dry-run" in result.output

    def test_strip_prefix_execute(self, tmp_path) -> None:
        (tmp_path / "Screenshot_001.png").write_bytes(b"x")

        result = runner.invoke(
            app,
            [
                "strip", str(tmp_path),
                "--text", "Screenshot_",
                "--position", "prefix",
                "--execute",
            ],
        )
        assert result.exit_code == 0
        assert (tmp_path / "001.png").exists()
        assert not (tmp_path / "Screenshot_001.png").exists()

    def test_strip_any_dryrun(self, tmp_path) -> None:
        (tmp_path / "IMG-20260329-photo.jpg").write_bytes(b"x")

        result = runner.invoke(
            app,
            ["strip", str(tmp_path), "--text", "IMG-"],
        )
        assert result.exit_code == 0
        assert "20260329-photo.jpg" in result.output

    def test_strip_suffix_dryrun(self, tmp_path) -> None:
        (tmp_path / "photo_edited.jpg").write_bytes(b"x")

        result = runner.invoke(
            app,
            ["strip", str(tmp_path), "--text", "_edited", "--position", "suffix"],
        )
        assert result.exit_code == 0
        assert "photo.jpg" in result.output

    def test_strip_case_insensitive(self, tmp_path) -> None:
        (tmp_path / "SCREENSHOT_001.png").write_bytes(b"x")

        result = runner.invoke(
            app,
            [
                "strip", str(tmp_path),
                "--text", "screenshot_",
                "--position", "prefix",
                "--ignore-case",
            ],
        )
        assert result.exit_code == 0
        assert "001.png" in result.output

    def test_strip_no_matches(self, tmp_path) -> None:
        (tmp_path / "photo.jpg").write_bytes(b"x")

        result = runner.invoke(
            app,
            ["strip", str(tmp_path), "--text", "Screenshot_", "--position", "prefix"],
        )
        assert result.exit_code == 0
        assert "No files to rename" in result.output


class TestCaseCLI:
    def test_case_help(self) -> None:
        result = runner.invoke(app, ["case", "--help"])
        assert result.exit_code == 0

    def test_case_lower(self, tmp_path) -> None:
        (tmp_path / "PHOTO.JPG").write_bytes(b"x")
        result = runner.invoke(app, ["case", str(tmp_path), "--case", "lower"])
        assert result.exit_code == 0
        assert "photo" in result.output

    def test_case_execute(self, tmp_path) -> None:
        (tmp_path / "PHOTO.JPG").write_bytes(b"x")
        result = runner.invoke(
            app, ["case", str(tmp_path), "--case", "lower", "--execute"],
        )
        assert result.exit_code == 0
        assert (tmp_path / "photo.JPG").exists()


class TestExtensionCLI:
    def test_extension_help(self) -> None:
        result = runner.invoke(app, ["extension", "--help"])
        assert result.exit_code == 0

    def test_extension_lower(self, tmp_path) -> None:
        (tmp_path / "photo.JPG").write_bytes(b"x")
        result = runner.invoke(app, ["extension", str(tmp_path), "--mode", "lower"])
        assert result.exit_code == 0
        assert "photo.jpg" in result.output

    def test_extension_fixed(self, tmp_path) -> None:
        (tmp_path / "photo.jpg").write_bytes(b"x")
        result = runner.invoke(
            app,
            ["extension", str(tmp_path), "--mode", "fixed", "--ext", ".bak"],
        )
        assert result.exit_code == 0
        assert "photo.bak" in result.output


class TestRemoveCLI:
    def test_remove_help(self) -> None:
        result = runner.invoke(app, ["remove", "--help"])
        assert result.exit_code == 0

    def test_remove_first_n(self, tmp_path) -> None:
        (tmp_path / "Screenshot_001.png").write_bytes(b"x")
        result = runner.invoke(
            app, ["remove", str(tmp_path), "--first-n", "11"],
        )
        assert result.exit_code == 0
        assert "001.png" in result.output

    def test_remove_crop_before(self, tmp_path) -> None:
        (tmp_path / "prefix_keepme.txt").write_bytes(b"x")
        result = runner.invoke(
            app, ["remove", str(tmp_path), "--crop-before", "prefix_"],
        )
        assert result.exit_code == 0
        assert "keepme.txt" in result.output


class TestInsertCLI:
    def test_insert_help(self) -> None:
        result = runner.invoke(app, ["insert", "--help"])
        assert result.exit_code == 0

    def test_insert_at_start(self, tmp_path) -> None:
        (tmp_path / "photo.jpg").write_bytes(b"x")
        result = runner.invoke(
            app, ["insert", str(tmp_path), "--text", "2024_", "--position", "0"],
        )
        assert result.exit_code == 0
        assert "2024_photo.jpg" in result.output


class TestAutoDateCLI:
    def test_auto_date_help(self) -> None:
        result = runner.invoke(app, ["auto-date", "--help"])
        assert result.exit_code == 0

    def test_auto_date_prefix(self, tmp_path) -> None:
        (tmp_path / "photo.jpg").write_bytes(b"x")
        result = runner.invoke(app, ["auto-date", str(tmp_path)])
        assert result.exit_code == 0
        assert "photo.jpg" in result.output


class TestFolderNameCLI:
    def test_folder_name_help(self) -> None:
        result = runner.invoke(app, ["folder-name", "--help"])
        assert result.exit_code == 0

    def test_folder_name_prefix(self, tmp_path) -> None:
        (tmp_path / "photo.jpg").write_bytes(b"x")
        result = runner.invoke(app, ["folder-name", str(tmp_path)])
        assert result.exit_code == 0
        assert "photo.jpg" in result.output


class TestNumberCLI:
    def test_number_help(self) -> None:
        result = runner.invoke(app, ["number", "--help"])
        assert result.exit_code == 0

    def test_number_basic(self, tmp_path) -> None:
        (tmp_path / "a.txt").write_bytes(b"x")
        (tmp_path / "b.txt").write_bytes(b"x")
        result = runner.invoke(app, ["number", str(tmp_path)])
        assert result.exit_code == 0
        assert "001.txt" in result.output

    def test_number_prefix_mode(self, tmp_path) -> None:
        (tmp_path / "photo.jpg").write_bytes(b"x")
        result = runner.invoke(
            app,
            ["number", str(tmp_path), "--position", "prefix", "--separator", "_"],
        )
        assert result.exit_code == 0
        assert "001_photo.jpg" in result.output


class TestNameCLI:
    def test_name_help(self) -> None:
        result = runner.invoke(app, ["name", "--help"])
        assert result.exit_code == 0

    def test_name_fixed(self, tmp_path) -> None:
        (tmp_path / "photo.jpg").write_bytes(b"x")
        result = runner.invoke(
            app, ["name", str(tmp_path), "--mode", "fixed", "--fixed-name", "image"],
        )
        assert result.exit_code == 0
        assert "image.jpg" in result.output

    def test_name_reverse(self, tmp_path) -> None:
        (tmp_path / "abc.txt").write_bytes(b"x")
        result = runner.invoke(app, ["name", str(tmp_path), "--mode", "reverse"])
        assert result.exit_code == 0
        assert "cba.txt" in result.output


class TestWordSpaceCLI:
    def test_word_space_help(self) -> None:
        result = runner.invoke(app, ["word-space", "--help"])
        assert result.exit_code == 0

    def test_word_space_camel(self, tmp_path) -> None:
        (tmp_path / "MyFileName.txt").write_bytes(b"x")
        result = runner.invoke(app, ["word-space", str(tmp_path)])
        assert result.exit_code == 0
        assert "My File Name.txt" in result.output

    def test_word_space_custom_sep(self, tmp_path) -> None:
        (tmp_path / "MyFileName.txt").write_bytes(b"x")
        result = runner.invoke(
            app, ["word-space", str(tmp_path), "--separator", "-"],
        )
        assert result.exit_code == 0
        assert "My-File-Name.txt" in result.output


class TestReplaceCLIExtended:
    def test_replace_first_only(self, tmp_path) -> None:
        (tmp_path / "aa_bb_aa.txt").write_bytes(b"x")
        result = runner.invoke(
            app,
            ["replace", str(tmp_path), "--old", "aa", "--new", "XX", "--first-only"],
        )
        assert result.exit_code == 0
        assert "XX_bb_aa.txt" in result.output


class TestRegexCLIExtended:
    def test_regex_stem_only(self, tmp_path) -> None:
        (tmp_path / "IMG_001.jpg").write_bytes(b"x")
        result = runner.invoke(
            app,
            [
                "regex", str(tmp_path),
                "--pattern", "IMG", "--replacement", "PHOTO",
                "--stem-only",
            ],
        )
        assert result.exit_code == 0
        assert "PHOTO_001.jpg" in result.output
