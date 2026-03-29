"""Control Center CLI - unified entrypoint for TidyForge tools."""

from __future__ import annotations

import typer

from disk_atlas.cli import app as disk_app
from media_curator.cli import app as media_app
from rename_studio.cli import app as rename_app

app = typer.Typer(
    name="tidyforge",
    help="TidyForge - desktop housekeeping and file management tools.",
    no_args_is_help=True,
)

app.add_typer(media_app, name="media", help="Organise photos and videos")
app.add_typer(disk_app, name="disk", help="Analyse disk usage")
app.add_typer(rename_app, name="rename", help="Batch rename files")


@app.command()
def version() -> None:
    """Show the TidyForge version."""
    from control_center import __version__

    typer.echo(f"TidyForge v{__version__}")
