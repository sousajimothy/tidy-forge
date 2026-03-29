"""Disk Atlas CLI - analyse disk usage."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from tidyforge.core.logging import setup_logging
from tidyforge.fs_indexer import (
    aggregate_by_directory,
    aggregate_by_extension,
    scan_directory,
    top_n,
)
from tidyforge.ui_common import format_size, print_error, print_header, print_table

app = typer.Typer(
    name="disk-atlas",
    help="Analyse disk usage: largest files, folders, and file type distribution.",
    no_args_is_help=True,
)


@app.command()
def scan(
    directory: Annotated[Path, typer.Argument(help="Directory to analyse")],
    top: Annotated[int, typer.Option(help="Number of top items to show")] = 15,
    max_depth: Annotated[int | None, typer.Option(help="Max scan depth")] = None,
) -> None:
    """Analyse a directory and report usage statistics."""
    setup_logging()
    directory = directory.resolve()

    if not directory.is_dir():
        print_error(f"Not a directory: {directory}")
        raise typer.Exit(1)

    typer.echo(f"Scanning {directory} ...")
    entries = list(scan_directory(directory, max_depth=max_depth))

    if not entries:
        typer.echo("No files found.")
        raise typer.Exit(0)

    total_size = sum(e.size for e in entries)
    total_count = len(entries)

    print_header(f"Disk Usage: {directory.name}")
    typer.echo(f"Total: {total_count} files, {format_size(total_size)}\n")

    # Largest files
    largest = top_n(entries, n=top, key="size")
    rows = []
    for entry in largest:
        rel = (
            entry.path.relative_to(directory)
            if entry.path.is_relative_to(directory)
            else entry.path
        )
        rows.append([str(rel), format_size(entry.size), entry.suffix or "-"])
    print_table(f"Top {top} Largest Files", ["Path", "Size", "Type"], rows)

    # Extension distribution
    ext_stats = aggregate_by_extension(entries)
    ext_sorted = sorted(ext_stats.values(), key=lambda s: s.total_size, reverse=True)
    rows = [[s.extension, str(s.count), format_size(s.total_size)] for s in ext_sorted[:top]]
    print_table("File Type Distribution", ["Extension", "Count", "Total Size"], rows)

    # Largest directories
    dir_stats = aggregate_by_directory(entries)
    dir_sorted = sorted(dir_stats.values(), key=lambda s: s.total_size, reverse=True)
    rows = []
    for ds in dir_sorted[:top]:
        rel = ds.path.relative_to(directory) if ds.path.is_relative_to(directory) else ds.path
        rows.append([str(rel), str(ds.file_count), format_size(ds.total_size)])
    print_table(f"Top {top} Largest Directories", ["Directory", "Files", "Size"], rows)


@app.command()
def tree(
    directory: Annotated[Path, typer.Argument(help="Directory to display")],
    depth: Annotated[int, typer.Option(help="Display depth")] = 2,
) -> None:
    """Show a directory tree with sizes."""
    setup_logging()
    directory = directory.resolve()

    if not directory.is_dir():
        print_error(f"Not a directory: {directory}")
        raise typer.Exit(1)

    entries = list(scan_directory(directory, max_depth=depth, include_dirs=True))
    dir_sizes: dict[Path, int] = {}
    for entry in entries:
        if not entry.is_dir:
            for parent in [entry.path.parent] + list(entry.path.parent.parents):
                if parent == directory.parent:
                    break
                dir_sizes[parent] = dir_sizes.get(parent, 0) + entry.size

    from rich.tree import Tree as RichTree

    from tidyforge.ui_common import console

    tree = RichTree(f"[bold]{directory.name}[/bold] ({format_size(dir_sizes.get(directory, 0))})")

    def _add_children(parent_tree: RichTree, parent_path: Path, current_depth: int) -> None:
        if current_depth >= depth:
            return
        try:
            children = sorted(parent_path.iterdir())
        except PermissionError:
            parent_tree.add("[red]Permission denied[/red]")
            return

        dirs = [c for c in children if c.is_dir()]
        dirs.sort(key=lambda d: dir_sizes.get(d, 0), reverse=True)

        for d in dirs[:15]:
            size = format_size(dir_sizes.get(d, 0))
            branch = parent_tree.add(f"[bold blue]{d.name}/[/bold blue] ({size})")
            _add_children(branch, d, current_depth + 1)

    _add_children(tree, directory, 0)
    console.print(tree)
