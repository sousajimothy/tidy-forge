"""Rename operations: prefix, suffix, replace, regex, case, extension, and more."""

from __future__ import annotations

import re
from collections import defaultdict

from tidyforge.core.models import FileEntry
from tidyforge.rename_engine.plan import RenameAction, RenamePlan

# Characters not allowed in filenames on Windows
_UNSAFE_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


def _apply_case(text: str, case: str) -> str:
    """Apply a case transformation to *text*."""
    if case == "upper":
        return text.upper()
    if case == "lower":
        return text.lower()
    if case == "title":
        return text.title()
    if case == "sentence":
        return text[:1].upper() + text[1:].lower() if text else text
    return text


def _format_counter(value: int, pad: int, base: int) -> str:
    """Format *value* with zero-padding in the given number *base*."""
    if base == 16:
        return f"{value:0{pad}x}"
    if base == 8:
        return f"{value:0{pad}o}"
    if base == 2:
        return f"{value:0{pad}b}"
    return str(value).zfill(pad)


# ---------------------------------------------------------------------------
# Batch 1 — core operations (existing, extended)
# ---------------------------------------------------------------------------


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
    first_only: bool = False,
) -> RenamePlan:
    """Create a plan that replaces text in filenames.

    Args:
        entries: Files to rename.
        old: Text to find.
        new: Replacement text.
        case_sensitive: Whether the search is case-sensitive.
        first_only: Replace only the first occurrence when True.
    """
    actions = []
    for entry in entries:
        if entry.is_dir:
            continue
        name = entry.name
        if case_sensitive:
            new_name = name.replace(old, new, 1) if first_only else name.replace(old, new)
        else:
            count = 1 if first_only else 0
            new_name = re.sub(re.escape(old), new, name, count=count, flags=re.IGNORECASE)
        if new_name != name:
            actions.append(
                RenameAction(source=entry.path, destination=entry.path.parent / new_name)
            )
    return RenamePlan(actions=actions)


