"""Media metadata extraction (EXIF and image properties)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".webp", ".bmp", ".gif", ".heic"}


def extract_media_metadata(path: Path) -> dict[str, Any]:
    """Extract media metadata from an image file.

    Uses Pillow for EXIF data when available. Returns an empty dict (with a
    warning log) if Pillow is not installed or the file is not a supported
    image format.

    Args:
        path: Path to the image file.

    Returns:
        Dict with keys like date_taken, camera_make, camera_model, width,
        height, orientation. Only keys with available data are included.
    """
    if path.suffix.lower() not in _IMAGE_EXTENSIONS:
        return {}

    try:
        from PIL import Image
        from PIL.ExifTags import TAGS
    except ImportError:
        logger.debug(
            "Pillow not installed; skipping media metadata for %s. "
            "Install with: uv add --package tidyforge-metadata 'tidyforge-metadata[media]'",
            path,
        )
        return {}

    result: dict[str, Any] = {}
    try:
        with Image.open(path) as img:
            result["width"] = img.width
            result["height"] = img.height
            result["format"] = img.format

            exif_data = img.getexif()
            if not exif_data:
                return result

            tag_map = {TAGS.get(k, k): v for k, v in exif_data.items()}

            if "DateTimeOriginal" in tag_map:
                result["date_taken"] = tag_map["DateTimeOriginal"]
            elif "DateTime" in tag_map:
                result["date_taken"] = tag_map["DateTime"]

            if "Make" in tag_map:
                result["camera_make"] = str(tag_map["Make"]).strip()
            if "Model" in tag_map:
                result["camera_model"] = str(tag_map["Model"]).strip()
            if "Orientation" in tag_map:
                result["orientation"] = tag_map["Orientation"]

    except Exception as exc:
        logger.warning("Failed to read media metadata from %s: %s", path, exc)

    return result
