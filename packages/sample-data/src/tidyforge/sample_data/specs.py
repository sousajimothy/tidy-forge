"""File specification model and content constants for sample data generation."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

# Minimal magic bytes for common file types
JPEG_MAGIC = b"\xff\xd8\xff\xe0" + b"\x00" * 4
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


class FileSpec(BaseModel):
    """Specification for a single dummy file to create.

    Attributes:
        name: Filename including extension (e.g. ``"IMG_001.jpg"``).
        size: File size in bytes when ``content`` is not provided.
        content: Exact bytes to write.  Overrides ``size`` when set.
        mtime: Optional modification time to stamp on the file.
        subdir: Optional subdirectory relative to the generation target.
    """

    name: str
    size: int = 8
    content: bytes | None = None
    mtime: datetime | None = None
    subdir: str | None = None
