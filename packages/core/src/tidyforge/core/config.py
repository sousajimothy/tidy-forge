"""Application settings powered by pydantic-settings."""

from __future__ import annotations

import functools
from pathlib import Path

from pydantic_settings import BaseSettings


class TidyForgeSettings(BaseSettings):
    """Global TidyForge configuration.

    Settings are loaded from environment variables prefixed with ``TIDYFORGE_``.
    For example, ``TIDYFORGE_LOG_LEVEL=DEBUG`` sets ``log_level`` to ``"DEBUG"``.
    """

    model_config = {"env_prefix": "TIDYFORGE_"}

    log_level: str = "INFO"
    data_dir: Path = Path("./data")
    dry_run: bool = True


@functools.lru_cache(maxsize=1)
def get_settings() -> TidyForgeSettings:
    """Return the cached global settings instance."""
    return TidyForgeSettings()
