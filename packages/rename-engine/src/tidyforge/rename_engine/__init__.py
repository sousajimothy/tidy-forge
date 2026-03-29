"""TidyForge Rename Engine - rename planning, templates, and collision detection."""

from tidyforge.rename_engine.operations import (
    add_prefix,
    add_suffix,
    append_folder_name,
    auto_date,
    change_case,
    change_extension,
    change_name,
    insert_at,
    regex_replace,
    remove_chars,
    replace_text,
    sanitize_filename,
    sequential_name,
    strip_text,
    word_space,
)
from tidyforge.rename_engine.plan import RenameAction, RenamePlan
from tidyforge.rename_engine.templates import TemplateRenderer, build_plan_from_template

__all__ = [
    "RenameAction",
    "RenamePlan",
    "TemplateRenderer",
    "add_prefix",
    "add_suffix",
    "append_folder_name",
    "auto_date",
    "build_plan_from_template",
    "change_case",
    "change_extension",
    "change_name",
    "insert_at",
    "regex_replace",
    "remove_chars",
    "replace_text",
    "sanitize_filename",
    "sequential_name",
    "strip_text",
    "word_space",
]
