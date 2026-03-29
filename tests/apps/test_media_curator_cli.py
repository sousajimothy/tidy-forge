"""CLI smoke tests for media-curator."""

from __future__ import annotations

import os
import time

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


def _make_jpg(directory, name: str, mtime_epoch: float) -> None:
    """Create a .jpg file with a specific modification time."""
    p = directory / name
    p.write_bytes(b"\xff\xd8\xff")  # minimal JPEG magic
    os.utime(p, (mtime_epoch, mtime_epoch))


# Epoch timestamps for deterministic date groups
_JAN_2026 = time.mktime(time.strptime("2026-01-15", "%Y-%m-%d"))
_FEB_2026 = time.mktime(time.strptime("2026-02-10", "%Y-%m-%d"))


class TestOrganizeCLI:
    def test_organize_help(self) -> None:
        result = runner.invoke(app, ["organize", "--help"])
        assert result.exit_code == 0
        assert "organize" in result.output.lower() or "organise" in result.output.lower()

    def test_organize_dryrun_default(self, tmp_path) -> None:
        """Dry-run should not move any files."""
        _make_jpg(tmp_path, "photo.jpg", _JAN_2026)
        result = runner.invoke(app, ["organize", str(tmp_path)])
        assert result.exit_code == 0
        assert (tmp_path / "photo.jpg").exists(), "File must still exist after dry-run"
        assert "dry-run" in result.output.lower() or "Dry-run" in result.output

    def test_organize_execute_move(self, tmp_path) -> None:
        """--execute should move files into YYYYMM subdirectories."""
        _make_jpg(tmp_path, "photo.jpg", _JAN_2026)
        result = runner.invoke(app, ["organize", str(tmp_path), "--execute"])
        assert result.exit_code == 0
        assert not (tmp_path / "photo.jpg").exists(), "Original should be gone after move"
        assert (tmp_path / "202601" / "photo.jpg").exists()

    def test_organize_execute_copy(self, tmp_path) -> None:
        """--copy --execute should copy files; originals must remain."""
        _make_jpg(tmp_path, "photo.jpg", _JAN_2026)
        result = runner.invoke(app, ["organize", str(tmp_path), "--copy", "--execute"])
        assert result.exit_code == 0
        assert (tmp_path / "photo.jpg").exists(), "Original must remain after copy"
        assert (tmp_path / "202601" / "photo.jpg").exists()

    def test_organize_ext_filter(self, tmp_path) -> None:
        """--ext should restrict which files are organised."""
        _make_jpg(tmp_path, "photo.jpg", _JAN_2026)
        (tmp_path / "doc.txt").write_bytes(b"hello")
        result = runner.invoke(
            app, ["organize", str(tmp_path), "--ext", ".jpg", "--execute"]
        )
        assert result.exit_code == 0
        assert (tmp_path / "202601" / "photo.jpg").exists()
        assert (tmp_path / "doc.txt").exists(), "Non-matching file must not be moved"

    def test_organize_prefix_filter(self, tmp_path) -> None:
        """--prefix should only include files whose name starts with the prefix."""
        _make_jpg(tmp_path, "IMG_001.jpg", _JAN_2026)
        _make_jpg(tmp_path, "DSC_001.jpg", _JAN_2026)
        result = runner.invoke(
            app,
            ["organize", str(tmp_path), "--prefix", "IMG_", "--execute"],
        )
        assert result.exit_code == 0
        assert (tmp_path / "202601" / "IMG_001.jpg").exists()
        assert (tmp_path / "DSC_001.jpg").exists(), "Non-matching file must not be moved"

    def test_organize_suffix_filter(self, tmp_path) -> None:
        """--suffix should only include files whose stem ends with the suffix."""
        _make_jpg(tmp_path, "photo_edited.jpg", _JAN_2026)
        _make_jpg(tmp_path, "photo_raw.jpg", _JAN_2026)
        result = runner.invoke(
            app,
            ["organize", str(tmp_path), "--suffix", "_edited", "--execute"],
        )
        assert result.exit_code == 0
        assert (tmp_path / "202601" / "photo_edited.jpg").exists()
        assert (tmp_path / "photo_raw.jpg").exists(), "Non-matching file must not be moved"

    def test_organize_custom_format(self, tmp_path) -> None:
        """--format should control the subfolder name."""
        _make_jpg(tmp_path, "photo.jpg", _JAN_2026)
        result = runner.invoke(
            app,
            ["organize", str(tmp_path), "--format", "%Y-%m", "--execute"],
        )
        assert result.exit_code == 0
        assert (tmp_path / "2026-01" / "photo.jpg").exists()

    def test_organize_dest_arg(self, tmp_path) -> None:
        """Explicit dest argument places files under that root, not in-place."""
        src = tmp_path / "source"
        src.mkdir()
        dst = tmp_path / "dest"
        _make_jpg(src, "photo.jpg", _JAN_2026)
        result = runner.invoke(
            app, ["organize", str(src), str(dst), "--execute"]
        )
        assert result.exit_code == 0
        assert (src / "photo.jpg").not_exists() if hasattr(src / "photo.jpg", "not_exists") \
            else not (src / "photo.jpg").exists()
        assert (dst / "202601" / "photo.jpg").exists()

    def test_organize_multiple_date_groups(self, tmp_path) -> None:
        """Files with different dates land in different subfolders."""
        _make_jpg(tmp_path, "jan.jpg", _JAN_2026)
        _make_jpg(tmp_path, "feb.jpg", _FEB_2026)
        result = runner.invoke(app, ["organize", str(tmp_path), "--execute"])
        assert result.exit_code == 0
        assert (tmp_path / "202601" / "jan.jpg").exists()
        assert (tmp_path / "202602" / "feb.jpg").exists()

    def test_organize_group_pattern_dryrun(self, tmp_path) -> None:
        """--group-pattern with capture group shows preview without moving."""
        _make_jpg(tmp_path, "Screenshot_20260101_120000_Reddit.png", _JAN_2026)
        _make_jpg(tmp_path, "Screenshot_20260101_130000_Firefox.png", _JAN_2026)
        pattern = r"Screenshot_\d{8}_\d{6}_(.+?)(?:\(\d+\))*\.\w+$"
        result = runner.invoke(
            app,
            ["organize", str(tmp_path), "--group-pattern", pattern, "--all"],
        )
        assert result.exit_code == 0
        # Dry-run: files must still be in place
        assert (tmp_path / "Screenshot_20260101_120000_Reddit.png").exists()
        assert (tmp_path / "Screenshot_20260101_130000_Firefox.png").exists()
        assert "dry-run" in result.output.lower() or "Dry-run" in result.output

    def test_organize_group_pattern_execute(self, tmp_path) -> None:
        """--group-pattern moves files into app-name subdirectories."""
        _make_jpg(tmp_path, "Screenshot_20260101_120000_Reddit.png", _JAN_2026)
        _make_jpg(tmp_path, "Screenshot_20260101_130000_Firefox.png", _JAN_2026)
        _make_jpg(
            tmp_path, "Screenshot_20260201_181839_Mr D(1)(1).png", _FEB_2026,
        )
        pattern = r"Screenshot_\d{8}_\d{6}_(.+?)(?:\(\d+\))*\.\w+$"
        result = runner.invoke(
            app,
            [
                "organize", str(tmp_path),
                "--group-pattern", pattern,
                "--all", "--execute",
            ],
        )
        assert result.exit_code == 0
        assert (tmp_path / "Reddit" / "Screenshot_20260101_120000_Reddit.png").exists()
        assert (
            tmp_path / "Firefox" / "Screenshot_20260101_130000_Firefox.png"
        ).exists()
        assert (
            tmp_path / "Mr D" / "Screenshot_20260201_181839_Mr D(1)(1).png"
        ).exists()

    def test_organize_group_pattern_unmatched(self, tmp_path) -> None:
        """Files not matching the pattern go into an 'unmatched' subfolder."""
        _make_jpg(tmp_path, "Screenshot_20260101_120000_Reddit.png", _JAN_2026)
        _make_jpg(tmp_path, "random_photo.jpg", _JAN_2026)
        pattern = r"Screenshot_\d{8}_\d{6}_(.+?)(?:\(\d+\))*\.\w+$"
        result = runner.invoke(
            app,
            [
                "organize", str(tmp_path),
                "--group-pattern", pattern,
                "--all", "--execute",
            ],
        )
        assert result.exit_code == 0
        assert (tmp_path / "Reddit" / "Screenshot_20260101_120000_Reddit.png").exists()
        assert (tmp_path / "unmatched" / "random_photo.jpg").exists()

    def test_organize_skip_unmatched(self, tmp_path) -> None:
        """--skip-unmatched leaves non-matching files in place."""
        _make_jpg(tmp_path, "Screenshot_20260101_120000_Reddit.png", _JAN_2026)
        _make_jpg(tmp_path, "random_photo.jpg", _JAN_2026)
        pattern = r"Screenshot_\d{8}_\d{6}_(.+?)(?:\(\d+\))*\.\w+$"
        result = runner.invoke(
            app,
            [
                "organize", str(tmp_path),
                "--group-pattern", pattern,
                "--skip-unmatched",
                "--all", "--execute",
            ],
        )
        assert result.exit_code == 0
        assert (tmp_path / "Reddit" / "Screenshot_20260101_120000_Reddit.png").exists()
        # Non-matching file stays exactly where it was
        assert (tmp_path / "random_photo.jpg").exists()
        assert not (tmp_path / "unmatched").exists()
