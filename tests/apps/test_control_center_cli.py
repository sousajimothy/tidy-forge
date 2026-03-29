"""CLI smoke tests for control-center (tidyforge command)."""

from __future__ import annotations

from typer.testing import CliRunner

from control_center.cli import app

runner = CliRunner()


class TestControlCenterCLI:
    def test_help(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "tidyforge" in result.output.lower() or "TidyForge" in result.output

    def test_version(self) -> None:
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_media_help(self) -> None:
        result = runner.invoke(app, ["media", "--help"])
        assert result.exit_code == 0

    def test_disk_help(self) -> None:
        result = runner.invoke(app, ["disk", "--help"])
        assert result.exit_code == 0

    def test_rename_help(self) -> None:
        result = runner.invoke(app, ["rename", "--help"])
        assert result.exit_code == 0
