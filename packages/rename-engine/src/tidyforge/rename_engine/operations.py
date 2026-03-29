"""Simple rename operations: prefix, suffix, replace, regex, sequence."""

from __future__ import annotations

import re

from tidyforge.core.models import FileEntry
from tidyforge.rename_engine.plan import RenameAction, RenamePlan

# Characters not allowed in filenames on Windows
_UNSAFE_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_filename(name: str, replacement: str = "_") -> str:
    """Remove or replace characters that are unsafe in filenames.

    Args:
        name: Filename to sanitise (without path).
        replacement: Character to substitute for unsafe characters.

    Returns:
        Sanitised filename.
    """
    sanitized = _UNSAFE_CHARS.sub(replacement, name)
    # Strip leading/trailing dots and spaces (Windows restriction)
    sanitized = sanitized.strip(". ")
    return sanitized or "unnamed"


def add_prefix(entries: list[FileEntry], prefix: str) -> RenamePlan:
    """Create a plan that adds a prefix to each filename.

    Args:
        entries: Files to rename.
        prefix: Prefix to prepend.
    """
    actions = []
    for entry in entries:
        if entry.is_dir:
            continue
        new_name = prefix + entry.name
        actions.append(RenameAction(source=entry.path, destination=entry.path.parent / new_name))
    return RenamePlan(actions=actions)


def add_suffix(entries: list[FileEntry], suffix: str) -> RenamePlan:
    """Create a plan that adds a suffix before the extension.

    Args:
        entries: Files to rename.
        suffix: Suffix to append before the extension.
    """
    actions = []
    for entry in entries:
        if entry.is_dir:
            continue
        stem = entry.path.stem
        ext = entry.suffix
        new_name = f"{stem}{suffix}{ext}"
        actions.append(RenameAction(source=entry.path, destination=entry.path.parent / new_name))
    return RenamePlan(actions=actions)


def replace_text(
    entries: list[FileEntry],
    old: str,
    new: str,
    *,
    case_sensitive: bool = True,
) -> RenamePlan:
    """Create a plan that replaces text in filenames.

    Args:
        entries: Files to rename.
        old: Text to find.
        new: Replacement text.
        case_sensitive: Whether the search is case-sensitive.
    """
    actions = []
    for entry in entries:
        if entry.is_dir:
            continue
        name = entry.name
        if case_sensitive:
            new_name = name.replace(old, new)
        else:
            new_name = re.sub(re.escape(old), new, name, flags=re.IGNORECASE)
        if new_name != name:
            actions.append(
                RenameAction(source=entry.path, destination=entry.path.parent / new_name)
            )
    return RenamePlan(actions=actions)


def regex_replace(entries: list[FileEntry], pattern: str, replacement: str) -> RenamePlan:
    """Create a plan using regex substitution on filenames.

    Args:
        entries: Files to rename.
        pattern: Regular expression pattern.
        replacement: Replacement string (may include backreferences).
    """
    compiled = re.compile(pattern)
    actions = []
    for entry in entries:
        if entry.is_dir:
            continue
        new_name = compiled.sub(replacement, entry.name)
        if new_name != entry.name:
            actions.append(
                RenameAction(source=entry.path, destination=entry.path.parent / new_name)
            )
    return RenamePlan(actions=actions)


def strip_text(
    entries: list[FileEntry],
    text: str,
    *,
    position: str = "any",
    case_sensitive: bool = True,
) -> RenamePlan:
    """Create a plan that strips text from filenames.

    A convenience wrapper around pattern-based removal, targeting common cases
    like stripping prefixes (``Screenshot_``), suffixes (``_edited``), or any
    occurrence of a substring.

    Args:
        entries: Files to rename.
        text: Text to remove.
        position: Where to match — ``"prefix"`` (start of name),
            ``"suffix"`` (end of stem, before extension), or ``"any"``
            (all occurrences anywhere in the name).  Default ``"any"``.
        case_sensitive: Whether the match is case-sensitive (default True).
    """
    flags = 0 if case_sensitive else re.IGNORECASE

    actions = []
    for entry in entries:
        if entry.is_dir:
            continue

        name = entry.name

        if position == "prefix":
            # Strip from start of filename
            pattern = re.compile(r"^" + re.escape(text), flags)
            new_name = pattern.sub("", name, count=1)
        elif position == "suffix":
            # Strip from end of stem (before extension)
            stem = entry.path.stem
            ext = entry.suffix
            pattern = re.compile(re.escape(text) + r"$", flags)
            new_stem = pattern.sub("", stem, count=1)
            new_name = new_stem + ext
        else:
            # Strip all occurrences anywhere in filename
            pattern = re.compile(re.escape(text), flags)
            new_name = pattern.sub("", name)

        if new_name != name and new_name:
            actions.append(
                RenameAction(source=entry.path, destination=entry.path.parent / new_name)
            )

    return RenamePlan(actions=actions)


def sequential_name(
    entries: list[FileEntry],
    template: str = "{counter}{ext}",
    start: int = 1,
    pad: int = 3,
) -> RenamePlan:
    """Create a plan that renames files with sequential numbers.

    Args:
        entries: Files to rename.
        template: Template with ``{counter}`` and ``{ext}`` placeholders.
        start: Starting number.
        pad: Zero-padding width.
    """
    actions = []
    counter = start
    for entry in entries:
        if entry.is_dir:
            continue
        new_name = template.format(
            counter=str(counter).zfill(pad),
            ext=entry.suffix,
            name=entry.path.stem,
        )
        actions.append(RenameAction(source=entry.path, destination=entry.path.parent / new_name))
        counter += 1
    return RenamePlan(actions=actions)
