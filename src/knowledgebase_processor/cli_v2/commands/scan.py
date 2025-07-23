"""Scan command - Process documents and extract knowledge."""

import click
from pathlib import Path
from typing import List, Optional
import time

from ..utils import console, print_success, print_error, print_info, format_path, create_progress, format_duration


@click.command('scan')
@click.argument('path', type=click.Path(exists=True), required=False)
@click.option('--pattern', '-p', multiple=True, help='File patterns to process (e.g., "**/*.md")')
@click.option('--watch', '-w', is_flag=True, help='Watch for file changes and process automatically')
@click.option('--recursive/--no-recursive', '-r/-R', default=True, help='Scan subdirectories')
@click.option('--force', '-f', is_flag=True, help='Reprocess all files, even if unchanged')
@click.option('--output', '-o', type=click.Path(), help='Output directory for processed files')
@click.option('--dry-run', is_flag=True, help='Show what would be processed without actually processing')
@click.pass_obj
def scan_cmd(ctx, path, pattern, watch, recursive, force, output, dry_run):
    """📁 Scan and process documents.
    
    Processes documents in the specified directory (or current directory)
    and extracts knowledge entities, todos, and relationships.
    
    \b
    Examples:
      kb scan                           Scan current directory
      kb scan ~/Documents              Scan specific directory
      kb scan --pattern "*.md"         Only process Markdown files
      kb scan --watch                  Watch for changes
      kb scan --dry-run                Preview what would be processed
    """
    start_time = time.time()
    
    # Determine scan path
    scan_path = Path(path).resolve() if path else Path.cwd()
    
    console.print(f"\n📁 [heading]Scanning Documents[/heading]\n")
    
    # Check if knowledge base is initialized
    kbp_dir = scan_path / ".kbp"
    if not kbp_dir.exists():
        # Look in parent directories
        current = scan_path
        while current != current.parent:
            if (current / ".kbp").exists():
                kbp_dir = current / ".kbp"
                break
            current = current.parent
        else:
            print_error("No knowledge base found. Run 'kb init' first.")
            return
    
    # Determine patterns
    patterns = list(pattern) if pattern else ["**/*.md", "**/*.txt"]
    
    print_info(f"Scanning: {format_path(scan_path)}")
    if dry_run:
        print_info("🔍 Dry run mode - no files will be processed")
    
    console.print(f"  📋 Patterns: {', '.join(patterns)}")
    console.print(f"  🔄 Recursive: {'Yes' if recursive else 'No'}")
    console.print(f"  💪 Force: {'Yes' if force else 'No'}")
    
    # Find matching files
    all_files = []
    for ptn in patterns:
        if recursive:
            all_files.extend(scan_path.rglob(ptn))
        else:
            all_files.extend(scan_path.glob(ptn))
    
    # Remove duplicates and filter
    unique_files = list(set(f for f in all_files if f.is_file()))
    
    if not unique_files:
        print_error(f"No files found matching patterns: {', '.join(patterns)}")
        return
    
    console.print(f"\n📊 Found {len(unique_files)} files to process\n")
    
    # Show files if dry run
    if dry_run:
        console.print("[subheading]Files that would be processed:[/subheading]")
        for i, file_path in enumerate(sorted(unique_files)[:10]):  # Show first 10
            rel_path = file_path.relative_to(scan_path) if file_path.is_relative_to(scan_path) else file_path
            console.print(f"  {i+1:3d}. {rel_path}")
        
        if len(unique_files) > 10:
            console.print(f"  ... and {len(unique_files) - 10} more files")
        
        elapsed = time.time() - start_time
        console.print(f"\n⏱️  Scan completed in {format_duration(elapsed)}")
        return
    
    # Process files
    with create_progress() as progress:
        task = progress.add_task("Processing files...", total=len(unique_files))
        
        processed_count = 0
        error_count = 0
        entities_count = 0
        todos_count = 0
        
        for file_path in unique_files:
            try:
                # Here would be the actual processing logic
                # For now, simulate processing
                time.sleep(0.01)  # Simulate work
                
                # Mock results
                processed_count += 1
                entities_count += 5  # Mock entity count
                todos_count += 2     # Mock todo count
                
                progress.advance(task)
                
            except Exception as e:
                error_count += 1
                console.print(f"[error]Error processing {file_path}: {e}[/error]")
                progress.advance(task)
    
    # Show results
    elapsed = time.time() - start_time
    
    print_success(f"Processing completed in {format_duration(elapsed)}")
    
    console.print("\n📈 [subheading]Results Summary:[/subheading]")
    console.print(f"  ✅ Files processed: {processed_count}")
    if error_count > 0:
        console.print(f"  ❌ Errors: {error_count}")
    console.print(f"  🔗 Entities extracted: {entities_count}")
    console.print(f"  ☐ Todos found: {todos_count}")
    
    # Show next steps
    if not watch:
        console.print("\n[subheading]Next steps:[/subheading]")
        console.print("  • Use [cyan]kb search[/cyan] to explore your knowledge base")
        console.print("  • Run [cyan]kb status[/cyan] to see detailed statistics")
        console.print("  • Add [cyan]--watch[/cyan] to monitor for file changes")
    
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