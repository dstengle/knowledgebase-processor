"""Publish command - Unified process + sync workflow."""

import click
from pathlib import Path
from typing import Optional
import time
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ..utils import console, print_success, print_error, print_info, print_warning, create_progress, format_duration
from ...services.orchestrator import OrchestratorService


class KnowledgeBaseHandler(FileSystemEventHandler):
    """File system event handler for knowledge base files."""
    
    def __init__(self, orchestrator: OrchestratorService, sync_config: dict, debounce_seconds: float = 2.0):
        super().__init__()
        self.orchestrator = orchestrator
        self.sync_config = sync_config
        self.debounce_seconds = debounce_seconds
        self.pending_changes = set()
        self.last_change_time = 0
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Check if file matches our patterns
        config = self.orchestrator.get_project_config()
        if config and any(file_path.match(pattern) for pattern in config.file_patterns):
            self.pending_changes.add(file_path)
            self.last_change_time = time.time()
    
    def on_created(self, event):
        self.on_modified(event)
    
    def on_deleted(self, event):
        if not event.is_directory:
            file_path = Path(event.src_path)
            self.pending_changes.add(file_path)
            self.last_change_time = time.time()
    
    def should_process_changes(self) -> bool:
        """Check if enough time has passed since last change (debouncing)."""
        return (
            self.pending_changes and 
            time.time() - self.last_change_time >= self.debounce_seconds
        )
    
    def process_pending_changes(self):
        """Process all pending file changes."""
        if not self.pending_changes:
            return
            
        console.print(f"\n📝 [subheading]Processing {len(self.pending_changes)} changed files...[/subheading]")
        
        try:
            # Process documents
            result = self.orchestrator.process_documents(
                patterns=None,  # Use default patterns
                force=False     # Only process changed files
            )
            
            if result.files_processed > 0:
                console.print(f"  ✅ Processed {result.files_processed} files")
                
                # Sync to SPARQL
                sync_result = self.orchestrator.sync_to_sparql(**self.sync_config)
                
                if sync_result.get('success'):
                    files_synced = sync_result.get('files_synced', 0)
                    transfer_rate = sync_result.get('transfer_rate', '0 KB/s')
                    console.print(f"  🔄 Synced {files_synced} files ({transfer_rate})")
                    print_success("Knowledge base updated successfully!")
                else:
                    print_error(f"Sync failed: {sync_result.get('error', 'Unknown error')}")
            else:
                console.print("  ℹ️  No files needed processing")
                
        except Exception as e:
            print_error(f"Auto-publish failed: {e}")
        finally:
            self.pending_changes.clear()


@click.command('publish')
@click.argument('path', type=click.Path(exists=True), required=False)
@click.option('--endpoint', '-e', help='SPARQL endpoint URL')
@click.option('--graph', '-g', help='Named graph URI', type=str)
@click.option('--username', '-u', help='Username for authentication', type=str)
@click.option('--password', help='Password for authentication', 
              type=str, hide_input=True, prompt=False)
