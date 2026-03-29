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
    append_folder_name,
    auto_date,
    build_plan_from_template,
    change_case,
    change_extension,
    change_name,
    insert_at,
    regex_replace,
    remove_chars,
    replace_text,
    sequential_name,
    strip_text,
    word_space,
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


def _execute_or_dryrun(plan, execute: bool) -> None:
    """Execute a plan or print dry-run message."""
    if execute:
        manifest = plan.execute(dry_run=False)
        typer.echo(manifest.summary)
    else:
        typer.echo("\nDry-run mode. Use --execute to apply.")


def _scan(directory: Path) -> list:
    """Validate directory and scan files."""
    directory = directory.resolve()
    if not directory.is_dir():
        print_error(f"Not a directory: {directory}")
        raise typer.Exit(1)
    return list(scan_directory(directory, max_depth=0))


# ---------------------------------------------------------------------------
# Original commands
# ---------------------------------------------------------------------------


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
    entries = _scan(directory)
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
    entries = _scan(directory)
    plan = add_prefix(entries, prefix_text)

    print_header(f"Prefix: '{prefix_text}'")
    _show_plan(plan, directory)
    _execute_or_dryrun(plan, execute)


@app.command()
def suffix(
    directory: Annotated[Path, typer.Argument(help="Directory containing files")],
    suffix_text: Annotated[str, typer.Option("--suffix", help="Suffix to add before extension")],
    execute: Annotated[bool, typer.Option("--execute", help="Actually rename")] = False,
) -> None:
    """Add a suffix before the extension for all filenames."""
    setup_logging()
    entries = _scan(directory)
    plan = add_suffix(entries, suffix_text)

    print_header(f"Suffix: '{suffix_text}'")
    _show_plan(plan, directory)
    _execute_or_dryrun(plan, execute)


@app.command(name="replace")
def replace_cmd(
    directory: Annotated[Path, typer.Argument(help="Directory containing files")],
    old: Annotated[str, typer.Option(help="Text to find")],
    new: Annotated[str, typer.Option(help="Replacement text")],
    first_only: Annotated[
        bool, typer.Option("--first-only", help="Replace only the first occurrence")
    ] = False,
    execute: Annotated[bool, typer.Option("--execute", help="Actually rename")] = False,
) -> None:
    """Replace text in filenames."""
    setup_logging()
    entries = _scan(directory)
    plan = replace_text(entries, old, new, first_only=first_only)

    label = f"Replace: '{old}' -> '{new}'"
    if first_only:
        label += " (first only)"
    print_header(label)
    _show_plan(plan, directory)
    _execute_or_dryrun(plan, execute)


@app.command(name="regex")
def regex_cmd(
    directory: Annotated[Path, typer.Argument(help="Directory containing files")],
    pattern: Annotated[str, typer.Option(help="Regex pattern")],
    replacement: Annotated[str, typer.Option(help="Replacement (supports backreferences)")],
    stem_only: Annotated[
        bool,
        typer.Option("--stem-only", help="Apply regex to stem only, not extension"),
    ] = False,
    execute: Annotated[bool, typer.Option("--execute", help="Actually rename")] = False,
) -> None:
    """Rename files using regex substitution."""
    setup_logging()
    entries = _scan(directory)
    plan = regex_replace(entries, pattern, replacement, include_ext=not stem_only)

    print_header(f"Regex: /{pattern}/ -> '{replacement}'")
    _show_plan(plan, directory)
    _execute_or_dryrun(plan, execute)


@app.command(name="strip")
def strip_cmd(
    directory: Annotated[Path, typer.Argument(help="Directory containing files")],
    text: Annotated[str, typer.Option(help="Text to remove from filenames")],
    position: Annotated[
        str,
        typer.Option(
            help=(
                "Where to strip: 'prefix' (start of name),"
                " 'suffix' (end of stem), 'any' (all occurrences)"
            ),
        ),
    ] = "any",
    ignore_case: Annotated[
        bool,
        typer.Option("--ignore-case", "-i", help="Case-insensitive matching"),
    ] = False,
    execute: Annotated[
        bool, typer.Option("--execute", help="Actually rename")
    ] = False,
) -> None:
    """Strip text from filenames (prefix, suffix, or anywhere)."""
    setup_logging()
    entries = _scan(directory)

    if position not in ("prefix", "suffix", "any"):
        print_error(
            f"Invalid position '{position}'."
            " Use 'prefix', 'suffix', or 'any'."
        )
        raise typer.Exit(1)

    plan = strip_text(
        entries, text, position=position, case_sensitive=not ignore_case,
    )

    label = f"Strip {position}: '{text}'"
    if ignore_case:
        label += " (case-insensitive)"
    print_header(label)
    _show_plan(plan, directory)
    _execute_or_dryrun(plan, execute)


