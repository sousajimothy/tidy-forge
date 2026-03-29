"""Tests for tidyforge.media_grouping."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from tidyforge.core.models import FileEntry
from tidyforge.media_grouping import (
    ByDate,
    ByExtension,
    ByFilenamePattern,
    ByParentFolder,
    GroupingEngine,
)


def _make_entry(name: str, size: int = 100, year: int = 2024, month: int = 6) -> FileEntry:
    return FileEntry(
        path=Path(f"/fake/{name}"),
        name=name,
        suffix=Path(name).suffix.lower(),
        size=size,
        modified=datetime(year, month, 15, tzinfo=UTC),
    )


class TestStrategies:
    def test_by_extension(self) -> None:
        strategy = ByExtension()
        assert strategy.group_key(_make_entry("photo.jpg")) == ".jpg"
        assert strategy.group_key(_make_entry("photo.PNG")) == ".png"

    def test_by_date_month(self) -> None:
        strategy = ByDate(granularity="month")
        key = strategy.group_key(_make_entry("a.jpg", year=2024, month=3))
        assert key == "2024-03"

    def test_by_date_year(self) -> None:
        strategy = ByDate(granularity="year")
        key = strategy.group_key(_make_entry("a.jpg", year=2024, month=3))
        assert key == "2024"

    def test_by_parent_folder(self) -> None:
        strategy = ByParentFolder()
        entry = _make_entry("a.jpg")
        assert strategy.group_key(entry) == "fake"

    def test_by_filename_pattern(self) -> None:
        strategy = ByFilenamePattern(pattern=r"IMG_(\d{4})")
        entry = FileEntry(
            path=Path("/x/IMG_2024_001.jpg"),
            name="IMG_2024_001.jpg",
            suffix=".jpg",
            size=100,
            modified=datetime.now(UTC),
        )
        assert strategy.group_key(entry) == "2024"

    def test_by_filename_pattern_unmatched(self) -> None:
        strategy = ByFilenamePattern(pattern=r"IMG_(\d{4})")
        entry = _make_entry("random.jpg")
        assert strategy.group_key(entry) == "unmatched"


class TestGroupingEngine:
    def test_group(self) -> None:
        entries = [
            _make_entry("a.jpg"),
            _make_entry("b.jpg"),
            _make_entry("c.png"),
        ]
        engine = GroupingEngine(ByExtension())
        groups = engine.group(entries)

        assert ".jpg" in groups
        assert ".png" in groups
        assert len(groups[".jpg"]) == 2
        assert len(groups[".png"]) == 1

    def test_group_summary(self) -> None:
        entries = [
            _make_entry("a.jpg", size=100),
            _make_entry("b.jpg", size=200),
            _make_entry("c.png", size=50),
        ]
        engine = GroupingEngine(ByExtension())
        summaries = engine.group_summary(entries)

        assert len(summaries) == 2
        # Sorted by count descending, .jpg first
        assert summaries[0].key == ".jpg"
        assert summaries[0].count == 2
        assert summaries[0].total_size == 300

    def test_skips_dirs(self) -> None:
        entries = [
            _make_entry("a.jpg"),
            FileEntry(
                path=Path("/fake/subdir"),
                name="subdir",
                suffix="",
                size=0,
                modified=datetime.now(UTC),
                is_dir=True,
            ),
        ]
        engine = GroupingEngine(ByExtension())
        groups = engine.group(entries)
        assert all(not e.is_dir for entries_list in groups.values() for e in entries_list)
