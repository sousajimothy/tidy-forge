"""TidyForge Rename Engine - rename planning, templates, and collision detection."""

from tidyforge.rename_engine.operations import (
    add_prefix,
    add_suffix,
    regex_replace,
    replace_text,
    sanitize_filename,
    sequential_name,
    strip_text,
)
from tidyforge.rename_engine.plan import RenameAction, RenamePlan
from tidyforge.rename_engine.templates import TemplateRenderer, build_plan_from_template

__all__ = [
    "RenameAction",
    "RenamePlan",
    "TemplateRenderer",
    "add_prefix",
    "add_suffix",
    "build_plan_from_template",
    "regex_replace",
    "replace_text",
    "sanitize_filename",
    "sequential_name",
    "strip_text",
]
