"""TidyForge FS Indexer - filesystem scanning, filtering, and aggregation."""

from tidyforge.fs_indexer.aggregator import (
    DirStats,
    ExtensionStats,
    aggregate_by_directory,
    aggregate_by_extension,
    top_n,
)
from tidyforge.fs_indexer.filters import (
    CompositeFilter,
    ExtensionFilter,
    PatternFilter,
    SizeFilter,
)
from tidyforge.fs_indexer.scanner import scan_directory

__all__ = [
    "CompositeFilter",
    "DirStats",
    "ExtensionFilter",
    "ExtensionStats",
    "PatternFilter",
    "SizeFilter",
    "aggregate_by_directory",
    "aggregate_by_extension",
    "scan_directory",
    "top_n",
]
