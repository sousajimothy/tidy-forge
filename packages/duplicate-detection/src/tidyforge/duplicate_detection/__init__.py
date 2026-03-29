"""TidyForge Duplicate Detection - hash-based duplicate file finding."""

from tidyforge.duplicate_detection.hashing import (
    DuplicateGroup,
    DuplicateReport,
    find_duplicates,
    hash_file,
)

__all__ = [
    "DuplicateGroup",
    "DuplicateReport",
    "find_duplicates",
    "hash_file",
]
