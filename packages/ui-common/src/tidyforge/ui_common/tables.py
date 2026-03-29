"""Table and tree formatting helpers."""

from __future__ import annotations

import math

from rich.table import Table

from tidyforge.core.models import FileEntry
from tidyforge.ui_common.console import console


def format_size(size_bytes: int) -> str:
    """Format a byte count as a human-readable string.

    Args:
        size_bytes: Size in bytes.

    Returns:
        Formatted string (e.g. ``"4.2 MB"``).
    """
    if size_bytes == 0:
        return "0 B"
    units = ("B", "KB", "MB", "GB", "TB")
    i = min(int(math.floor(math.log(size_bytes, 1024))), len(units) - 1)
    value = size_bytes / (1024**i)
    return f"{value:.1f} {units[i]}"


def print_table(
    title: str,
    columns: list[str],
    rows: list[list[str]],
) -> None:
    """Print a Rich table.

    Args:
        title: Table title.
        columns: Column header names.
        rows: List of row data (each row is a list of strings).
    """
    table = Table(title=title, show_lines=False)
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*row)
    console.print(table)


def print_file_table(
    entries: list[FileEntry],
    title: str = "Files",
    max_rows: int = 50,
) -> None:
    """Print a table of file entries.

    Args:
        entries: File entries to display.
        title: Table title.
        max_rows: Maximum rows to display.
    """
    table = Table(title=title)
    table.add_column("Name", style="cyan")
    table.add_column("Size", justify="right", style="green")
    table.add_column("Modified", style="yellow")
    table.add_column("Type", style="magenta")

    for entry in entries[:max_rows]:
        table.add_row(
            entry.name,
            entry.size_human,
            entry.modified.strftime("%Y-%m-%d %H:%M"),
            entry.suffix or "(dir)" if entry.is_dir else entry.suffix or "-",
        )

    if len(entries) > max_rows:
        table.add_row(f"... and {len(entries) - max_rows} more", "", "", "")

    console.print(table)
