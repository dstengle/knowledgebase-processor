"""Search command - Find information in the knowledge base."""

import click
from pathlib import Path
from typing import Optional, List
import time

from ..utils import console, print_success, print_error, print_info, create_table, get_emoji


@click.command('search')
@click.argument('query', required=True)
@click.option('--type', '-t', 'search_type', 
              type=click.Choice(['all', 'document', 'todo', 'entity', 'tag'], case_sensitive=False),
              default='all', help='Type of content to search')
@click.option('--limit', '-l', type=int, default=20, help='Maximum number of results')
@click.option('--format', '-f', 'output_format',
              type=click.Choice(['table', 'list', 'json'], case_sensitive=False),
              default='table', help='Output format')
@click.option('--case-sensitive', '-c', is_flag=True, help='Case-sensitive search')
@click.option('--regex', '-r', is_flag=True, help='Use regular expression matching')
@click.option('--path', type=click.Path(exists=True), help='Specific path to search in')
@click.pass_obj
def search_cmd(ctx, query, search_type, limit, output_format, case_sensitive, regex, path):
    """🔍 Search your knowledge base.
    
    Find documents, todos, entities, and other content in your knowledge base.
    Supports full-text search with various filtering options.
    
    \b
    Examples:
      kb search "project tasks"        Search for anything containing "project tasks"
      kb search --type todo "urgent"   Search only todos for "urgent"
      kb search --type document API    Search only in document titles/content
      kb search --regex "bug-[0-9]+"   Use regular expressions
    """
    start_time = time.time()
    
    console.print(f"\n🔍 [heading]Searching Knowledge Base[/heading]\n")
    
    # Determine search path
    search_path = Path(path).resolve() if path else Path.cwd()
    
    # Check if knowledge base exists
    kbp_dir = search_path / ".kbp"
    if not kbp_dir.exists():
        # Look in parent directories
        current = search_path
        while current != current.parent:
            if (current / ".kbp").exists():
                kbp_dir = current / ".kbp"
                search_path = current
                break
            current = current.parent
        else:
            print_error("No knowledge base found. Run 'kb init' and 'kb scan' first.")
            return
    
    # Show search parameters
    search_icon = get_emoji('search')
    type_icon = {
        'all': '🌐',
        'document': get_emoji('document'),
        'todo': get_emoji('todo'),
        'entity': '🔗',
        'tag': '🏷️'
    }.get(search_type, '•')
    
    console.print(f"  {search_icon} Query: [highlight]'{query}'[/highlight]")
    console.print(f"  {type_icon} Type: {search_type}")
    console.print(f"  📄 Limit: {limit}")
    console.print(f"  📁 Scope: {search_path.name}")
    
    if case_sensitive:
        console.print("  🔤 Case-sensitive search enabled")
    if regex:
        console.print("  📝 Regular expression mode enabled")
    
    console.print()
    
    # Simulate search (in real implementation, this would query the database/index)
    time.sleep(0.5)  # Simulate search time
    
    # Mock results based on search type
    results = []
    
    if search_type in ['all', 'document']:
        results.extend([
            {
                'type': 'document',
                'title': 'Project Documentation.md',
                'path': 'docs/project.md',
                'snippet': f"...implementation of {query} system requires careful planning...",
                'score': 0.95
            },
            {
                'type': 'document', 
                'title': 'Meeting Notes 2024-01-15.md',
                'path': 'notes/meeting-2024-01-15.md',
                'snippet': f"...discussed {query} implementation timeline...",
                'score': 0.87
            }
        ])
    
    if search_type in ['all', 'todo']:
        results.extend([
            {
                'type': 'todo',
                'title': f'Implement {query} feature',
                'path': 'todos/backlog.md',
                'snippet': f"- [ ] Implement {query} feature with tests",
                'score': 0.92,
                'completed': False
            },
            {
                'type': 'todo',
                'title': f'Review {query} documentation',
                'path': 'todos/review.md', 
                'snippet': f"- [x] Review {query} documentation",
                'score': 0.78,
                'completed': True
            }
        ])
    
    if search_type in ['all', 'entity']:
        results.extend([
            {
                'type': 'entity',
                'title': f'{query.title()} API',
                'path': 'entities/api.md',
                'snippet': f"Entity representing {query} API endpoints...",
                'score': 0.89
            }
        ])
    
    # Sort by score and limit
    results = sorted(results, key=lambda x: x['score'], reverse=True)[:limit]
    
    # Display results
    if not results:
        print_error(f"No results found for '{query}'")
        console.print("[muted]Try:\n  • Different search terms\n  • Broader search type (--type all)\n  • Check if documents have been processed with 'kb scan'[/muted]")
        return
    
    elapsed = time.time() - start_time
    print_success(f"Found {len(results)} results in {elapsed:.2f}s")
    
    console.print()
    
    # Format output
    if output_format == 'table':
        table = create_table("Search Results", [
            ("Type", "cyan"),
            ("Title", "white"),
            ("Path", "dim white"),
            ("Score", "green")
        ])
        
        for result in results:
            type_emoji = {
                'document': get_emoji('document'),
                'todo': get_emoji('done') if result.get('completed') else get_emoji('todo'),
                'entity': '🔗',
                'tag': '🏷️'
            }.get(result['type'], '•')
            
            score_display = f"{result['score']:.0%}"
            
            table.add_row(
                f"{type_emoji} {result['type']}",
                result['title'],
                result['path'],
                score_display
            )
        
        console.print(table)
        console.print()
        
        # Show snippets
        console.print("[subheading]Content Previews:[/subheading]")
        for i, result in enumerate(results[:5], 1):  # Show first 5 snippets
            console.print(f"\n{i}. [cyan]{result['title']}[/cyan]")
            console.print(f"   {result['snippet']}")
    
    elif output_format == 'list':
        for i, result in enumerate(results, 1):
            type_emoji = {
                'document': get_emoji('document'),
                'todo': get_emoji('done') if result.get('completed') else get_emoji('todo'),
                'entity': '🔗'
            }.get(result['type'], '•')
            
            console.print(f"{i:2d}. {type_emoji} [cyan]{result['title']}[/cyan]")
            console.print(f"     📁 {result['path']} • 📊 {result['score']:.0%}")
            console.print(f"     {result['snippet']}")
            console.print()
    
    elif output_format == 'json':
        import json
        console.print(json.dumps(results, indent=2))
    
    # Show suggestions
    if len(results) == limit:
        console.print(f"[muted]Showing top {limit} results. Use --limit to see more.[/muted]")
    
    console.print("\n[subheading]Search Tips:[/subheading]")
    console.print("  • Use quotes for exact phrases: [cyan]kb search \"exact phrase\"[/cyan]")
    console.print("  • Filter by type: [cyan]kb search --type todo urgent[/cyan]")
    console.print("  • Use regex patterns: [cyan]kb search --regex \"bug-[0-9]+\"[/cyan]")