# ---------------------------------------------------------------------------
# New commands — Batch 1
# ---------------------------------------------------------------------------


@app.command(name="case")
def case_cmd(
    directory: Annotated[Path, typer.Argument(help="Directory containing files")],
    case: Annotated[
        str,
        typer.Option(help="Case: 'upper', 'lower', 'title', 'sentence'"),
    ] = "lower",
    scope: Annotated[
        str,
        typer.Option(help="Scope: 'stem', 'ext', 'both'"),
    ] = "stem",
    execute: Annotated[bool, typer.Option("--execute", help="Actually rename")] = False,
) -> None:
    """Change the case of filenames."""
    setup_logging()
    entries = _scan(directory)
    plan = change_case(entries, case, scope=scope)

    print_header(f"Case: {case} ({scope})")
    _show_plan(plan, directory)
    _execute_or_dryrun(plan, execute)


@app.command(name="extension")
def extension_cmd(
    directory: Annotated[Path, typer.Argument(help="Directory containing files")],
    mode: Annotated[
        str,
        typer.Option(
            help="Mode: 'lower', 'upper', 'title', 'fixed', 'extra', 'remove'",
        ),
    ] = "lower",
    ext: Annotated[
        str,
        typer.Option(help="New extension for 'fixed'/'extra' modes (e.g. '.bak')"),
    ] = "",
    execute: Annotated[bool, typer.Option("--execute", help="Actually rename")] = False,
) -> None:
    """Change file extensions."""
    setup_logging()
    entries = _scan(directory)
    plan = change_extension(entries, mode, new_ext=ext)

    print_header(f"Extension: {mode}" + (f" '{ext}'" if ext else ""))
    _show_plan(plan, directory)
    _execute_or_dryrun(plan, execute)


# ---------------------------------------------------------------------------
# New commands — Batch 2
# ---------------------------------------------------------------------------


@app.command(name="remove")
def remove_cmd(
    directory: Annotated[Path, typer.Argument(help="Directory containing files")],
    first_n: Annotated[
        int, typer.Option("--first-n", help="Remove first N characters from stem")
    ] = 0,
    last_n: Annotated[
        int, typer.Option("--last-n", help="Remove last N characters from stem")
    ] = 0,
    from_pos: Annotated[
        int | None,
        typer.Option("--from", help="Remove from this position (0-based)"),
    ] = None,
    to_pos: Annotated[
        int | None,
        typer.Option("--to", help="Remove up to this position (exclusive)"),
    ] = None,
    crop_before: Annotated[
        str | None,
        typer.Option("--crop-before", help="Keep only text after this string"),
    ] = None,
    crop_after: Annotated[
        str | None,
        typer.Option("--crop-after", help="Keep only text before this string"),
    ] = None,
    execute: Annotated[bool, typer.Option("--execute", help="Actually rename")] = False,
) -> None:
    """Remove characters from filename stems."""
    setup_logging()
    entries = _scan(directory)
    plan = remove_chars(
        entries,
        first_n=first_n,
        last_n=last_n,
        from_pos=from_pos,
        to_pos=to_pos,
        crop_before=crop_before,
        crop_after=crop_after,
    )

    # Build a descriptive label
    parts = []
    if first_n:
        parts.append(f"first {first_n}")
    if last_n:
        parts.append(f"last {last_n}")
    if from_pos is not None and to_pos is not None:
        parts.append(f"pos {from_pos}-{to_pos}")
    if crop_before:
        parts.append(f"crop before '{crop_before}'")
    if crop_after:
        parts.append(f"crop after '{crop_after}'")
    print_header(f"Remove: {', '.join(parts) or 'no-op'}")
    _show_plan(plan, directory)
    _execute_or_dryrun(plan, execute)


@app.command(name="insert")
def insert_cmd(
    directory: Annotated[Path, typer.Argument(help="Directory containing files")],
    text: Annotated[str, typer.Option(help="Text to insert")],
    position: Annotated[int, typer.Option(help="Character position (0-based, negative from end)")],
    execute: Annotated[bool, typer.Option("--execute", help="Actually rename")] = False,
) -> None:
    """Insert text at a position in filename stems."""
    setup_logging()
    entries = _scan(directory)
    plan = insert_at(entries, text, position)

    print_header(f"Insert '{text}' at position {position}")
    _show_plan(plan, directory)
    _execute_or_dryrun(plan, execute)


# ---------------------------------------------------------------------------
# New commands — Batch 3
# ---------------------------------------------------------------------------


