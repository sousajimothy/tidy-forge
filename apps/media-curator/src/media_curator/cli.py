"""Media Curator CLI - scan, group, and organise media files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated

import typer

from media_curator.organize import build_organize_plan
from tidyforge.core.logging import setup_logging
from tidyforge.fs_indexer import ExtensionFilter, PatternFilter, scan_directory
from tidyforge.media_grouping import (
    ByDate,
    ByExtension,
    ByFilenamePattern,
    ByParentFolder,
    GroupingEngine,
)
from tidyforge.metadata import categorize_file
from tidyforge.ui_common import (
    format_size,
    print_error,
    print_header,
    print_success,
    print_table,
    print_warning,
)

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
        rows.append([cat, f"{len(cat_entries):,}", format_size(cat_size)])

    print_table(
        f"{len(entries):,} files ({format_size(total_size)})",
        ["Category", "Count", "Size"],
        rows,
    )


@app.command()
def organize(
    source: Annotated[Path, typer.Argument(help="Source directory to organise")],
    dest: Annotated[
        Path | None, typer.Argument(help="Destination root (default: in-place)")
    ] = None,
    date_format: Annotated[
        str, typer.Option("--format", help="strftime format for subfolder names")
    ] = "%Y%m",
    copy: Annotated[
        bool, typer.Option("--copy", help="Copy files instead of moving")
    ] = False,
    ext: Annotated[
        str | None,
        typer.Option(help="Extensions to include, comma-separated e.g. .jpg,.png"),
    ] = None,
    match: Annotated[
        str | None,
        typer.Option(help="Regex pattern matched against filenames"),
    ] = None,
    prefix: Annotated[
        str | None,
        typer.Option(help="Only files whose name starts with this string"),
    ] = None,
    suffix: Annotated[
        str | None,
        typer.Option(help="Only files whose stem ends with this string"),
    ] = None,
    group_pattern: Annotated[
        str | None,
        typer.Option(
            "--group-pattern",
            help="Regex with capture group for subfolder name (overrides --format)",
        ),
    ] = None,
    skip_unmatched: Annotated[
        bool,
        typer.Option(
            "--skip-unmatched",
            help="Leave files that don't match --group-pattern in place",
        ),
    ] = False,
    all_files: Annotated[
        bool, typer.Option("--all", help="Include non-media files")
    ] = False,
    execute: Annotated[
        bool, typer.Option("--execute", help="Apply changes (default is dry-run)")
    ] = False,
) -> None:
    """Organise files into subdirectories by date or pattern. Dry-run by default."""
    setup_logging()
    source = source.resolve()

    if not source.is_dir():
        print_error(f"Not a directory: {source}")
        raise typer.Exit(1)

    # Build filter list
    filters = []

    # Extension filter
    if ext is not None:
        filters.append(ExtensionFilter(include={e.strip() for e in ext.split(",")}))
    elif not all_files:
        filters.append(ExtensionFilter(include=MEDIA_EXTENSIONS))

    # Pattern filters
    if match is not None:
        filters.append(PatternFilter(pattern=match))
    if prefix is not None:
        filters.append(PatternFilter(pattern=f"^{re.escape(prefix)}"))
    if suffix is not None:
        filters.append(PatternFilter(pattern=f"{re.escape(suffix)}\\.[^.]*$"))

    entries = list(scan_directory(source, filters=filters))

    if not entries:
        typer.echo("No files found.")
        raise typer.Exit(0)

    dest_dir = dest.resolve() if dest else source
    mode = "copy" if copy else "move"

    # Build group function — pattern overrides date format
    group_fn = None
    if group_pattern is not None:
        strategy = ByFilenamePattern(pattern=group_pattern)
        group_fn = strategy.group_key

    plan = build_organize_plan(
        entries,
        dest_dir,
        date_format=date_format,
        mode=mode,
        group_fn=group_fn,
        skip_unmatched=skip_unmatched,
    )

    # Validate — abort on collisions, warn on overwrites
    issues = plan.validate()
    collisions = [i for i in issues if i.startswith("Collision")]
    warnings = [i for i in issues if not i.startswith("Collision")]

    for w in warnings:
        print_warning(w)

    if collisions:
        for c in collisions:
            print_error(c)
        raise typer.Exit(1)

    # Preview table
    print_header(f"Organise: {source.name} ({'dry-run' if not execute else mode})")

    rows = [
        [action.source.name, str(action.destination.relative_to(dest_dir))]
        for action in plan.actions
    ]
    print_table(
        f"{len(entries):,} files -> {dest_dir}",
        ["Source", "Destination"],
        rows,
    )

    if not execute:
        typer.echo("\nDry-run: no files changed. Pass --execute to apply.")
        raise typer.Exit(0)

    manifest = plan.execute(dry_run=False)
    print_success(manifest.summary)


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
        [s.key, f"{s.count:,}", format_size(s.total_size), ", ".join(sorted(s.extensions))]
        for s in summaries
    ]
    print_table(
        f"{len(summaries):,} groups from {len(entries):,} files",
        ["Group", "Files", "Size", "Extensions"],
        rows,
    )
