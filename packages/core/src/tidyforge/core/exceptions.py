"""Shared exception hierarchy for TidyForge."""

from __future__ import annotations


class TidyForgeError(Exception):
    """Base exception for all TidyForge errors."""


class ScanError(TidyForgeError):
    """Raised when a filesystem scan encounters a fatal error."""


class MetadataError(TidyForgeError):
    """Raised when metadata extraction fails."""


class RenameError(TidyForgeError):
    """Raised when a rename operation fails."""


class CollisionError(RenameError):
    """Raised when a rename would overwrite an existing file."""