@click.option('--dataset', '-d', help='Dataset name', type=str, default='kb')
@click.option('--watch', '-w', is_flag=True, help='Watch for changes and auto-publish')
@click.option('--pattern', multiple=True, help='File patterns to include (e.g., "**/*.md")')
@click.option('--dry-run', is_flag=True, help='Preview what would be published without publishing')
@click.option('--force', '-f', is_flag=True, help='Reprocess all files, even if unchanged')
@click.option('--clear-first', is_flag=True, help='Clear existing data before publishing')
@click.option('--upsert/--no-upsert', default=True, help='Use upsert to avoid duplicates (default: enabled)')
@click.option('--batch-size', type=int, default=1000, help='Number of triples per batch')
@click.option('--debounce', type=float, default=2.0, help='Seconds to wait after file changes before processing')
@click.pass_obj
def publish_cmd(ctx, path, endpoint, graph, username, password, dataset, watch, pattern, 
                dry_run, force, clear_first, upsert, batch_size, debounce):
    """📤 Publish knowledge base to SPARQL endpoint.
    
    Unified workflow that processes documents and syncs them to a SPARQL endpoint
    in one command. Perfect for both one-shot publishing and continuous publishing
    during development.
    
    \b
    Examples:
      kb publish                                  Process + sync with configured endpoint
      kb publish --endpoint http://localhost:3030/kb  Publish to specific endpoint  
      kb publish --watch                          Continuous publishing mode
      kb publish --dry-run                        Preview what would be published
      kb publish --force                          Reprocess all files
      kb publish --clear-first                    Replace all existing data
    """
    start_time = time.time()
    
    console.print(f"\n📤 [heading]Publishing Knowledge Base[/heading]\n")
    
    # Determine path
    publish_path = Path(path).resolve() if path else Path.cwd()
    
    # Initialize orchestrator service  
    orchestrator = OrchestratorService(publish_path)
    
    # Check if knowledge base is initialized
    if not orchestrator.is_initialized():
        print_error("No knowledge base found. Run 'kb init' first.")
        return
    
    # Get project configuration
    config = orchestrator.get_project_config()
    if not config:
        print_error("Invalid project configuration. Run 'kb init' first.")
        return
    
    # Determine patterns
    patterns = list(pattern) if pattern else config.file_patterns
    
    # Determine endpoint from config if not provided
    if not endpoint:
        # Try to load from config
        endpoint = config.sparql_endpoint
        if not endpoint:
            endpoint = "http://localhost:3030/kb"  # Default
            print_info("Using default endpoint (configure with 'kb config sparql.endpoint <url>')")
    elif endpoint == "fuseki":
        endpoint = f"http://localhost:3030/{dataset}"
        print_info(f"Using Fuseki preset with dataset '{dataset}'")
    
    # Determine graph URI from config if not provided
    if not graph:
        graph = config.sparql_graph or "http://example.org/knowledgebase"
        if not config.sparql_graph:
            print_info("Using default graph URI")
    
    # Display configuration
    print_info(f"Publishing from: {publish_path}")
    console.print(f"  📋 Patterns: {', '.join(patterns)}")
    console.print(f"  🎯 Endpoint: [cyan]{endpoint}[/cyan]")
    if graph:
        console.print(f"  📊 Graph: [cyan]{graph}[/cyan]")
    console.print(f"  👤 Authentication: {'Yes' if username else 'No'}")
    console.print(f"  🔄 Force: {'Yes' if force else 'No'}")
    console.print(f"  🎯 Upsert mode: {'Enabled' if upsert else 'Disabled'}")
    
    if dry_run:
        console.print("  🔍 [yellow]Dry run mode - no publishing will occur[/yellow]")
    
    if clear_first:
        print_warning("⚠️  Clear-first mode - existing data will be removed!")
    
    if not upsert:
        print_warning("⚠️  Upsert disabled - may create duplicate triples!")
    
    console.print()
    
    # Setup sync configuration
    sync_config = {
        'endpoint_url': endpoint,
        'graph_uri': graph,
        'username': username,
        'password': password,
        'clear_first': clear_first,
        'upsert': upsert
    }
    
    # Get authentication if needed
    if endpoint and username and not password:
        password = click.prompt('Password', hide_input=True)
        sync_config['password'] = password
    
    def publish_once():
        """Perform a single publish operation."""
        try:
            # Step 1: Process documents
            console.print("📁 [subheading]Step 1: Processing Documents[/subheading]")
            
            doc_count = orchestrator.count_documents(patterns)
            if doc_count == 0:
                print_error(f"No files found matching patterns: {', '.join(patterns)}")
                return False
            
            console.print(f"Found {doc_count} files to process")
            
            if dry_run:
                console.print("🔍 Would process files (dry run mode)")
            else:
                with create_progress() as progress:
                    task = progress.add_task("Processing files...", total=doc_count)
                    
                    result = orchestrator.process_documents(
                        patterns=patterns,
                        force=force
                    )
                    
                    progress.update(task, completed=doc_count)
                
                if result.files_processed == 0:
                    print_info("No files needed processing")
                    return True
                
                console.print(f"  ✅ Processed: {result.files_processed} files")
                console.print(f"  🔗 Entities: {result.entities_extracted}")
                console.print(f"  ☐ Todos: {result.todos_found}")
                
                if result.files_failed > 0:
                    console.print(f"  ❌ Errors: {result.files_failed}")
            
            # Step 2: Sync to SPARQL
            console.print("\n🔄 [subheading]Step 2: Syncing to SPARQL[/subheading]")
            
            if dry_run:
                console.print("🔍 Would sync to SPARQL (dry run mode)")
                return True
            
            console.print(f"  🎯 Endpoint: {endpoint}")
            if graph:
                console.print(f"  📊 Graph: {graph}")
            
            sync_result = orchestrator.sync_to_sparql(**sync_config)
            
            if sync_result.get('success'):
                files_synced = sync_result.get('files_synced', 0)
                transfer_rate = sync_result.get('transfer_rate', '0 KB/s')
                sync_time = sync_result.get('sync_time', 0)
                
                console.print(f"  ✅ Synced: {files_synced} files")
                console.print(f"  ⚡ Rate: {transfer_rate}")
                console.print(f"  ⏱️  Time: {format_duration(sync_time)}")
                
                return True
            else:
                print_error(f"Sync failed: {sync_result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print_error(f"Publishing failed: {e}")
            if ctx.verbose:
                console.print_exception()
            return False
    
    # Single publish
    if not watch:
        success = publish_once()
        
        elapsed = time.time() - start_time
        
        if success:
            print_success(f"Knowledge base published successfully in {format_duration(elapsed)}!")
            
            if not dry_run:
                console.print("\n[subheading]Next steps:[/subheading]")
                console.print("  • Query your knowledge base via SPARQL endpoint")
                console.print("  • Use [cyan]kb publish --watch[/cyan] for continuous publishing")
                console.print("  • Run [cyan]kb status[/cyan] for detailed statistics")
        else:
            print_error("Publishing failed")
        return
    
    # Watch mode
    console.print("👀 [heading]Watch Mode Enabled[/heading]")
    console.print(f"Monitoring {publish_path} for changes... Press Ctrl+C to stop")
    console.print(f"Debounce delay: {debounce}s")
    
    # Endpoint is already determined from config or provided, so no need to check again
    
    # Initial publish
    console.print("\n🚀 [subheading]Initial Publish[/subheading]")
    publish_once()
    
    # Setup file watching
    event_handler = KnowledgeBaseHandler(orchestrator, sync_config, debounce)
    observer = Observer()
    observer.schedule(event_handler, str(publish_path), recursive=True)
    
    try:
        observer.start()
        console.print(f"\n✅ Watching for changes in {publish_path}")
        
        while True:
            time.sleep(1)
            
            # Check for pending changes to process
            if event_handler.should_process_changes():
                event_handler.process_pending_changes()
                
    except KeyboardInterrupt:
        console.print("\n✋ Watch mode stopped")
        observer.stop()
    
    observer.join()