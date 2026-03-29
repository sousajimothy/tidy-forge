# ADR-001: Monorepo Structure

## Status

Accepted

## Context

TidyForge is a collection of related desktop file-management tools that share significant functionality (scanning, metadata, renaming, UI helpers). We need a project structure that:

- Allows shared code reuse without duplication
- Supports independent CLI entry points for each tool
- Is easy to develop, test, and maintain locally
- Scales as tools are added

## Decision

Use a **Python monorepo** with **uv workspaces** and **hatchling** as the build backend.

### Structure

- **Root**: Virtual workspace (`pyproject.toml` with no `[project]` table)
- **Shared packages**: `packages/` directory, each with its own `pyproject.toml`
- **Applications**: `apps/` directory, each with its own `pyproject.toml`
- **Namespace**: Implicit namespace packages under `tidyforge.*`
- **Build backend**: hatchling (fast, simple, good uv integration)

### Why uv workspaces

- Single lockfile across all packages
- Editable installs for all workspace members
- Fast dependency resolution
- Growing community adoption for Python monorepos

### Why implicit namespace packages

- Clean imports: `from tidyforge.core import FileEntry`
- Each package is independently buildable
- No risk of `__init__.py` conflicts between packages

### Why hatchling

- Native uv support
- Simple configuration
- Fast builds
- No legacy baggage

## Alternatives Considered

1. **Single package with sub-modules**: Simpler but poor separation of concerns and harder to manage optional dependencies
2. **Poetry workspaces**: Poetry's monorepo support is less mature than uv's
3. **Separate repositories**: Too much overhead for closely related tools

## Consequences

- Developers must use uv (not pip directly) for dependency management
- All packages share a single Python version constraint
- Adding a new package requires creating a directory with `pyproject.toml` and adding it to the workspace
- The implicit namespace pattern requires care: never create `tidyforge/__init__.py`
