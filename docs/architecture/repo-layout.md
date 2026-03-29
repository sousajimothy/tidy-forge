# Repository Layout

```
tidy-forge/
  pyproject.toml              # Workspace root: uv config, ruff, pytest, mypy
  .python-version             # Python 3.11 pin
  .gitignore
  .editorconfig
  .env.example
  .pre-commit-config.yaml
  README.md

  packages/                   # Shared libraries
    core/                     # Settings, logging, exceptions, data models
      pyproject.toml
      src/tidyforge/core/
        __init__.py
        config.py             # TidyForgeSettings (pydantic-settings)
        logging.py            # Rich-based logging setup
        exceptions.py         # TidyForgeError hierarchy
        models.py             # FileEntry, OperationResult, ActionManifest
        types.py              # PathLike, FilterFunc type aliases

    fs-indexer/               # Filesystem scanning and aggregation
      src/tidyforge/fs_indexer/
        scanner.py            # scan_directory() with depth/filter control
        filters.py            # Extension, size, pattern, composite filters
        aggregator.py         # Aggregation by extension, directory, top-N

    metadata/                 # File metadata extraction
      src/tidyforge/metadata/
        fs_metadata.py        # Filesystem metadata (cross-platform)
        media.py              # EXIF extraction (optional Pillow)
        categories.py         # Extension-to-category mapping

    media-grouping/           # File grouping strategies
      src/tidyforge/media_grouping/
        strategies.py         # ByExtension, ByDate, ByParentFolder, etc.
        engine.py             # GroupingEngine + GroupSummary

    duplicate-detection/      # Hash-based duplicate finding
      src/tidyforge/duplicate_detection/
        hashing.py            # hash_file(), find_duplicates(), DuplicateReport

    rename-engine/            # Rename planning and execution
      src/tidyforge/rename_engine/
        plan.py               # RenameAction, RenamePlan (collision detection)
        templates.py          # TemplateRenderer, build_plan_from_template()
        operations.py         # prefix, suffix, replace, regex, sequential

    job-runner/               # Job lifecycle tracking
      src/tidyforge/job_runner/
        runner.py             # Job, JobStatus, run_job()

    ui-common/                # Console output helpers
      src/tidyforge/ui_common/
        console.py            # Rich console instance, print helpers
        tables.py             # Table and file table formatters

  apps/                       # User-facing tools
    media-curator/            # CLI: scan, group media files
      src/media_curator/
        cli.py                # Typer app: scan, group commands

    disk-atlas/               # CLI: analyse disk usage
      src/disk_atlas/
        cli.py                # Typer app: scan, tree commands

    rename-studio/            # CLI: batch rename with preview
      src/rename_studio/
        cli.py                # Typer app: preview, prefix, suffix, replace, regex

    control-center/           # Unified launcher
      src/control_center/
        cli.py                # Typer app: tidyforge media|disk|rename

  tests/
    conftest.py               # Shared fixtures
    packages/                 # Unit tests for each package
    apps/                     # CLI smoke tests

  docs/
    architecture/             # This directory
    product-roadmap/          # Phase plan
    decisions/                # Architecture Decision Records
    naming/                   # Naming conventions

  data/
    fixtures/sample_tree/     # Static test fixtures
    samples/                  # Development sample data
    tmp/                      # Temporary files (gitignored)

  infra/
    scripts/                  # Bootstrap and utility scripts
    ci/                       # CI pipeline configs
    packaging/                # Distribution packaging
```
