"""Shared Rich console instance and output helpers."""

from __future__ import annotations

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.prompt import Confirm

console = Console()


def print_header(title: str) -> None:
    """Print a styled section header."""
    console.print(f"\n[bold cyan]{title}[/bold cyan]")
    console.print("[dim]" + "-" * len(title) + "[/dim]")


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]{message}[/green]")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[bold red]Error:[/bold red] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow]Warning:[/yellow] {message}")


def confirm_action(message: str, *, default: bool = False) -> bool:
    """Prompt the user for confirmation.

    Args:
        message: The confirmation prompt text.
        default: Default answer if the user presses Enter.

    Returns:
        True if confirmed, False otherwise.
    """
    return Confirm.ask(message, default=default, console=console)


def create_progress() -> Progress:
    """Create a configured Rich Progress bar."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    )
