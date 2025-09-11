"""Utility functions for the modern CLI."""

import sys
from pathlib import Path
from typing import Optional, Any
from datetime import datetime

from rich.console import Console
from rich.theme import Theme
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
import click

# Custom theme for consistent styling
custom_theme = Theme({
    "info": "cyan",
    "success": "green",
    "warning": "yellow",
    "error": "red bold",
    "highlight": "magenta",
    "muted": "dim white",
    "heading": "bold cyan",
    "subheading": "bold white",
})

# Global console instance
console = Console(theme=custom_theme)


def setup_error_handling():
    """Setup global error handling for better UX."""
    sys.excepthook = handle_exception


def handle_exception(exc_type, exc_value, exc_traceback):
    """Handle uncaught exceptions with helpful messages."""
    if issubclass(exc_type, KeyboardInterrupt):
        console.print("\n[warning]Operation cancelled by user.[/warning]")
        sys.exit(130)
    
    # Don't handle system exit
    if issubclass(exc_type, SystemExit):
        return
    
    # Format the error nicely
    console.print(f"\n[error]An error occurred:[/error] {exc_value}")
    
    # Provide helpful suggestions based on error type
    if issubclass(exc_type, FileNotFoundError):
        console.print("[muted]Tip: Check if the file or directory exists.[/muted]")
    elif issubclass(exc_type, PermissionError):
        console.print("[muted]Tip: Check file permissions or try with sudo.[/muted]")
    elif "connection" in str(exc_value).lower():
        console.print("[muted]Tip: Check your network connection and endpoint URL.[/muted]")
    
    # Show traceback in verbose mode
    if "--verbose" in sys.argv or "-v" in sys.argv:
        console.print("\n[muted]Full traceback:[/muted]")
        console.print_exception()


def create_progress() -> Progress:
    """Create a rich progress bar with nice styling."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
        expand=True,
    )


def format_path(path: Path, relative_to: Optional[Path] = None) -> str:
    """Format a path for display, making it relative if possible."""
    if relative_to:
        try:
            return str(path.relative_to(relative_to))
        except ValueError:
            pass
    
    # Try to make relative to home
    try:
        home = Path.home()
        if path.is_relative_to(home):
            return "~/" + str(path.relative_to(home))
    except:
        pass
    
    return str(path)


def format_size(size_bytes: int) -> str:
    """Format byte size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def print_success(message: str):
    """Print a success message with checkmark."""
    console.print(f"[success]✓[/success] {message}")


def print_error(message: str):
    """Print an error message with X mark."""
    console.print(f"[error]✗[/error] {message}")


def print_warning(message: str):
    """Print a warning message with warning sign."""
    console.print(f"[warning]⚠[/warning]  {message}")


def print_info(message: str):
    """Print an info message with info icon."""
    console.print(f"[info]ℹ[/info]  {message}")


def create_table(title: str, columns: list[tuple[str, str]]) -> Table:
    """Create a styled table.
    
    Args:
        title: Table title
        columns: List of (header, style) tuples
    """
    table = Table(title=title, show_header=True, header_style="bold cyan")
    for header, style in columns:
        table.add_column(header, style=style)
    return table


def confirm(message: str, default: bool = False, abort: bool = False) -> bool:
    """Show a confirmation prompt.
    
    Args:
        message: Prompt message
        default: Default value if user just presses enter
        abort: If True, exit program on 'no'
    """
    return click.confirm(message, default=default, abort=abort)


def prompt(message: str, default: Any = None, type: Any = str, **kwargs) -> Any:
    """Show an input prompt.
    
    Args:
        message: Prompt message
        default: Default value
        type: Expected type
        **kwargs: Additional arguments for click.prompt
    """
    return click.prompt(message, default=default, type=type, **kwargs)


def show_panel(content: str, title: str = None, style: str = "cyan"):
    """Show content in a nice panel."""
    panel = Panel(content, title=title, border_style=style, expand=False)
    console.print(panel)


def show_code(code: str, language: str = "python", title: str = None):
    """Show syntax-highlighted code."""
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    if title:
        panel = Panel(syntax, title=title, border_style="dim")
        console.print(panel)
    else:
        console.print(syntax)


def format_timestamp(dt: datetime) -> str:
    """Format a datetime in a friendly way."""
    now = datetime.now()
    delta = now - dt
    
    if delta.days == 0:
        if delta.seconds < 60:
            return "just now"
        elif delta.seconds < 3600:
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif delta.days == 1:
        return "yesterday"
    elif delta.days < 7:
        return f"{delta.days} days ago"
    else:
        return dt.strftime("%Y-%m-%d")


def get_emoji(status: str) -> str:
    """Get emoji for different statuses."""
    emojis = {
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
        "processing": "⚙️",
        "document": "📄",
        "folder": "📁",
        "search": "🔍",
        "sync": "🔄",
        "config": "⚙️",
        "rocket": "🚀",
        "sparkles": "✨",
        "brain": "🧠",
        "link": "🔗",
        "todo": "☐",
        "done": "☑",
    }
    return emojis.get(status, "•")