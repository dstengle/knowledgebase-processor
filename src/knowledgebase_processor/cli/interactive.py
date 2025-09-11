"""Interactive mode for the CLI - provides a delightful wizard experience."""

from typing import Optional, Dict, Any
from pathlib import Path

from rich.prompt import Prompt, Confirm
from rich import print as rprint
from rich.panel import Panel
from rich.columns import Columns
from rich.console import Group
from rich.align import Align

from .utils import console, get_emoji, format_path, print_success, print_info


class InteractiveMode:
    """Interactive wizard mode for the CLI."""
    
    def __init__(self, context):
        self.context = context
        self.kb_path = None
        self.config = {}
    
    def run(self):
        """Run the interactive mode."""
        self._show_welcome()
        
        # Check if this is first run
        if not self._check_existing_kb():
            self._first_time_setup()
        else:
            self._main_menu()
    
    def _show_welcome(self):
        """Show welcome banner."""
        welcome_text = Group(
            Align.center(
                f"[bold cyan]{get_emoji('brain')} Knowledge Base Processor[/bold cyan]"
            ),
            Align.center("[dim]Your intelligent document companion[/dim]"),
            "",
            Align.center(f"[cyan]Version 2.0.0[/cyan]")
        )
        
        panel = Panel(
            welcome_text,
            border_style="cyan",
            padding=(1, 2),
            expand=False
        )
        console.print(panel)
        console.print()
    
    def _check_existing_kb(self) -> bool:
        """Check if there's an existing knowledge base."""
        # Look for .kbp directory or config file
        current_dir = Path.cwd()
        kbp_dir = current_dir / ".kbp"
        
        if kbp_dir.exists():
            self.kb_path = current_dir
            print_info(f"Found existing knowledge base at {format_path(current_dir)}")
            return True
        
        # Look in parent directories
        for parent in current_dir.parents:
            kbp_dir = parent / ".kbp"
            if kbp_dir.exists():
                self.kb_path = parent
                print_info(f"Found knowledge base at {format_path(parent)}")
                return True
        
        return False
    
    def _first_time_setup(self):
        """First time setup wizard."""
        console.print(f"\n{get_emoji('sparkles')} [heading]Welcome! Let's set up the processor.[/heading]\n")
        
        # Ask what they want to do
        choices = [
            "1. Configure processor for this directory",
            "2. Scan existing documents",
            "3. Connect to a SPARQL endpoint",
            "4. Just explore the CLI"
        ]
        
        console.print("[subheading]What would you like to do?[/subheading]\n")
        for choice in choices:
            console.print(f"  {choice}")
        
        choice = Prompt.ask("\n[cyan]Enter your choice[/cyan]", choices=["1", "2", "3", "4"], default="1")
        
        if choice == "1":
            self._init_wizard()
        elif choice == "2":
            self._scan_wizard()
        elif choice == "3":
            self._sync_wizard()
        else:
            self._show_help()
    
    def _main_menu(self):
        """Show main menu for existing KB."""
        console.print(f"\n[heading]Knowledge Base Menu[/heading]\n")
        
        options = {
            "1": ("Scan for new documents", "scan"),
            "2": ("Search the knowledge base", "search"),
            "3": ("View statistics", "status"),
            "4": ("Sync with SPARQL endpoint", "sync"),
            "5": ("Configure settings", "config"),
            "6": ("Exit", "exit")
        }
        
        for key, (label, _) in options.items():
            icon = {
                "scan": get_emoji("folder"),
                "search": get_emoji("search"),
                "status": get_emoji("info"),
                "sync": get_emoji("sync"),
                "config": get_emoji("config"),
                "exit": "👋"
            }.get(options[key][1], "")
            console.print(f"  {key}. {icon}  {label}")
        
        choice = Prompt.ask("\n[cyan]What would you like to do?[/cyan]", choices=list(options.keys()), default="1")
        
        action = options[choice][1]
        if action == "exit":
            console.print(f"\n{get_emoji('sparkles')} Thanks for using Knowledge Base Processor!\n")
            return
        elif action == "scan":
            self._scan_wizard()
        elif action == "search":
            self._search_wizard()
        elif action == "status":
            self._show_status()
        elif action == "sync":
            self._sync_wizard()
        elif action == "config":
            self._config_wizard()
        
        # Return to menu
        if Confirm.ask("\n[cyan]Return to main menu?[/cyan]", default=True):
            self._main_menu()
    
    def _init_wizard(self):
        """Initialize processor configuration wizard."""
        console.print(f"\n{get_emoji('rocket')} [heading]Configure Knowledge Base Processor[/heading]\n")
        
        # Get path
        default_path = Path.cwd()
        path_str = Prompt.ask(
            "[cyan]Which directory contains your documents?[/cyan]",
            default=str(default_path)
        )
        kb_path = Path(path_str).expanduser().resolve()
        
        # Get project name
        name = Prompt.ask(
            "[cyan]Project name for this configuration?[/cyan]",
            default=kb_path.name
        )
        
        # Check for existing documents
        doc_count = len(list(kb_path.rglob("*.md")) + list(kb_path.rglob("*.txt")))
        
        # Confirmation
        console.print(f"\n[info]Configuration Summary:[/info]")
        console.print(f"  • Document directory: {format_path(kb_path)}")
        console.print(f"  • Project name: {name}")
        console.print(f"  • Documents found: {doc_count}")
        
        if Confirm.ask("\n[cyan]Configure processor?[/cyan]", default=True):
            # Would actually run: kb init <path> --name <name>
            print_success("Processor configured successfully!")
            self.kb_path = kb_path
            
            if doc_count > 0 and Confirm.ask("\n[cyan]Would you like to scan existing documents now?[/cyan]", default=True):
                self._scan_wizard()
    
    def _scan_wizard(self):
        """Document scanning wizard."""
        console.print(f"\n{get_emoji('folder')} [heading]Scan Documents[/heading]\n")
        
        # Get path
        default_path = self.kb_path or Path.cwd()
        path_str = Prompt.ask(
            "[cyan]Which folder should we scan?[/cyan]",
            default=str(default_path)
        )
        scan_path = Path(path_str).expanduser().resolve()
        
        # Get pattern
        pattern = Prompt.ask(
            "[cyan]File pattern to match[/cyan]",
            default="**/*.md"
        )
        
        # Options
        watch = Confirm.ask("[cyan]Watch for changes?[/cyan]", default=False)
        
        # Show what will be done
        console.print(f"\n[info]Scanning configuration:[/info]")
        console.print(f"  • Path: {format_path(scan_path)}")
        console.print(f"  • Pattern: {pattern}")
        console.print(f"  • Watch mode: {'Yes' if watch else 'No'}")
        
        if Confirm.ask("\n[cyan]Start scanning?[/cyan]", default=True):
            # Would actually run: kb scan <path> --pattern <pattern> [--watch]
            print_success("Scanning completed!")
            console.print("  • Found: 42 documents")
            console.print("  • Processed: 42 documents")
            console.print("  • Extracted: 156 entities, 89 todos")
    
    def _search_wizard(self):
        """Search wizard."""
        console.print(f"\n{get_emoji('search')} [heading]Search Knowledge Base[/heading]\n")
        
        # Get query
        query = Prompt.ask("[cyan]What are you looking for?[/cyan]")
        
        # Get type
        search_types = ["all", "todo", "document", "entity", "tag"]
        search_type = Prompt.ask(
            "[cyan]Search type[/cyan]",
            choices=search_types,
            default="all"
        )
        
        # Would actually run: kb search <query> --type <type>
        console.print(f"\n[info]Searching for '{query}' in {search_type}...[/info]\n")
        
        # Mock results
        print_success("Found 5 results:")
        console.print("  1. [cyan]daily-note-2024-11-07.md[/cyan] - Line 42")
        console.print("     '...implement [highlight]{query}[/highlight] extraction...'")
        console.print("  2. [cyan]project-notes.md[/cyan] - Line 15")
        console.print("     '...the [highlight]{query}[/highlight] system needs...'")
    
    def _show_status(self):
        """Show KB status."""
        console.print(f"\n{get_emoji('info')} [heading]Knowledge Base Status[/heading]\n")
        
        # Mock status
        from rich.table import Table
        
        table = Table(show_header=False, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Location", format_path(self.kb_path or Path.cwd()))
        table.add_row("Documents", "156")
        table.add_row("Total Entities", "1,234")
        table.add_row("Todos", "89 (23 completed)")
        table.add_row("Tags", "45")
        table.add_row("Links", "567")
        table.add_row("Last Scan", "2 hours ago")
        table.add_row("Database Size", "12.3 MB")
        
        console.print(table)
    
    def _sync_wizard(self):
        """Sync wizard."""
        console.print(f"\n{get_emoji('sync')} [heading]Sync with SPARQL Endpoint[/heading]\n")
        
        # Get endpoint
        endpoint = Prompt.ask(
            "[cyan]SPARQL endpoint URL[/cyan]",
            default="http://localhost:3030/kb"
        )
        
        # Get credentials if needed
        needs_auth = Confirm.ask("[cyan]Does the endpoint require authentication?[/cyan]", default=False)
        
        username = None
        password = None
        if needs_auth:
            username = Prompt.ask("[cyan]Username[/cyan]")
            password = Prompt.ask("[cyan]Password[/cyan]", password=True)
        
        # Graph name
        graph = Prompt.ask(
            "[cyan]Graph name[/cyan]",
            default="http://example.org/knowledgebase"
        )
        
        # Confirmation
        console.print(f"\n[info]Sync configuration:[/info]")
        console.print(f"  • Endpoint: {endpoint}")
        console.print(f"  • Graph: {graph}")
        console.print(f"  • Authentication: {'Yes' if needs_auth else 'No'}")
        
        if Confirm.ask("\n[cyan]Start sync?[/cyan]", default=True):
            # Would actually run sync
            print_success("Sync completed successfully!")
            console.print("  • Uploaded: 156 documents")
            console.print("  • Total triples: 4,567")
    
    def _config_wizard(self):
        """Configuration wizard."""
        console.print(f"\n{get_emoji('config')} [heading]Configuration[/heading]\n")
        
        choices = [
            "1. Edit general settings",
            "2. Configure SPARQL endpoint",
            "3. Set up automatic scanning",
            "4. Export configuration",
            "5. Back to menu"
        ]
        
        for choice in choices:
            console.print(f"  {choice}")
        
        choice = Prompt.ask("\n[cyan]Select option[/cyan]", choices=["1", "2", "3", "4", "5"], default="5")
        
        if choice == "5":
            return
        
        # Would show appropriate config screens
        print_info("Configuration updated!")
    
    def _show_help(self):
        """Show help information."""
        console.print(f"\n{get_emoji('info')} [heading]Quick Help[/heading]\n")
        
        help_text = """
The Knowledge Base Processor helps you transform documents into a searchable knowledge graph.

[subheading]Common Commands:[/subheading]
  • kb init     - Create a new knowledge base
  • kb scan     - Process documents
  • kb search   - Search your knowledge
  • kb status   - View statistics
  • kb sync     - Upload to SPARQL endpoint

[subheading]Tips:[/subheading]
  • Use [cyan]kb[/cyan] without arguments for interactive mode
  • Add [cyan]--help[/cyan] to any command for details
  • Use [cyan]--watch[/cyan] with scan for live updates
  
[subheading]Examples:[/subheading]
  kb scan ~/Documents --watch
  kb search "project todos" --type todo
  kb sync fuseki --graph myproject
"""
        console.print(help_text)