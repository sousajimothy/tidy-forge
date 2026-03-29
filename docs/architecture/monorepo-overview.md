# Monorepo Overview

## Workspace Structure

TidyForge uses **uv workspaces** with **hatchling** as the build backend. The root `pyproject.toml` is a virtual workspace (no `[project]` table) that defines all workspace members.

```
tidy-forge/
  pyproject.toml          # Virtual workspace root
  packages/               # Shared libraries (tidyforge.* namespace)
  apps/                   # User-facing applications
```

## Namespace Strategy

Shared packages use **implicit namespace packages** under the `tidyforge` namespace:

```python
from tidyforge.core import FileEntry
from tidyforge.fs_indexer import scan_directory
from tidyforge.metadata import categorize_file
```

This works because there is **no `__init__.py`** in any `src/tidyforge/` directory. Only the sub-packages (e.g., `src/tidyforge/core/__init__.py`) have init files.

Apps use their own top-level package names:

```python
from media_curator.cli import app
from disk_atlas.cli import app
```

## Dependency Graph

```
core (pydantic, pydantic-settings, rich)
  |
  +-- fs-indexer
  +-- metadata (optional: pillow)
  +-- rename-engine
  +-- job-runner
  +-- ui-common (rich)
  +-- media-grouping --> fs-indexer, metadata
  +-- duplicate-detection --> fs-indexer
```

Apps depend on the shared packages they need:

- **media-curator**: core, fs-indexer, metadata, media-grouping, duplicate-detection, ui-common
- **disk-atlas**: core, fs-indexer, ui-common
- **rename-studio**: core, fs-indexer, rename-engine, ui-common
- **control-center**: all three apps above

## How Workspace Dependencies Work

Each package declares its workspace dependencies in two places:

1. `[project] dependencies` - lists the package name
2. `[tool.uv.sources]` - maps the name to `{ workspace = true }`

Example from `packages/fs-indexer/pyproject.toml`:

```toml
[project]
dependencies = ["tidyforge-core"]

[tool.uv.sources]
tidyforge-core = { workspace = true }
```

## Shared Tool Configuration

Ruff, pytest, and mypy are configured once in the root `pyproject.toml` and apply to the entire workspace. This prevents configuration drift between packages.
