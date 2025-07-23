"""Initialize command - Set up a new knowledge base."""

import click
from pathlib import Path
from typing import Optional

from ..utils import console, print_success, print_error, print_info, format_path, create_progress
from ...services.orchestrator import OrchestratorService


@click.command('init')
@click.argument('path', type=click.Path(), required=False)
@click.option('--name', '-n', help='Project name for this configuration', type=str)
@click.option('--sparql-endpoint', '-s', help='SPARQL endpoint URL', type=str)
@click.option('--watch/--no-watch', default=False, help='Enable file watching')
@click.option('--force', '-f', is_flag=True, help='Overwrite existing configuration')
@click.pass_obj
def init_cmd(ctx, path, name, sparql_endpoint, watch, force):
    """🚀 Initialize Knowledge Base Processor configuration.
    
    Sets up the processor to work with your existing documents by creating
    a .kbp configuration directory. Your documents remain unchanged.
    
    \b
    Examples:
      kb init                    Configure processor for current directory
      kb init ~/Documents        Configure processor for specific directory  
      kb init --name "My Docs"   Set a project name for this configuration
    """
    # Determine target path
    target_path = Path(path).resolve() if path else Path.cwd()
    
    console.print(f"\n🚀 [heading]Configuring Knowledge Base Processor[/heading]\n")
    
    # Initialize orchestrator service
    orchestrator = OrchestratorService(target_path)
    
    # Check if already initialized
    if orchestrator.is_initialized() and not force:
        print_error(f"Processor already configured for {format_path(target_path)}")
        console.print("[muted]Use --force to overwrite existing configuration.[/muted]")
        return
    
    # Get name if not provided (this is a project/config name, not creating a KB)
    if not name:
        name = click.prompt("Project name", default=target_path.name, type=str)
    
    # Get SPARQL endpoint if not provided
    if not sparql_endpoint and click.confirm("Would you like to configure a SPARQL endpoint?", default=False):
        sparql_endpoint = click.prompt(
            "SPARQL endpoint URL", 
            default="http://localhost:3030/kb",
            type=str
        )
    
    # Initialize project using orchestrator
    try:
        with create_progress() as progress:
            task = progress.add_task("Setting up processor configuration...", total=1)
            
            config = orchestrator.initialize_project(
                path=target_path,
                project_name=name,
                watch_enabled=watch,
                sparql_endpoint=sparql_endpoint,
                force=force
            )
            
            progress.advance(task)
        
        print_success(f"Processor configured for project '{name}'!")
        console.print(f"  📁 Document directory: {format_path(config.configured_path)}")
        console.print(f"  ⚙️  Configuration: {format_path(target_path / '.kbp' / 'config.yaml')}")
        
        if watch:
            print_info("File watching is enabled - changes will be processed automatically")
        
        # Show what the processor will find
        doc_count = orchestrator.count_documents()
        if doc_count > 0:
            print_info(f"Found {doc_count} existing documents ready to process")
        
        # Suggest next steps
        console.print("\n[subheading]Next steps:[/subheading]")
        if doc_count > 0:
            console.print("  1. Run [cyan]kb scan[/cyan] to process your existing documents")
            console.print("  2. Use [cyan]kb search[/cyan] to explore extracted knowledge")
            console.print("  3. Check [cyan]kb status[/cyan] for processing statistics")
        else:
            console.print("  1. Add some documents (Markdown, text files) to this directory")
            console.print("  2. Run [cyan]kb scan[/cyan] to process them")
            console.print("  3. Use [cyan]kb search[/cyan] to explore your knowledge base")
            
    except ValueError as e:
        print_error(str(e))
    except Exception as e:
        print_error(f"Failed to initialize project: {e}")
        if ctx.verbose:
            console.print_exception()