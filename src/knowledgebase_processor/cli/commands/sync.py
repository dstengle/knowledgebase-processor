"""Sync command - Upload knowledge base to SPARQL endpoint."""

import click
from pathlib import Path
from typing import Optional
import time

from ..utils import console, print_success, print_error, print_info, print_warning, create_progress, format_duration
from ...services.orchestrator import OrchestratorService


@click.command('sync')
@click.argument('endpoint', required=False)
@click.option('--graph', '-g', help='Named graph URI', type=str)
@click.option('--username', '-u', help='Username for authentication', type=str)
@click.option('--password', '-p', help='Password for authentication', 
              type=str, hide_input=True, prompt=False)
@click.option('--dataset', '-d', help='Dataset name', type=str, default='kb')
@click.option('--dry-run', is_flag=True, help='Preview sync without uploading')
@click.option('--force', '-f', is_flag=True, help='Force upload even if data exists')
@click.option('--clear-first', is_flag=True, help='Clear existing data before upload')
@click.option('--upsert/--no-upsert', default=True, help='Use upsert to avoid duplicates (default: enabled)')
@click.option('--batch-size', type=int, default=1000, help='Number of triples per batch')
@click.pass_obj
def sync_cmd(ctx, endpoint, graph, username, password, dataset, dry_run, force, clear_first, upsert, batch_size):
    """🔄 Sync knowledge base to SPARQL endpoint.
    
    Uploads your processed knowledge base to a SPARQL endpoint like Fuseki.
    Supports authentication and various sync strategies. By default, uses upsert
    to avoid creating duplicate triples.
    
    \b
    Examples:
      kb sync                                    Use configured endpoint with upsert
      kb sync http://localhost:3030/kb           Specify endpoint
      kb sync fuseki --dataset kb-test           Use preset with dataset
      kb sync --dry-run                          Preview what would be synced
      kb sync --clear-first                      Replace existing data
      kb sync --no-upsert                        Disable upsert (may create duplicates)
    """
    start_time = time.time()
    
    console.print(f"\n🔄 [heading]Syncing to SPARQL Endpoint[/heading]\n")
    
    # Initialize orchestrator service
    orchestrator = OrchestratorService()
    
    # Check if knowledge base is initialized
    if not orchestrator.is_initialized():
        print_error("No knowledge base found. Run 'kb init' and 'kb scan' first.")
        return
    
    # Get project configuration
    config = orchestrator.get_project_config()
    if not config:
        print_error("Invalid project configuration.")
        return
    
    # Determine endpoint
    if not endpoint:
        # Try to load from config
        endpoint = config.sparql_endpoint
        if not endpoint:
            endpoint = "http://localhost:3030/kb"  # Default
            print_info("Using default endpoint (configure with 'kb config sparql.endpoint <url>')")
    elif endpoint == "fuseki":
        endpoint = f"http://localhost:3030/{dataset}"
        print_info(f"Using Fuseki preset with dataset '{dataset}'")
    
    # Determine graph URI
    if not graph:
        graph = config.sparql_graph or "http://example.org/knowledgebase"
        if not config.sparql_graph:
            print_info("Using default graph URI")
    
    # Show sync configuration
    console.print(f"  🎯 Endpoint: [cyan]{endpoint}[/cyan]")
    console.print(f"  📊 Graph: [cyan]{graph}[/cyan]")
    console.print(f"  👤 Authentication: {'Yes' if username else 'No'}")
    console.print(f"  📦 Batch size: {batch_size:,} triples")
    console.print(f"  🔄 Upsert mode: {'Enabled' if upsert else 'Disabled'}")
    
    if dry_run:
        console.print("  🔍 [yellow]Dry run mode - no data will be uploaded[/yellow]")
    
    if clear_first:
        print_warning("⚠️  Clear-first mode - existing data will be removed!")
    
    if not upsert:
        print_warning("⚠️  Upsert disabled - may create duplicate triples!")
    
    console.print()
    
    # Get authentication if needed
    if username and not password:
        password = click.prompt("Password", hide_input=True)
    
    # Get statistics
    stats = orchestrator.get_project_stats()
    if stats:
        estimated_triples = (stats.total_entities * 3) if stats else 1000
        
        console.print(f"📋 [subheading]Data to sync:[/subheading]")
        console.print(f"  • ~{estimated_triples:,} total triples (estimated)")
        console.print(f"  • {stats.total_documents:,} documents")
        console.print(f"  • {stats.total_entities:,} entities") 
        console.print(f"  • {stats.todos_total:,} todos")
        console.print(f"  • {stats.wikilinks:,} relationships")
    
    if dry_run:
        elapsed = time.time() - start_time
        console.print(f"\n✅ Dry run completed in {format_duration(elapsed)}")
        console.print("Remove --dry-run to perform actual sync")
        return
    
    # Ask for confirmation if not forcing
    if not force and not ctx.yes:
        if not click.confirm(f"\nProceed with sync to {endpoint}?"):
            console.print("Sync cancelled.")
            return
    
    console.print()
    
    # Perform sync using orchestrator
    try:
        def progress_callback(current, total):
            # This would be used for real-time progress updates
            pass
        
        with create_progress() as progress:
            sync_task = progress.add_task("Syncing to SPARQL endpoint...", total=100)
            
            result = orchestrator.sync_to_sparql(
                endpoint_url=endpoint,
                graph_uri=graph,
                username=username,
                password=password,
                clear_first=clear_first,
                upsert=upsert,
                callback=progress_callback
            )
            
            # Update progress
            progress.update(sync_task, completed=100)
        
        elapsed = time.time() - start_time
        
        if result.get("success"):
            print_success(f"Sync completed successfully in {format_duration(result.get('sync_time', elapsed))}")
            
            # Show results
            console.print("\n📈 [subheading]Sync Results:[/subheading]")
            console.print(f"  ✅ {result.get('triples_uploaded', 0):,} triples uploaded")
            console.print(f"  📊 Graph: {result.get('graph', graph)}")
            if result.get('transfer_rate'):
                console.print(f"  ⚡ Transfer rate: {result['transfer_rate']:.0f} triples/second")
            
            # Provide next steps
            console.print("\n🎯 [subheading]Next Steps:[/subheading]")
            console.print(f"  • Test your endpoint: [cyan]{result.get('endpoint', endpoint)}[/cyan]")
            console.print("  • Run SPARQL queries to explore your data")
            console.print("  • Use [cyan]kb status[/cyan] to monitor your knowledge base")
            
            # Show sample queries
            console.print("\n📝 [subheading]Sample SPARQL Queries:[/subheading]")
            console.print("  • Count documents:")
            console.print("    [dim]SELECT (COUNT(?doc) as ?count) WHERE { ?doc a kb:Document }[/dim]")
            console.print("  • List all todos:")
            console.print("    [dim]SELECT ?todo ?label WHERE { ?todo a kb:TodoItem ; rdfs:label ?label }[/dim]")
        else:
            print_error(f"Sync failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print_error(f"Sync failed: {e}")
        if ctx.verbose:
            console.print_exception()