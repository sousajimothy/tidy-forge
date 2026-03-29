"""CLI smoke tests for media-curator."""

from __future__ import annotations

from typer.testing import CliRunner

from media_curator.cli import app

runner = CliRunner()


class TestMediaCuratorCLI:
    def test_help(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "media-curator" in result.output.lower() or "organise" in result.output.lower()

    def test_scan_help(self) -> None:
        result = runner.invoke(app, ["scan", "--help"])
        assert result.exit_code == 0

    def test_group_help(self) -> None:
        result = runner.invoke(app, ["group", "--help"])
        assert result.exit_code == 0

    def test_scan_nonexistent(self, tmp_path) -> None:
        result = runner.invoke(app, ["scan", str(tmp_path / "nope")])
        assert result.exit_code != 0

    def test_scan_empty(self, tmp_path) -> None:
        result = runner.invoke(app, ["scan", str(tmp_path)])
        assert result.exit_code == 0
        assert "No files found" in result.output

    def test_scan_with_files(self, tmp_tree) -> None:
        result = runner.invoke(app, ["scan", str(tmp_tree), "--all"])
        assert result.exit_code == 0
