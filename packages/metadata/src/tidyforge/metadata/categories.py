"""File extension categorisation."""

from __future__ import annotations

from pathlib import Path

CATEGORY_MAP: dict[str, str] = {
    # Images
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".gif": "image",
    ".bmp": "image",
    ".tiff": "image",
    ".tif": "image",
    ".webp": "image",
    ".svg": "image",
    ".ico": "image",
    ".heic": "image",
    ".heif": "image",
    ".raw": "image",
    ".cr2": "image",
    ".nef": "image",
    ".arw": "image",
    # Video
    ".mp4": "video",
    ".avi": "video",
    ".mkv": "video",
    ".mov": "video",
    ".wmv": "video",
    ".flv": "video",
    ".webm": "video",
    ".m4v": "video",
    ".mpg": "video",
    ".mpeg": "video",
    ".3gp": "video",
    # Audio
    ".mp3": "audio",
    ".wav": "audio",
    ".flac": "audio",
    ".aac": "audio",
    ".ogg": "audio",
    ".wma": "audio",
    ".m4a": "audio",
    ".opus": "audio",
    # Documents
    ".pdf": "document",
    ".doc": "document",
    ".docx": "document",
    ".xls": "document",
    ".xlsx": "document",
    ".ppt": "document",
    ".pptx": "document",
    ".odt": "document",
    ".ods": "document",
    ".odp": "document",
    ".rtf": "document",
    ".txt": "document",
    ".md": "document",
    ".csv": "document",
    ".tsv": "document",
    # Archives
    ".zip": "archive",
    ".rar": "archive",
    ".7z": "archive",
    ".tar": "archive",
    ".gz": "archive",
    ".bz2": "archive",
    ".xz": "archive",
    ".iso": "archive",
    # Code
    ".py": "code",
    ".js": "code",
    ".ts": "code",
    ".java": "code",
    ".c": "code",
    ".cpp": "code",
    ".h": "code",
    ".cs": "code",
    ".go": "code",
    ".rs": "code",
    ".rb": "code",
    ".php": "code",
    ".html": "code",
    ".css": "code",
    ".sql": "code",
    ".sh": "code",
    ".bat": "code",
    ".ps1": "code",
    ".json": "data",
    ".xml": "data",
    ".yaml": "data",
    ".yml": "data",
    ".toml": "data",
    ".ini": "data",
    # Executables
    ".exe": "executable",
    ".msi": "executable",
    ".dll": "executable",
    ".so": "executable",
    ".app": "executable",
}

_REVERSE_MAP: dict[str, set[str]] = {}


def _build_reverse_map() -> None:
    if _REVERSE_MAP:
        return
    for ext, cat in CATEGORY_MAP.items():
        _REVERSE_MAP.setdefault(cat, set()).add(ext)


def categorize_file(path: Path) -> str:
    """Return the category for a file based on its extension.

    Args:
        path: File path.

    Returns:
        Category string (e.g. ``"image"``, ``"video"``). Returns ``"other"``
        for unrecognised extensions.
    """
    return CATEGORY_MAP.get(path.suffix.lower(), "other")


def get_extensions_for_category(category: str) -> set[str]:
    """Return all known extensions for a category.

    Args:
        category: Category name (e.g. ``"image"``).

    Returns:
        Set of extensions including the leading dot.
    """
    _build_reverse_map()
    return _REVERSE_MAP.get(category, set())
