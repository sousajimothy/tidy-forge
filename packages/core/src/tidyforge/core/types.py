"""Common type aliases used across TidyForge."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

PathLike = str | Path
"""A value that can be either a string path or a Path object."""

FilterFunc = Callable[[Path], bool]
"""A function that takes a Path and returns True to include it."""
