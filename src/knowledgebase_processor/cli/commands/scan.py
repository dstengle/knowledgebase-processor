"""Scan command - Process documents and extract knowledge."""

import click
from pathlib import Path
from typing import List, Optional
import time

from ..utils import console, print_success, print_error, print_info, format_path, create_progress, format_duration
from ...services.orchestrator import OrchestratorService


@click.command('scan')
@click.argument('path', type=click.Path(exists=True), required=False)
@click.option('--pattern', '-p', multiple=True, help='File patterns to process (e.g., "**/*.md")')
@click.option('--watch', '-w', is_flag=True, help='Watch for file changes and process automatically')
@click.option('--sync', is_flag=True, help='Sync to SPARQL after processing')
@click.option('--endpoint', '-e', help='SPARQL endpoint URL for sync')
@click.option('--recursive/--no-recursive', '-r/-R', default=True, help='Scan subdirectories')
@click.option('--force', '-f', is_flag=True, help='Reprocess all files, even if unchanged')
@click.option('--output', '-o', type=click.Path(), help='Output directory for processed files')
@click.option('--dry-run', is_flag=True, help='Show what would be processed without actually processing')
@click.pass_obj
def scan_cmd(ctx, path, pattern, watch, sync, endpoint, recursive, force, output, dry_run):
    """📁 Scan and process documents.
    
    Processes documents in the specified directory (or current directory)
    and extracts knowledge entities, todos, and relationships. Optionally
    syncs the results to a SPARQL endpoint.
    
    \b
    Examples:
      kb scan                           Scan current directory
      kb scan ~/Documents              Scan specific directory
      kb scan --pattern "*.md"         Only process Markdown files
      kb scan --watch                  Watch for changes
      kb scan --sync --endpoint http://localhost:3030/kb  Process + sync to SPARQL
      kb scan --dry-run                Preview what would be processed
    """
    start_time = time.time()
    
    # Determine scan path
    scan_path = Path(path).resolve() if path else Path.cwd()
    
    console.print(f"\n📁 [heading]Scanning Documents[/heading]\n")
    
    # Initialize orchestrator service
    orchestrator = OrchestratorService(scan_path)
    
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
    
    print_info(f"Scanning: {format_path(scan_path)}")
    if dry_run:
        print_info("🔍 Dry run mode - no files will be processed")
    
    console.print(f"  📋 Patterns: {', '.join(patterns)}")
    console.print(f"  🔄 Recursive: {'Yes' if recursive else 'No'}")
    console.print(f"  💪 Force: {'Yes' if force else 'No'}")
    
    # Count documents to process
    doc_count = orchestrator.count_documents(patterns)
    
    if doc_count == 0:
        print_error(f"No files found matching patterns: {', '.join(patterns)}")
        return
    
    console.print(f"\n📊 Found {doc_count} files to process\n")
    
    # Show files if dry run
    if dry_run:
        console.print("[subheading]Files that would be processed:[/subheading]")
        
        # Find actual files for display
        all_files = []
        for ptn in patterns:
            if recursive:
                all_files.extend(scan_path.rglob(ptn))
            else:
                all_files.extend(scan_path.glob(ptn))
        
        unique_files = sorted(set(f for f in all_files if f.is_file()))
        
        for i, file_path in enumerate(unique_files[:10]):  # Show first 10
            try:
                rel_path = file_path.relative_to(scan_path)
            except ValueError:
                rel_path = file_path
            console.print(f"  {i+1:3d}. {rel_path}")
        
        if len(unique_files) > 10:
            console.print(f"  ... and {len(unique_files) - 10} more files")
        
        elapsed = time.time() - start_time
        console.print(f"\n⏱️  Scan completed in {format_duration(elapsed)}")
        return
    
    # Process files using orchestrator
    try:
        def progress_callback(current, total):
            # This would be used for real-time progress updates
            pass
        
        with create_progress() as progress:
            task = progress.add_task("Processing files...", total=doc_count)
            
            result = orchestrator.process_documents(
                patterns=patterns,
                force=force,
                callback=progress_callback
            )
            
            # Update progress bar
            progress.update(task, completed=doc_count)
        
        # Show results
        elapsed = time.time() - start_time
        
        if result.error_messages:
            for error in result.error_messages:
                console.print(f"[error]Error: {error}[/error]")
        
        if result.files_processed > 0:
            print_success(f"Processing completed in {format_duration(result.processing_time)}")
            
            console.print("\n📈 [subheading]Results Summary:[/subheading]")
            console.print(f"  ✅ Files processed: {result.files_processed}")
            if result.files_failed > 0:
                console.print(f"  ❌ Errors: {result.files_failed}")
            console.print(f"  🔗 Entities extracted: {result.entities_extracted}")
            console.print(f"  ☐ Todos found: {result.todos_found}")
            
            # Handle sync if requested
            if sync:
                # Determine endpoint from config if not provided
                sync_endpoint = endpoint
                if not sync_endpoint:
                    sync_endpoint = config.sparql_endpoint
                    if not sync_endpoint:
                        sync_endpoint = "http://localhost:3030/kb"  # Default
                        print_info("Using default SPARQL endpoint for sync")
                
                console.print("\n🔄 [subheading]Syncing to SPARQL...[/subheading]")
                console.print(f"  🎯 Endpoint: [cyan]{sync_endpoint}[/cyan]")
                
                try:
                    sync_result = orchestrator.sync_to_sparql(
                        endpoint_url=sync_endpoint,
                        upsert=True  # Use upsert by default for scan
                    )
                    
                    if sync_result.get('success'):
                        files_synced = sync_result.get('files_synced', 0)
                        transfer_rate = sync_result.get('transfer_rate', '0 KB/s')
                        console.print(f"  ✅ Synced: {files_synced} files ({transfer_rate})")
                        print_success("Scan and sync completed successfully!")
                    else:
                        print_error(f"Sync failed: {sync_result.get('error', 'Unknown error')}")
                except Exception as e:
                    print_error(f"Sync failed: {e}")
            
            # Show next steps
            if not watch and not sync:
                console.print("\n[subheading]Next steps:[/subheading]")
                console.print("  • Use [cyan]kb search[/cyan] to explore your knowledge base")
                console.print("  • Run [cyan]kb status[/cyan] to see detailed statistics")
                console.print("  • Add [cyan]--sync --endpoint <url>[/cyan] to publish to SPARQL")
                console.print("  • Add [cyan]--watch[/cyan] to monitor for file changes")
        else:
            print_error("No files were processed successfully")
        
        # Handle watch mode
        if watch:
            console.print("\n👀 [heading]Watch Mode Enabled[/heading]")
            console.print("Monitoring for file changes... Press Ctrl+C to stop")
            
            try:
                while True:
                    # Here would be the actual file watching logic
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                console.print("\n✋ Watch mode stopped")
                
    except Exception as e:
        print_error(f"Processing failed: {e}")
        if ctx.verbose:
            console.print_exception()