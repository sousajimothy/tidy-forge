"""Template-based rename logic."""

from __future__ import annotations

from pathlib import Path

from tidyforge.core.models import FileEntry
from tidyforge.rename_engine.plan import RenameAction, RenamePlan


class TemplateRenderer:
    """Render filenames from a template string.

    Supported placeholders:
        - ``{name}`` - original filename without extension
        - ``{ext}`` - extension including the dot (e.g. ``.jpg``)
        - ``{date}`` - modification date as ``YYYY-MM-DD``
        - ``{datetime}`` - modification datetime as ``YYYY-MM-DD_HH-MM-SS``
        - ``{counter}`` - sequential counter (zero-padded)
        - ``{parent}`` - immediate parent folder name
        - ``{size}`` - file size in bytes

    Args:
        template: Template string with placeholders.
        counter_start: Starting value for the counter.
        counter_pad: Zero-padding width for the counter.
    """

    def __init__(
        self,
        template: str,
        counter_start: int = 1,
        counter_pad: int = 3,
    ) -> None:
        self.template = template
        self.counter_start = counter_start
        self.counter_pad = counter_pad

    def render(self, entry: FileEntry, counter: int) -> str:
        """Render the template for a single entry.

        Args:
            entry: The file entry to render for.
            counter: Current counter value.

        Returns:
            The rendered filename string.
        """
        stem = entry.path.stem
        ext = entry.suffix
        return self.template.format(
            name=stem,
            ext=ext,
            date=entry.modified.strftime("%Y-%m-%d"),
            datetime=entry.modified.strftime("%Y-%m-%d_%H-%M-%S"),
            counter=str(counter).zfill(self.counter_pad),
            parent=entry.path.parent.name,
            size=str(entry.size),
        )


def build_plan_from_template(
    entries: list[FileEntry],
    template: str,
    dest_dir: Path | None = None,
    counter_start: int = 1,
    counter_pad: int = 3,
) -> RenamePlan:
    """Build a RenamePlan by applying a template to each entry.

    Args:
        entries: Files to rename.
        template: Template string (see TemplateRenderer for placeholders).
        dest_dir: Target directory for renamed files. If None, files stay
            in their original directory.
        counter_start: Starting counter value.
        counter_pad: Counter zero-padding width.

    Returns:
        A RenamePlan with one action per entry.
    """
    renderer = TemplateRenderer(template, counter_start=counter_start, counter_pad=counter_pad)
    actions = []
    for i, entry in enumerate(entries):
        if entry.is_dir:
            continue
        new_name = renderer.render(entry, counter=counter_start + i)
        target_dir = dest_dir if dest_dir else entry.path.parent
        actions.append(RenameAction(source=entry.path, destination=target_dir / new_name))
    return RenamePlan(actions=actions)
