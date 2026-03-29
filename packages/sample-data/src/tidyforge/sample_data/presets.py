"""Per-notebook preset file specifications."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from tidyforge.sample_data.generator import generate_files
from tidyforge.sample_data.specs import JPEG_MAGIC, PNG_MAGIC, FileSpec

# ---------------------------------------------------------------------------
# rename_playground.ipynb — all 13 rename operations
# ---------------------------------------------------------------------------


def rename_playground_specs() -> list[FileSpec]:
    """Return file specs that exercise all 13 rename operations.

    The returned list contains ~40 files with patterns suited to every
    operation demonstrated in ``notebooks/rename_playground.ipynb``.
    """
    now = datetime(2024, 3, 15, 10, 30, 0, tzinfo=UTC)
    week_ago = datetime(2024, 3, 8, 14, 0, 0, tzinfo=UTC)

    return [
        # --- replace_text: IMG_ prefix files ---
        FileSpec(name="IMG_001.jpg", content=JPEG_MAGIC, mtime=now),
        FileSpec(name="IMG_002.png", content=PNG_MAGIC, mtime=week_ago),
        FileSpec(name="IMG_003.jpg", content=JPEG_MAGIC, mtime=now),
        # --- regex_replace: IMG_YYYYMMDD_NNN pattern ---
        FileSpec(name="IMG_20240315_001.jpg", content=JPEG_MAGIC, mtime=now),
        FileSpec(name="IMG_20240308_002.jpg", content=JPEG_MAGIC, mtime=week_ago),
        FileSpec(name="IMG_20240301_003.jpg", content=JPEG_MAGIC),
        # --- strip_text: Screenshot_, SmartSelect_, IMG- prefixes ---
        FileSpec(name="Screenshot_20260329_094302_Reddit.png", content=PNG_MAGIC),
        FileSpec(name="Screenshot_20260201_181839_Firefox.png", content=PNG_MAGIC),
        FileSpec(name="SmartSelect_20260115_photo.jpg", content=JPEG_MAGIC),
        FileSpec(name="IMG-20240315-vacation.jpg", content=JPEG_MAGIC),
        # --- change_case: mixed case files ---
        FileSpec(name="PHOTO.JPG", content=JPEG_MAGIC),
        FileSpec(name="Photo.Jpg", content=JPEG_MAGIC),
        FileSpec(name="hello world.txt"),
        FileSpec(name="VACATION PICS.PNG", content=PNG_MAGIC),
        # --- change_extension: various extension cases ---
        FileSpec(name="sunset.JPG", content=JPEG_MAGIC),
        FileSpec(name="portrait.Jpg", content=JPEG_MAGIC),
        FileSpec(name="landscape.png", content=PNG_MAGIC),
        FileSpec(name="notes.TXT"),
        # --- remove_chars: files with removable prefixes/positions ---
        FileSpec(name="Screenshot_001.png", content=PNG_MAGIC),
        FileSpec(name="prefix_keepme.txt"),
        # --- insert_at: simple stems ---
        FileSpec(name="photo.jpg", content=JPEG_MAGIC, mtime=now),
        FileSpec(name="sunset.png", content=PNG_MAGIC, mtime=week_ago),
        # --- add_prefix / add_suffix: generic files ---
        FileSpec(name="document.pdf"),
        FileSpec(name="report.docx"),
        # --- auto_date: files with distinct modification times ---
        FileSpec(
            name="birthday.jpg",
            content=JPEG_MAGIC,
            mtime=datetime(2024, 6, 15, 14, 30, tzinfo=UTC),
        ),
        FileSpec(
            name="graduation.png",
            content=PNG_MAGIC,
            mtime=datetime(2023, 12, 20, 10, 0, tzinfo=UTC),
        ),
        # --- append_folder_name: files in named subdirectories ---
        FileSpec(name="beach.jpg", content=JPEG_MAGIC, subdir="Vacation"),
        FileSpec(name="tower.jpg", content=JPEG_MAGIC, subdir="Vacation"),
        FileSpec(name="dinner.jpg", content=JPEG_MAGIC, subdir="Food"),
        FileSpec(name="cake.jpg", content=JPEG_MAGIC, subdir="Food"),
        # --- sequential_name: multiple files for numbering ---
        FileSpec(name="batch_a.txt"),
        FileSpec(name="batch_b.txt"),
        FileSpec(name="batch_c.txt"),
        FileSpec(name="batch_d.txt"),
        FileSpec(name="batch_e.txt"),
        # --- change_name: reversible / replaceable stems ---
        FileSpec(name="abc.txt"),
        FileSpec(name="MyPhoto.jpg", content=JPEG_MAGIC),
        # --- word_space: camelCase, underscored, hyphenated ---
        FileSpec(name="MyFileName.txt"),
        FileSpec(name="my_file_name.txt"),
        FileSpec(name="my-file-name.txt"),
        FileSpec(name="AnotherCamelCase.jpg", content=JPEG_MAGIC),
    ]


def create_rename_playground_samples(
    target: Path,
    *,
    clean: bool = True,
) -> list[Path]:
    """Generate all sample files for the rename playground notebook.

    Args:
        target: Directory where files will be created.
        clean: Remove existing contents of *target* first (default ``True``).

    Returns:
        List of paths to created files.
    """
    return generate_files(target, rename_playground_specs(), clean=clean)


# ---------------------------------------------------------------------------
# Future presets (stubs) — to be fleshed out per-notebook as needed
# ---------------------------------------------------------------------------


def rename_strip_specs() -> list[FileSpec]:
    """Return file specs for ``notebooks/rename_strip.ipynb``."""
    raise NotImplementedError("rename_strip_specs will be implemented in a future phase")


def organize_playground_specs() -> list[FileSpec]:
    """Return file specs for ``notebooks/organize_playground.ipynb``."""
    raise NotImplementedError(
        "organize_playground_specs will be implemented in a future phase"
    )


def organize_by_app_specs() -> list[FileSpec]:
    """Return file specs for ``notebooks/organize_by_app.ipynb``."""
    raise NotImplementedError(
        "organize_by_app_specs will be implemented in a future phase"
    )


def scanning_and_filtering_specs() -> list[FileSpec]:
    """Return file specs for ``notebooks/scanning_and_filtering.ipynb``."""
    raise NotImplementedError(
        "scanning_and_filtering_specs will be implemented in a future phase"
    )
