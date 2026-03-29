"""Media Curator CLI - scan, group, and organise media files."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from tidyforge.core.logging import setup_logging
from tidyforge.fs_indexer import ExtensionFilter, scan_directory
from tidyforge.media_grouping import (
    ByDate,
    ByExtension,
    ByParentFolder,
    GroupingEngine,
)
from tidyforge.metadata import categorize_file
from tidyforge.ui_common import format_size, print_error, print_header, print_table

app = typer.Typer(
    name="media-curator",
    help="Organise photos and videos by metadata, dates, and folder structure.",
    no_args_is_help=True,
)


MEDIA_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tiff",
    ".tif",
    ".webp",
    ".heic",
    ".heif",
    ".raw",
    ".cr2",
    ".nef",
    ".arw",
    ".svg",
    ".mp4",
    ".avi",
    ".mkv",
    ".mov",
    ".wmv",
    ".flv",
    ".webm",
    ".m4v",
    ".mp3",
    ".wav",
    ".flac",
    ".aac",
    ".ogg",
    ".wma",
    ".m4a",
}


@app.command()
def scan(
    directory: Annotated[Path, typer.Argument(help="Directory to scan for media files")],
    all_files: Annotated[bool, typer.Option("--all", help="Include non-media files")] = False,
) -> None:
    """Scan a directory and report media file statistics."""
    setup_logging()
    directory = directory.resolve()

    if not directory.is_dir():
        print_error(f"Not a directory: {directory}")
        raise typer.Exit(1)

    filters = [] if all_files else [ExtensionFilter(include=MEDIA_EXTENSIONS)]
    entries = list(scan_directory(directory, filters=filters))

    if not entries:
        typer.echo("No files found.")
        raise typer.Exit(0)

    # Category breakdown
    categories: dict[str, list] = {}
    total_size = 0
    for entry in entries:
        cat = categorize_file(entry.path)
        categories.setdefault(cat, []).append(entry)
        total_size += entry.size

    print_header(f"Media Scan: {directory.name}")

    rows = []
    for cat, cat_entries in sorted(categories.items(), key=lambda x: -len(x[1])):
        cat_size = sum(e.size for e in cat_entries)
        rows.append([cat, str(len(cat_entries)), format_size(cat_size)])

    print_table(
        f"{len(entries)} files ({format_size(total_size)})",
        ["Category", "Count", "Size"],
        rows,
    )


@app.command()
def group(
    directory: Annotated[Path, typer.Argument(help="Directory to scan")],
    by: Annotated[str, typer.Option(help="Grouping strategy: extension, date, folder")] = "date",
    granularity: Annotated[str, typer.Option(help="Date granularity: year, month, day")] = "month",
) -> None:
    """Group media files and show a summary of each group."""
    setup_logging()
    directory = directory.resolve()

    if not directory.is_dir():
        print_error(f"Not a directory: {directory}")
        raise typer.Exit(1)

    filters = [ExtensionFilter(include=MEDIA_EXTENSIONS)]
    entries = list(scan_directory(directory, filters=filters))

    if not entries:
        typer.echo("No media files found.")
        raise typer.Exit(0)

    strategies = {
        "extension": ByExtension(),
        "date": ByDate(granularity=granularity),
        "folder": ByParentFolder(),
    }

    strategy = strategies.get(by)
    if strategy is None:
        print_error(f"Unknown strategy '{by}'. Choose from: {', '.join(strategies)}")
        raise typer.Exit(1)

    engine = GroupingEngine(strategy)
    summaries = engine.group_summary(entries)

    print_header(f"Groups by {by}")

    rows = [
        [s.key, str(s.count), format_size(s.total_size), ", ".join(sorted(s.extensions))]
        for s in summaries
    ]
    print_table(
        f"{len(summaries)} groups from {len(entries)} files",
        ["Group", "Files", "Size", "Extensions"],
        rows,
    )
