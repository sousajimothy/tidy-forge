# TidyForge

A Python monorepo of desktop/PC housekeeping and file-management tools.

## Tools

| App | Description | Command |
|-----|-------------|---------|
| **media-curator** | Organise photos and videos by metadata, dates, extensions, and folder structure | `uv run media-curator` |
| **disk-atlas** | Analyse disk usage - largest files, folders, and file type distribution | `uv run disk-atlas` |
| **rename-studio** | Batch rename files with templates, regex, and collision detection | `uv run rename-studio` |
| **control-center** | Unified launcher for all TidyForge tools | `uv run tidyforge` |

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (`pip install uv` or see install docs)

### Setup

```bash
# Clone the repo
git clone <repo-url> tidy-forge
cd tidy-forge

# Install all dependencies (creates .venv automatically)
uv sync

# Verify everything works
uv run pytest
```

### Running the Tools

```bash
# Scan a folder for media files and group by date
uv run media-curator scan ~/Pictures
uv run media-curator group ~/Pictures --by date

# Analyse disk usage
uv run disk-atlas scan C:\Users
uv run disk-atlas scan ~/Documents --top 20

# Preview a batch rename (dry-run by default)
uv run rename-studio preview ./photos --template "{date}_{name}{ext}"
uv run rename-studio prefix ./downloads --prefix "2024_"

# Use the unified launcher
uv run tidyforge media scan ~/Pictures
uv run tidyforge disk scan C:\Users
uv run tidyforge rename preview ./photos --template "{date}_{name}{ext}"
```

## Project Structure

```
tidy-forge/
  pyproject.toml              # Workspace root (uv workspace config + shared tool settings)
  apps/
    media-curator/             # Photo/video organisation tool
    disk-atlas/                # Disk usage analysis tool
    rename-studio/             # Batch rename tool
    control-center/            # Unified CLI launcher
  packages/
    core/                      # Shared settings, logging, exceptions, models
    fs-indexer/                # Filesystem scanning and filtering
    metadata/                  # File and media metadata extraction
    media-grouping/            # Grouping strategies for media files
    duplicate-detection/       # Hash-based duplicate finding
    rename-engine/             # Rename planning, templates, collision detection
    job-runner/                # Job lifecycle and progress tracking
    ui-common/                 # Console output helpers (Rich-based)
  tests/
    packages/                  # Tests for shared packages
    apps/                      # CLI smoke tests for apps
  docs/                        # Architecture, decisions, roadmap
  data/
    fixtures/                  # Test fixtures
    samples/                   # Sample data for development
    tmp/                       # Temporary working directory (gitignored)
  infra/                       # CI, scripts, packaging
```

## Development

### Common Commands

```bash
# Run all tests
uv run pytest

# Run tests for a specific area
uv run pytest tests/packages/test_fs_indexer.py
uv run pytest tests/apps/test_media_curator_cli.py

# Run tests with coverage
uv run pytest --cov

# Lint and format
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy packages/ apps/
```

### Package Imports

Shared packages use the `tidyforge` namespace:

```python
from tidyforge.core import FileEntry, TidyForgeSettings
from tidyforge.fs_indexer import scan_directory
from tidyforge.metadata import categorize_file
from tidyforge.rename_engine import RenamePlan
```

### Adding Dependencies

```bash
# Add a dependency to a specific package
uv add --package tidyforge-core some-library

# Add a dev dependency to the workspace root
uv add --dev some-dev-tool
```

## Architecture

All file-mutating operations follow a **plan-preview-execute** model:

1. **Plan** - Generate a manifest of intended actions
2. **Preview** - Display the plan for user review (dry-run, the default)
3. **Execute** - Apply changes only with explicit confirmation
4. **Log** - Record all actions to a manifest file

This ensures safety by default. No tool will modify files without preview.

## Tech Stack

- **Python 3.11+** with type hints throughout
- **uv** for dependency management and workspaces
- **Typer** for CLI interfaces
- **Pydantic** for data models and settings
- **Rich** for terminal output
- **pytest** for testing
- **ruff** for linting and formatting

## License

Apache-2.0

See [LICENSE](LICENSE) for the full license text and [NOTICE](NOTICE) for attribution notices preserved under Apache-2.0.
