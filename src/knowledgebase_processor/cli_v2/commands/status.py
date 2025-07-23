"""Status command - Show knowledge base statistics and health."""

import click
from pathlib import Path
from datetime import datetime, timedelta
import time

from ..utils import (
    console, print_success, print_info, create_table, 
    format_path, format_size, format_timestamp, get_emoji
)


@click.command('status')
@click.option('--detailed', '-d', is_flag=True, help='Show detailed statistics')
@click.option('--health-check', is_flag=True, help='Run system health checks')
@click.option('--path', type=click.Path(exists=True), help='Knowledge base path')
@click.pass_obj
def status_cmd(ctx, detailed, health_check, path):
    """📊 Show knowledge base status and statistics.
    
    Displays an overview of your knowledge base including document counts,
    processing statistics, and system health information.
    
    \b
    Examples:
      kb status                 Show basic statistics
      kb status --detailed      Show detailed breakdown
      kb status --health-check  Include system health checks
    """
    console.print(f"\n📊 [heading]Knowledge Base Status[/heading]\n")
    
    # Determine KB path
    kb_path = Path(path).resolve() if path else Path.cwd()
    
    # Find knowledge base
    kbp_dir = kb_path / ".kbp"
    if not kbp_dir.exists():
        # Look in parent directories
        current = kb_path
        while current != current.parent:
            if (current / ".kbp").exists():
                kbp_dir = current / ".kbp"
                kb_path = current
                break
            current = current.parent
        else:
            console.print(f"❌ [error]No knowledge base found[/error]")
            console.print("[muted]Run 'kb init' to create one, or specify --path[/muted]")
            return
    
    # Load config (mock data for now)
    config_file = kbp_dir / "config.yaml"
    kb_name = "My Knowledge Base"  # Would read from config
    
    print_info(f"Knowledge Base: [cyan]{kb_name}[/cyan]")
    console.print(f"📁 Location: {format_path(kb_path)}")
    console.print()
    
    # Basic statistics (mock data)
    stats = {
        'documents': 156,
        'processed_documents': 152,
        'failed_documents': 4,
        'total_entities': 1234,
        'todos_total': 89,
        'todos_completed': 23,
        'todos_pending': 66,
        'tags': 45,
        'wikilinks': 567,
        'last_scan': datetime.now() - timedelta(hours=2, minutes=15),
        'database_size': 12345678,  # bytes
        'processing_time': 45.2,  # seconds
    }
    
    # Create main stats table
    main_table = create_table("Overview", [
        ("Metric", "cyan"),
        ("Value", "white"),
        ("Status", "green")
    ])
    
    # Add basic stats
    main_table.add_row(
        f"{get_emoji('document')} Documents",
        f"{stats['processed_documents']:,} / {stats['documents']:,}",
        "✅ Good" if stats['failed_documents'] < 5 else "⚠️ Issues"
    )
    
    main_table.add_row(
        f"{get_emoji('link')} Total Entities",
        f"{stats['total_entities']:,}",
        "✅ Active"
    )
    
    todo_status = "✅ On Track" if stats['todos_completed'] > stats['todos_pending'] * 0.3 else "📝 Active"
    main_table.add_row(
        f"{get_emoji('todo')} Todos",
        f"{stats['todos_completed']:,} done, {stats['todos_pending']:,} pending",
        todo_status
    )
    
    main_table.add_row(
        "🏷️ Tags",
        f"{stats['tags']:,}",
        "✅ Active"
    )
    
    main_table.add_row(
        "🔗 Wiki Links",
        f"{stats['wikilinks']:,}",
        "✅ Connected"
    )
    
    main_table.add_row(
        "📅 Last Scan",
        format_timestamp(stats['last_scan']),
        "✅ Recent" if (datetime.now() - stats['last_scan']).days < 1 else "⚠️ Stale"
    )
    
    main_table.add_row(
        "💾 Database Size",
        format_size(stats['database_size']),
        "✅ Normal"
    )
    
    console.print(main_table)
    
    # Show errors if any
    if stats['failed_documents'] > 0:
        console.print(f"\n⚠️ [warning]{stats['failed_documents']} documents failed to process[/warning]")
        console.print("[muted]Run 'kb scan --force' to retry failed documents[/muted]")
    
    # Detailed statistics
    if detailed:
        console.print(f"\n📈 [subheading]Detailed Statistics[/subheading]\n")
        
        # Document types
        doc_types_table = create_table("Document Types", [
            ("Type", "cyan"),
            ("Count", "white"),
            ("Percentage", "green")
        ])
        
        doc_types = [
            ("Markdown (.md)", 142, 91.0),
            ("Text (.txt)", 10, 6.4),
            ("Other", 4, 2.6)
        ]
        
        for doc_type, count, percentage in doc_types:
            doc_types_table.add_row(doc_type, f"{count:,}", f"{percentage:.1f}%")
        
        console.print(doc_types_table)
        
        # Entity types
        console.print()
        entity_table = create_table("Entity Breakdown", [
            ("Entity Type", "cyan"),
            ("Count", "white"),
            ("Growth", "green")
        ])
        
        entities = [
            ("Documents", stats['documents'], "+12"),
            ("Todos", stats['todos_total'], "+5"),
            ("Tags", stats['tags'], "+3"),
            ("Wiki Links", stats['wikilinks'], "+45"),
            ("Mentions", 234, "+15"),
            ("References", 123, "+8")
        ]
        
        for entity_type, count, growth in entities:
            growth_color = "green" if growth.startswith("+") else "red"
            entity_table.add_row(
                entity_type,
                f"{count:,}",
                f"[{growth_color}]{growth}[/{growth_color}]"
            )
        
        console.print(entity_table)
    
    # Health checks
    if health_check:
        console.print(f"\n🏥 [subheading]System Health Check[/subheading]\n")
        
        # Simulate health checks
        health_checks = [
            ("Configuration", "✅", "Valid configuration found"),
            ("Database", "✅", "SQLite database accessible"),
            ("File System", "✅", "All paths accessible"),
            ("Dependencies", "✅", "All required packages installed"),
            ("Memory Usage", "✅", f"Using {format_size(45 * 1024 * 1024)} (Normal)"),
            ("SPARQL Endpoint", "❓", "Not configured")
        ]
        
        health_table = create_table("Health Checks", [
            ("Component", "cyan"),
            ("Status", "white"),
            ("Details", "dim white")
        ])
        
        for component, status, details in health_checks:
            health_table.add_row(component, status, details)
        
        console.print(health_table)
        
        # Overall health score
        healthy_count = sum(1 for _, status, _ in health_checks if status == "✅")
        total_checks = len(health_checks)
        health_score = (healthy_count / total_checks) * 100
        
        if health_score >= 90:
            health_status = "[green]Excellent[/green] 🎉"
        elif health_score >= 75:
            health_status = "[yellow]Good[/yellow] 👍"
        elif health_score >= 60:
            health_status = "[yellow]Fair[/yellow] 😐"
        else:
            health_status = "[red]Poor[/red] 😟"
        
        console.print(f"\n📊 Overall Health Score: [bold]{health_score:.0f}%[/bold] ({health_status})")
    
    # Performance info
    console.print(f"\n⚡ [subheading]Performance[/subheading]")
    console.print(f"  • Last processing time: {stats['processing_time']:.1f}s")
    console.print(f"  • Average processing speed: {stats['documents'] / stats['processing_time']:.1f} docs/second")
    
    # Suggestions
    console.print(f"\n💡 [subheading]Suggestions[/subheading]")
    
    suggestions = []
    
    if stats['failed_documents'] > 0:
        suggestions.append("Run [cyan]kb scan --force[/cyan] to retry failed documents")
    
    if (datetime.now() - stats['last_scan']).days >= 1:
        suggestions.append("Consider running [cyan]kb scan[/cyan] to update with recent changes")
    
    if stats['todos_pending'] > stats['todos_completed'] * 2:
        suggestions.append("You have many pending todos - use [cyan]kb search --type todo[/cyan] to review them")
    
    if not suggestions:
        suggestions.append("Your knowledge base is in great shape! 🌟")
    
    for suggestion in suggestions:
        console.print(f"  • {suggestion}")
    
    console.print()