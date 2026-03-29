"""TidyForge Metadata - filesystem and media metadata extraction."""

from tidyforge.metadata.categories import CATEGORY_MAP, categorize_file, get_extensions_for_category
from tidyforge.metadata.fs_metadata import extract_fs_metadata
from tidyforge.metadata.media import extract_media_metadata

__all__ = [
    "CATEGORY_MAP",
    "categorize_file",
    "extract_fs_metadata",
    "extract_media_metadata",
    "get_extensions_for_category",
]
