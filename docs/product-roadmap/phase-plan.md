# TidyForge Phase Plan

## Phase 1: Foundation (current)

Establish the monorepo structure and deliver minimal viable versions of all four tools.

- Monorepo with uv workspaces
- 8 shared packages with starter implementations
- 4 apps with CLI entry points
- Comprehensive test suite
- Documentation

### Deliverables

| Tool | Capabilities |
|------|-------------|
| media-curator | Scan directories, group by extension/date/folder |
| disk-atlas | Scan, top-N files/folders, extension distribution, tree view |
| rename-studio | Template rename, prefix/suffix/replace/regex, collision detection, dry-run |
| control-center | Unified `tidyforge` command routing to all tools |

## Phase 2: Core Enhancements

- Manifest logging to JSON for all file operations
- Undo/rollback support in rename-studio using manifests
- Richer media metadata (Pillow EXIF integration)
- Improved filtering (date ranges, size ranges, custom patterns)
- Progress bars for long-running scans

## Phase 3: Duplicate Detection

- Full duplicate detection workflow in media-curator
- Interactive duplicate resolution (keep newest, keep largest, etc.)
- Hard link / symlink deduplication options
- Wasted space reporting

## Phase 4: Advanced Grouping

- Grouping by camera/device
- Grouping by EXIF date vs filesystem date
- Custom grouping rules
- Organisational plans: propose folder structures

## Phase 5: Disk Atlas Enhancements

- Treemap visualisation (terminal-based with Rich or simple HTML export)
- Historical snapshots and comparison
- Cleanup suggestions (temp files, caches, old downloads)
- Watch mode for monitoring growth

## Phase 6: UI Layer

- Lightweight TUI using Textual for interactive workflows
- control-center as an interactive dashboard
- Theme support in ui-common

## Future Considerations (not planned yet)

- Semantic similarity / near-duplicate detection (embeddings, UMAP)
- Image classification / auto-tagging
- Cloud storage integration
- Plugin system for custom tools
- GUI shell
