"""TidyForge Media Grouping - strategies for organising files into groups."""

from tidyforge.media_grouping.engine import GroupingEngine, GroupSummary
from tidyforge.media_grouping.strategies import (
    ByDate,
    ByExtension,
    ByFilenamePattern,
    ByParentFolder,
    GroupingStrategy,
)

__all__ = [
    "ByDate",
    "ByExtension",
    "ByFilenamePattern",
    "ByParentFolder",
    "GroupingEngine",
    "GroupSummary",
    "GroupingStrategy",
]
