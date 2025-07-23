"""Modern CLI implementation with delightful user experience."""

import click
from pathlib import Path
from typing import Optional
import sys

from .commands import init, scan, search, sync, publish, status, config
from .utils import console, setup_error_handling
from .interactive import InteractiveMode

# Version info
__version__ = "2.0.0"

CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help'],
    max_content_width=120,
)


class KBContext:
    """Context object for passing state between commands."""
    
    def __init__(self):
        self.config_path: Optional[Path] = None
        self.kb_path: Optional[Path] = None
        self.verbose: bool = False
        self.quiet: bool = False
        self.no_color: bool = False
        self.yes: bool = False  # Auto-confirm prompts


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.option('--version', '-V', is_flag=True, help='Show version and exit.')
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to config file.')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output.')
@click.option('--quiet', '-q', is_flag=True, help='Suppress all output except errors.')
@click.option('--no-color', is_flag=True, help='Disable colored output.')
@click.option('--yes', '-y', is_flag=True, help='Auto-confirm all prompts (non-interactive).')
@click.pass_context
def cli(ctx, version, config, verbose, quiet, no_color, yes):
    """🧠 Knowledge Base Processor - Your intelligent document companion.
    
    A modern CLI for processing your existing documents into a searchable knowledge graph.
    Run without arguments for interactive mode.
    
    \b
    Quick Start:
      kb init          Configure processor for your documents
      kb scan          Process documents in current directory  
      kb publish       Process + sync to SPARQL in one command
      kb search "todo" Search for content
      kb status        Show processing statistics
    
    \b
    Examples:
      kb publish --watch                   Continuous publishing mode
      kb scan --sync --endpoint <url>      Process + sync to endpoint
      kb search --type todo "project tasks"
    """
    # Create context
    ctx.obj = KBContext()
    ctx.obj.verbose = verbose
    ctx.obj.quiet = quiet
    ctx.obj.no_color = no_color
    ctx.obj.yes = yes
    
    if config:
        ctx.obj.config_path = Path(config)
    
    # Setup error handling
    setup_error_handling()
    
    # Show version and exit
    if version:
        from rich import print as rprint
        from rich.panel import Panel
        rprint(Panel.fit(
            f"[bold cyan]Knowledge Base Processor[/bold cyan]\n"
            f"Version {__version__}",
            border_style="cyan"
        ))
        ctx.exit(0)
    
    # If no command specified, enter interactive mode
    if ctx.invoked_subcommand is None:
        if not sys.stdin.isatty() or yes:
            # Non-interactive environment or --yes flag
            console.print("[yellow]No command specified.[/yellow] Use 'kb --help' for usage.")
            ctx.exit(1)
        else:
            # Enter interactive mode
            interactive = InteractiveMode(ctx.obj)
            interactive.run()
            ctx.exit(0)


# Register commands
cli.add_command(init.init_cmd)
cli.add_command(scan.scan_cmd)
cli.add_command(search.search_cmd)
cli.add_command(sync.sync_cmd)
cli.add_command(publish.publish_cmd)
cli.add_command(status.status_cmd)
cli.add_command(config.config_cmd)


def main():
    """Entry point for the CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]Unexpected error:[/red] {e}")
        if '-v' in sys.argv or '--verbose' in sys.argv:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()