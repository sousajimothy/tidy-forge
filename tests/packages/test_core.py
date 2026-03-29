"""Tests for tidyforge.core."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from tidyforge.core.config import TidyForgeSettings
from tidyforge.core.exceptions import CollisionError, RenameError, ScanError, TidyForgeError
from tidyforge.core.models import ActionManifest, FileEntry, OperationResult


class TestFileEntry:
    def test_from_path(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("hello")
        entry = FileEntry.from_path(f)

        assert entry.name == "test.txt"
        assert entry.suffix == ".txt"
        assert entry.size == 5
        assert not entry.is_dir

    def test_from_path_directory(self, tmp_path: Path) -> None:
        d = tmp_path / "subdir"
        d.mkdir()
        entry = FileEntry.from_path(d)

        assert entry.is_dir
        assert entry.name == "subdir"

    def test_size_human(self) -> None:
        entry = FileEntry(
            path=Path("test.bin"),
            name="test.bin",
            suffix=".bin",
            size=1536,
            modified=datetime.now(UTC),
        )
        assert entry.size_human == "1.5 KB"

    def test_size_human_zero(self) -> None:
        entry = FileEntry(
            path=Path("empty"),
            name="empty",
            suffix="",
            size=0,
            modified=datetime.now(UTC),
        )
        assert entry.size_human == "0 B"

    def test_size_human_large(self) -> None:
        entry = FileEntry(
            path=Path("big.iso"),
            name="big.iso",
            suffix=".iso",
            size=2 * 1024**3,
            modified=datetime.now(UTC),
        )
        assert entry.size_human == "2.0 GB"


class TestActionManifest:
    def test_summary_dry_run(self) -> None:
        manifest = ActionManifest(
            dry_run=True,
            operations=[
                OperationResult(success=True, source=Path("a.txt")),
                OperationResult(success=True, source=Path("b.txt")),
                OperationResult(success=False, source=Path("c.txt"), error="fail"),
            ],
        )
        assert "DRY RUN" in manifest.summary
        assert manifest.success_count == 2
        assert manifest.failure_count == 1

    def test_to_json(self, tmp_path: Path) -> None:
        manifest = ActionManifest(operations=[OperationResult(success=True, source=Path("a.txt"))])
        out = tmp_path / "manifest.json"
        manifest.to_json(out)
        assert out.exists()
        assert "a.txt" in out.read_text()


class TestSettings:
    def test_defaults(self) -> None:
        settings = TidyForgeSettings()
        assert settings.log_level == "INFO"
        assert settings.dry_run is True

    def test_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TIDYFORGE_LOG_LEVEL", "DEBUG")
        settings = TidyForgeSettings()
        assert settings.log_level == "DEBUG"


class TestExceptions:
    def test_hierarchy(self) -> None:
        assert issubclass(ScanError, TidyForgeError)
        assert issubclass(RenameError, TidyForgeError)
        assert issubclass(CollisionError, RenameError)

    def test_raise(self) -> None:
        with pytest.raises(TidyForgeError):
            raise ScanError("test")