@app.command(name="auto-date")
def auto_date_cmd(
    directory: Annotated[Path, typer.Argument(help="Directory containing files")],
    source: Annotated[
        str, typer.Option(help="Date source: 'modified' or 'created'")
    ] = "modified",
    fmt: Annotated[
        str, typer.Option("--format", help="Date format (strftime)")
    ] = "%Y-%m-%d",
    position: Annotated[
        str, typer.Option(help="Position: 'prefix' or 'suffix'")
    ] = "prefix",
    separator: Annotated[
        str, typer.Option(help="Separator between date and name")
    ] = "_",
    execute: Annotated[bool, typer.Option("--execute", help="Actually rename")] = False,
) -> None:
    """Add file date to filenames."""
    setup_logging()
    entries = _scan(directory)
    plan = auto_date(
        entries,
        date_source=source,
        fmt=fmt,
        position=position,
        separator=separator,
    )

    print_header(f"Auto-date: {source} ({fmt}) as {position}")
    _show_plan(plan, directory)
    _execute_or_dryrun(plan, execute)


@app.command(name="folder-name")
def folder_name_cmd(
    directory: Annotated[Path, typer.Argument(help="Directory containing files")],
    position: Annotated[
        str, typer.Option(help="Position: 'prefix' or 'suffix'")
    ] = "prefix",
    separator: Annotated[
        str, typer.Option(help="Separator between folder name and filename")
    ] = "_",
    levels: Annotated[
        int, typer.Option(help="Number of parent folder levels")
    ] = 1,
    execute: Annotated[bool, typer.Option("--execute", help="Actually rename")] = False,
) -> None:
    """Prepend or append parent folder name to filenames."""
    setup_logging()
    entries = _scan(directory)
    plan = append_folder_name(
        entries, position=position, separator=separator, levels=levels,
    )

    print_header(f"Folder name: {position} ({levels:,} level(s))")
    _show_plan(plan, directory)
    _execute_or_dryrun(plan, execute)


@app.command(name="number")
def number_cmd(
    directory: Annotated[Path, typer.Argument(help="Directory containing files")],
    start: Annotated[int, typer.Option(help="Starting number")] = 1,
    increment: Annotated[int, typer.Option(help="Step between numbers")] = 1,
    pad: Annotated[int, typer.Option(help="Zero-padding width")] = 3,
    base: Annotated[
        int, typer.Option(help="Number base (10=decimal, 16=hex, 8=octal, 2=binary)")
    ] = 10,
    separator: Annotated[str, typer.Option(help="Separator between number and name")] = "",
    position: Annotated[
        str,
        typer.Option(help="Position: 'replace', 'prefix', 'suffix'"),
    ] = "replace",
    template: Annotated[
        str, typer.Option(help="Template (for 'replace' mode)")
    ] = "{counter}{ext}",
    reset_per_folder: Annotated[
        bool,
        typer.Option("--reset-per-folder", help="Reset counter per parent folder"),
    ] = False,
    execute: Annotated[bool, typer.Option("--execute", help="Actually rename")] = False,
) -> None:
    """Add sequential numbers to filenames."""
    setup_logging()
    entries = _scan(directory)
    plan = sequential_name(
        entries,
        template=template,
        start=start,
        pad=pad,
        increment=increment,
        base=base,
        separator=separator,
        position=position,
        reset_per_folder=reset_per_folder,
    )

    print_header(f"Number: start={start}, step={increment}, base={base}, pos={position}")
    _show_plan(plan, directory)
    _execute_or_dryrun(plan, execute)


# ---------------------------------------------------------------------------
# New commands — Batch 4
# ---------------------------------------------------------------------------


@app.command(name="name")
def name_cmd(
    directory: Annotated[Path, typer.Argument(help="Directory containing files")],
    mode: Annotated[
        str, typer.Option(help="Mode: 'fixed', 'reverse', 'remove'")
    ],
    fixed_name: Annotated[
        str, typer.Option("--fixed-name", help="New stem (for 'fixed' mode)")
    ] = "",
    execute: Annotated[bool, typer.Option("--execute", help="Actually rename")] = False,
) -> None:
    """Manipulate filename stems (fixed text, reverse, or remove)."""
    setup_logging()
    entries = _scan(directory)
    plan = change_name(entries, mode, fixed_name=fixed_name)

    print_header(f"Name: {mode}" + (f" '{fixed_name}'" if fixed_name else ""))
    _show_plan(plan, directory)
    _execute_or_dryrun(plan, execute)


@app.command(name="word-space")
def word_space_cmd(
    directory: Annotated[Path, typer.Argument(help="Directory containing files")],
    separator: Annotated[
        str, typer.Option(help="Separator to insert between words")
    ] = " ",
    execute: Annotated[bool, typer.Option("--execute", help="Actually rename")] = False,
) -> None:
    """Insert spaces between words in filenames (CamelCase, underscores, hyphens)."""
    setup_logging()
    entries = _scan(directory)
    plan = word_space(entries, separator=separator)

    print_header(f"Word space: separator='{separator}'")
    _show_plan(plan, directory)
    _execute_or_dryrun(plan, execute)
