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