def regex_replace(
    entries: list[FileEntry],
    pattern: str,
    replacement: str,
    *,
    include_ext: bool = True,
) -> RenamePlan:
    """Create a plan using regex substitution on filenames.

    Args:
        entries: Files to rename.
        pattern: Regular expression pattern.
        replacement: Replacement string (may include backreferences).
        include_ext: Apply regex to full name (True) or stem only (False).
    """
    compiled = re.compile(pattern)
    actions = []
    for entry in entries:
        if entry.is_dir:
            continue
        if include_ext:
            new_name = compiled.sub(replacement, entry.name)
        else:
            new_stem = compiled.sub(replacement, entry.path.stem)
            new_name = new_stem + entry.suffix
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

    Args:
        entries: Files to rename.
        text: Text to remove.
        position: ``"prefix"``, ``"suffix"`` (before ext), or ``"any"``.
        case_sensitive: Whether the match is case-sensitive (default True).
    """
    flags = 0 if case_sensitive else re.IGNORECASE

    actions = []
    for entry in entries:
        if entry.is_dir:
            continue

        name = entry.name

        if position == "prefix":
            pat = re.compile(r"^" + re.escape(text), flags)
            new_name = pat.sub("", name, count=1)
        elif position == "suffix":
            stem = entry.path.stem
            ext = entry.suffix
            pat = re.compile(re.escape(text) + r"$", flags)
            new_stem = pat.sub("", stem, count=1)
            new_name = new_stem + ext
        else:
            pat = re.compile(re.escape(text), flags)
            new_name = pat.sub("", name)

        if new_name != name and new_name:
            actions.append(
                RenameAction(source=entry.path, destination=entry.path.parent / new_name)
            )

    return RenamePlan(actions=actions)


# ---------------------------------------------------------------------------
# Batch 1 — new operations: case, extension
# ---------------------------------------------------------------------------


def change_case(
    entries: list[FileEntry],
    case: str = "lower",
    *,
    scope: str = "stem",
) -> RenamePlan:
    """Change the case of filenames.

    Args:
        entries: Files to rename.
        case: ``"upper"``, ``"lower"``, ``"title"``, or ``"sentence"``.
        scope: ``"stem"`` (default), ``"ext"``, or ``"both"``.
    """
    actions = []
    for entry in entries:
        if entry.is_dir:
            continue
        stem = entry.path.stem
        ext = entry.path.suffix  # original case from filesystem

        new_stem = _apply_case(stem, case) if scope in ("stem", "both") else stem
        new_ext = _apply_case(ext, case) if scope in ("ext", "both") else ext
        new_name = new_stem + new_ext

        if new_name != entry.name:
            actions.append(
                RenameAction(source=entry.path, destination=entry.path.parent / new_name)
            )
    return RenamePlan(actions=actions)


def change_extension(
    entries: list[FileEntry],
    mode: str = "lower",
    *,
    new_ext: str = "",
) -> RenamePlan:
    """Change file extensions.

    Args:
        entries: Files to rename.
        mode: ``"lower"``, ``"upper"``, ``"title"``, ``"fixed"``,
            ``"extra"``, or ``"remove"``.
        new_ext: Extension for ``"fixed"`` and ``"extra"`` modes
            (include the dot, e.g. ``".bak"``).
    """
    actions = []
    for entry in entries:
        if entry.is_dir:
            continue
        stem = entry.path.stem
        ext = entry.path.suffix  # original case from filesystem

        if mode == "fixed":
            result_ext = new_ext
        elif mode == "extra":
            result_ext = ext + new_ext
        elif mode == "remove":
            result_ext = ""
        elif mode == "upper":
            result_ext = ext.upper()
        elif mode == "title":
            result_ext = ext.title()
        else:  # "lower" (default)
            result_ext = ext.lower()

        new_name = stem + result_ext
        if new_name != entry.name and new_name:
            actions.append(
                RenameAction(source=entry.path, destination=entry.path.parent / new_name)
            )
    return RenamePlan(actions=actions)


# ---------------------------------------------------------------------------
# Batch 2 — character manipulation
# ---------------------------------------------------------------------------


def remove_chars(
    entries: list[FileEntry],
    *,
    first_n: int = 0,
    last_n: int = 0,
    from_pos: int | None = None,
    to_pos: int | None = None,
    crop_before: str | None = None,
    crop_after: str | None = None,
) -> RenamePlan:
    """Remove characters from the filename stem.

    Args:
        entries: Files to rename.
        first_n: Remove first N characters.
        last_n: Remove last N characters.
        from_pos: Remove from this 0-based position …
        to_pos: … up to (but not including) this position.
        crop_before: Keep only text *after* the first occurrence of this string.
        crop_after: Keep only text *before* the first occurrence of this string.
    """
    actions = []
    for entry in entries:
        if entry.is_dir:
            continue
        stem = entry.path.stem
        ext = entry.suffix

        if crop_before is not None:
            idx = stem.find(crop_before)
            new_stem = stem[idx + len(crop_before) :] if idx != -1 else stem
        elif crop_after is not None:
            idx = stem.find(crop_after)
            new_stem = stem[:idx] if idx != -1 else stem
        elif from_pos is not None and to_pos is not None:
            f = max(0, min(from_pos, len(stem)))
            t = max(f, min(to_pos, len(stem)))
            new_stem = stem[:f] + stem[t:]
        else:
            new_stem = stem
            if first_n > 0:
                new_stem = new_stem[min(first_n, len(new_stem)) :]
            if last_n > 0:
                cut = min(last_n, len(new_stem))
                new_stem = new_stem[: len(new_stem) - cut] if cut else new_stem

        new_name = new_stem + ext
        if new_name != entry.name and new_stem:
            actions.append(
                RenameAction(source=entry.path, destination=entry.path.parent / new_name)
            )
    return RenamePlan(actions=actions)


def insert_at(
    entries: list[FileEntry],
    text: str,
    position: int,
) -> RenamePlan:
    """Insert text at a character position in the filename stem.

    Args:
        entries: Files to rename.
        text: Text to insert.
        position: 0-based index (negative counts from end). Clamped to valid range.
    """
    actions = []
    for entry in entries:
        if entry.is_dir:
            continue
        stem = entry.path.stem
        ext = entry.suffix

        # Clamp position
        pos = max(0, len(stem) + position) if position < 0 else min(position, len(stem))

        new_stem = stem[:pos] + text + stem[pos:]
        new_name = new_stem + ext
        if new_name != entry.name:
            actions.append(
                RenameAction(source=entry.path, destination=entry.path.parent / new_name)
            )
    return RenamePlan(actions=actions)


# ---------------------------------------------------------------------------
# Batch 3 — date, folder name, enhanced numbering
# ---------------------------------------------------------------------------


def auto_date(
    entries: list[FileEntry],
    *,
    date_source: str = "modified",
    fmt: str = "%Y-%m-%d",
    position: str = "prefix",
    separator: str = "_",
) -> RenamePlan:
    """Add a formatted date to filenames.

    Args:
        entries: Files to rename.
        date_source: ``"modified"`` (default) or ``"created"``. For
            ``"created"`` the caller should populate ``entry.metadata``
            with a ``"created"`` key; falls back to ``entry.modified``.
        fmt: :meth:`~datetime.datetime.strftime` format string.
        position: ``"prefix"`` or ``"suffix"``.
        separator: Text placed between the date and the original name.
    """
    actions = []
    for entry in entries:
        if entry.is_dir:
            continue
        stem = entry.path.stem
        ext = entry.suffix

        if date_source == "created":
            dt = entry.metadata.get("created", entry.modified)
        else:
            dt = entry.modified

        date_str = dt.strftime(fmt)

        if position == "suffix":
            new_stem = stem + separator + date_str
        else:
            new_stem = date_str + separator + stem

        new_name = new_stem + ext
        if new_name != entry.name:
            actions.append(
                RenameAction(source=entry.path, destination=entry.path.parent / new_name)
            )
    return RenamePlan(actions=actions)


def append_folder_name(
    entries: list[FileEntry],
    *,
    position: str = "prefix",
    separator: str = "_",
    levels: int = 1,
) -> RenamePlan:
    """Prepend or append parent folder name(s) to filenames.

    Args:
        entries: Files to rename.
        position: ``"prefix"`` or ``"suffix"``.
        separator: Separator between folder name and filename.
        levels: Number of parent levels (1 = immediate parent).
    """
    actions = []
    for entry in entries:
        if entry.is_dir:
            continue
        stem = entry.path.stem
        ext = entry.suffix

        parts = []
        p = entry.path.parent
        for _ in range(levels):
            parts.append(p.name)
            p = p.parent
        folder_str = separator.join(reversed(parts))

        if position == "suffix":
            new_stem = stem + separator + folder_str
        else:
            new_stem = folder_str + separator + stem

        new_name = new_stem + ext
        if new_name != entry.name:
            actions.append(
                RenameAction(source=entry.path, destination=entry.path.parent / new_name)
            )
    return RenamePlan(actions=actions)


def sequential_name(
    entries: list[FileEntry],
    template: str = "{counter}{ext}",
    start: int = 1,
    pad: int = 3,
    *,
    increment: int = 1,
    base: int = 10,
    separator: str = "",
    position: str = "replace",
    reset_per_folder: bool = False,
) -> RenamePlan:
    """Create a plan that renames files with sequential numbers.

    Args:
        entries: Files to rename.
        template: Template with ``{counter}``, ``{ext}``, ``{name}`` placeholders.
            Only used when *position* is ``"replace"`` (default).
        start: Starting number.
        pad: Zero-padding width.
        increment: Step between numbers.
        base: Number base (10=decimal, 16=hex, 8=octal, 2=binary).
        separator: Text between the counter and the original name
            (used in ``"prefix"``/``"suffix"`` modes).
        position: ``"replace"`` (default), ``"prefix"``, or ``"suffix"``.
        reset_per_folder: Reset counter to *start* for each parent folder.
    """
    if reset_per_folder:
        folder_counters: dict[str, int] = defaultdict(lambda: start)
    else:
        global_counter = start

    actions = []
    for entry in entries:
        if entry.is_dir:
            continue

        if reset_per_folder:
            folder_key = str(entry.path.parent)
            counter = folder_counters[folder_key]
            folder_counters[folder_key] = counter + increment
        else:
            counter = global_counter
            global_counter += increment

        counter_str = _format_counter(counter, pad, base)

        if position == "prefix":
            new_name = counter_str + separator + entry.path.stem + entry.suffix
        elif position == "suffix":
            new_name = entry.path.stem + separator + counter_str + entry.suffix
        else:
            new_name = template.format(
                counter=counter_str,
                ext=entry.suffix,
                name=entry.path.stem,
            )

        actions.append(
            RenameAction(source=entry.path, destination=entry.path.parent / new_name)
        )
    return RenamePlan(actions=actions)


# ---------------------------------------------------------------------------
# Batch 4 — name manipulation, word spacing
# ---------------------------------------------------------------------------


def change_name(
    entries: list[FileEntry],
    mode: str,
    *,
    fixed_name: str = "",
) -> RenamePlan:
    """Manipulate the filename stem.

    Args:
        entries: Files to rename.
        mode: ``"fixed"`` (replace stem), ``"reverse"``, or ``"remove"``.
        fixed_name: New stem when *mode* is ``"fixed"``.
    """
    actions = []
    for entry in entries:
        if entry.is_dir:
            continue
        ext = entry.suffix

        if mode == "fixed":
            new_stem = fixed_name
        elif mode == "reverse":
            new_stem = entry.path.stem[::-1]
        elif mode == "remove":
            new_stem = ""
        else:
            continue

        new_name = new_stem + ext
        if new_name != entry.name and new_stem:
            actions.append(
                RenameAction(source=entry.path, destination=entry.path.parent / new_name)
            )
    return RenamePlan(actions=actions)


def word_space(
    entries: list[FileEntry],
    *,
    separator: str = " ",
) -> RenamePlan:
    """Insert separators between words in filenames.

    Splits on camelCase boundaries, underscores, and hyphens.

    Args:
        entries: Files to rename.
        separator: Character to insert between words (default: space).
    """
    # Insert separator before uppercase letter preceded by lowercase
    _camel_re = re.compile(r"(?<=[a-z])(?=[A-Z])")
    # Replace existing underscores and hyphens
    _delim_re = re.compile(r"[_\-]+")

    actions = []
    for entry in entries:
        if entry.is_dir:
            continue
        stem = entry.path.stem
        ext = entry.suffix

        new_stem = _camel_re.sub(separator, stem)
        new_stem = _delim_re.sub(separator, new_stem)
        new_name = new_stem + ext

        if new_name != entry.name:
            actions.append(
                RenameAction(source=entry.path, destination=entry.path.parent / new_name)
            )
    return RenamePlan(actions=actions)
