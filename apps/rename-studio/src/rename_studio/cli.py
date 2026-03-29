"""Rename Studio CLI - batch rename with preview and safety checks."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from tidyforge.core.logging import setup_logging
from tidyforge.fs_indexer import scan_directory
from tidyforge.rename_engine import (
    add_prefix,
    add_suffix,
    build_plan_from_template,
    regex_replace,
    replace_text,
)
from tidyforge.ui_common import print_error, print_header, print_table, print_warning

app = typer.Typer(
    name="rename-studio",
    help="Batch rename files with templates, regex, and collision detection.",
    no_args_is_help=True,
)


def _show_plan(plan, directory: Path) -> None:
    """Display a rename plan as a table."""
    issues = plan.validate()
    if issues:
        for issue in issues:
            print_warning(issue)

    preview = plan.preview()
    if not preview:
        typer.echo("No files to rename.")
        return

    rows = [[old, new] for old, new in preview]
    print_table(
        f"{len(preview):,} renames planned",
        ["Current Name", "New Name"],
        rows,
    )


@app.command()
def preview(
    directory: Annotated[Path, typer.Argument(help="Directory containing files to rename")],
    template: Annotated[
        str, typer.Option(help="Rename template (e.g. '{date}_{name}{ext}')")
    ] = "{name}{ext}",
    glob: Annotated[str, typer.Option(help="File glob pattern")] = "*",
) -> None:
    """Preview a template-based batch rename (dry-run only)."""
    setup_logging()
    directory = directory.resolve()

    if not directory.is_dir():
        print_error(f"Not a directory: {directory}")
        raise typer.Exit(1)

    entries = list(scan_directory(directory, max_depth=0))
    plan = build_plan_from_template(entries, template)

    print_header("Rename Preview (dry-run)")
    _show_plan(plan, directory)


@app.command()
def prefix(
    directory: Annotated[Path, typer.Argument(help="Directory containing files")],
    prefix_text: Annotated[str, typer.Option("--prefix", help="Prefix to add")],
    execute: Annotated[
        bool, typer.Option("--execute", help="Actually rename (default: preview only)")
    ] = False,
) -> None:
    """Add a prefix to all filenames in a directory."""
    setup_logging()
    directory = directory.resolve()

    if not directory.is_dir():
        print_error(f"Not a directory: {directory}")
        raise typer.Exit(1)

    entries = list(scan_directory(directory, max_depth=0))
    plan = add_prefix(entries, prefix_text)

    print_header(f"Prefix: '{prefix_text}'")
    _show_plan(plan, directory)

    if execute:
        manifest = plan.execute(dry_run=False)
        typer.echo(manifest.summary)
    else:
        typer.echo("\nDry-run mode. Use --execute to apply.")


@app.command()
def suffix(
    directory: Annotated[Path, typer.Argument(help="Directory containing files")],
    suffix_text: Annotated[str, typer.Option("--suffix", help="Suffix to add before extension")],
    execute: Annotated[bool, typer.Option("--execute", help="Actually rename")] = False,
) -> None:
    """Add a suffix before the extension for all filenames."""
    setup_logging()
    directory = directory.resolve()

    if not directory.is_dir():
        print_error(f"Not a directory: {directory}")
        raise typer.Exit(1)

    entries = list(scan_directory(directory, max_depth=0))
    plan = add_suffix(entries, suffix_text)

    print_header(f"Suffix: '{suffix_text}'")
    _show_plan(plan, directory)

    if execute:
        manifest = plan.execute(dry_run=False)
        typer.echo(manifest.summary)
    else:
        typer.echo("\nDry-run mode. Use --execute to apply.")


@app.command(name="replace")
def replace_cmd(
    directory: Annotated[Path, typer.Argument(help="Directory containing files")],
    old: Annotated[str, typer.Option(help="Text to find")],
    new: Annotated[str, typer.Option(help="Replacement text")],
    execute: Annotated[bool, typer.Option("--execute", help="Actually rename")] = False,
) -> None:
    """Replace text in filenames."""
    setup_logging()
    directory = directory.resolve()

    if not directory.is_dir():
        print_error(f"Not a directory: {directory}")
        raise typer.Exit(1)

    entries = list(scan_directory(directory, max_depth=0))
    plan = replace_text(entries, old, new)

    print_header(f"Replace: '{old}' -> '{new}'")
    _show_plan(plan, directory)

    if execute:
        manifest = plan.execute(dry_run=False)
        typer.echo(manifest.summary)
    else:
        typer.echo("\nDry-run mode. Use --execute to apply.")


@app.command(name="regex")
def regex_cmd(
    directory: Annotated[Path, typer.Argument(help="Directory containing files")],
    pattern: Annotated[str, typer.Option(help="Regex pattern")],
    replacement: Annotated[str, typer.Option(help="Replacement (supports backreferences)")],
    execute: Annotated[bool, typer.Option("--execute", help="Actually rename")] = False,
) -> None:
    """Rename files using regex substitution."""
    setup_logging()
    directory = directory.resolve()

    if not directory.is_dir():
        print_error(f"Not a directory: {directory}")
        raise typer.Exit(1)

    entries = list(scan_directory(directory, max_depth=0))
    plan = regex_replace(entries, pattern, replacement)

    print_header(f"Regex: /{pattern}/ -> '{replacement}'")
    _show_plan(plan, directory)

    if execute:
        manifest = plan.execute(dry_run=False)
        typer.echo(manifest.summary)
    else:
        typer.echo("\nDry-run mode. Use --execute to apply.")
