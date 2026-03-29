# Naming Conventions

## Directory Names

| Type | Convention | Example |
|------|-----------|---------|
| App directory | kebab-case | `media-curator`, `disk-atlas` |
| Package directory | kebab-case | `fs-indexer`, `ui-common` |

## Python Package Names (PyPI)

| Type | Convention | Example |
|------|-----------|---------|
| Shared package | `tidyforge-{name}` | `tidyforge-core`, `tidyforge-fs-indexer` |
| App package | `tidyforge-{name}` | `tidyforge-media-curator` |

## Python Import Names

| Type | Convention | Example |
|------|-----------|---------|
| Shared package | `tidyforge.{name}` | `tidyforge.core`, `tidyforge.fs_indexer` |
| App module | `{name}` (underscored) | `media_curator`, `disk_atlas` |

## CLI Command Names

| Command | Source |
|---------|--------|
| `media-curator` | `apps/media-curator` |
| `disk-atlas` | `apps/disk-atlas` |
| `rename-studio` | `apps/rename-studio` |
| `tidyforge` | `apps/control-center` |

## Code Style

- **Functions and variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: Leading underscore `_internal_function`
- **Type aliases**: `PascalCase` (e.g., `PathLike`, `FilterFunc`)
- **Protocols**: `PascalCase`, descriptive names (e.g., `GroupingStrategy`, `FileFilter`)

## File Naming

- Python modules: `snake_case.py`
- Test files: `test_{module}.py`
- Config files: lowercase with dots (`.editorconfig`, `pyproject.toml`)
- Documentation: kebab-case for directory names, descriptive for filenames
