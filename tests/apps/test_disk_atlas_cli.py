"""CLI smoke tests for disk-atlas."""

from __future__ import annotations

from typer.testing import CliRunner

from disk_atlas.cli import app

runner = CliRunner()


class TestDiskAtlasCLI:
    def test_help(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

    def test_scan_help(self) -> None:
        result = runner.invoke(app, ["scan", "--help"])
        assert result.exit_code == 0

    def test_scan_nonexistent(self, tmp_path) -> None:
        result = runner.invoke(app, ["scan", str(tmp_path / "nope")])
        assert result.exit_code != 0

    def test_scan_empty(self, tmp_path) -> None:
        result = runner.invoke(app, ["scan", str(tmp_path)])
        assert result.exit_code == 0

    def test_scan_with_files(self, tmp_tree) -> None:
        result = runner.invoke(app, ["scan", str(tmp_tree)])
        assert result.exit_code == 0
        assert "Largest Files" in result.output or "files" in result.output.lower()
