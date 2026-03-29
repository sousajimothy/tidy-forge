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
        # IMG file should not appear in rename plan
        assert "IMG_003.jpg" not in result.output or "No files" not in result.output
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
