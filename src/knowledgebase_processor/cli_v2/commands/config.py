"""Config command - Manage knowledge base configuration."""

import click
from pathlib import Path
from typing import Optional
import yaml

from ..utils import console, print_success, print_error, print_info, show_panel, create_table, format_path
from ...services.orchestrator import OrchestratorService


@click.command('config')
@click.argument('key', required=False)
@click.argument('value', required=False)
@click.option('--list', '-l', is_flag=True, help='List all configuration values')
@click.option('--edit', '-e', is_flag=True, help='Edit configuration file in editor')
@click.option('--reset', is_flag=True, help='Reset to default configuration')
@click.option('--global', 'is_global', is_flag=True, help='Operate on global config')
@click.option('--path', type=click.Path(exists=True), help='Knowledge base path')
@click.pass_obj
def config_cmd(ctx, key, value, list, edit, reset, is_global, path):
    """⚙️ Manage knowledge base configuration.
    
    View, edit, or update configuration settings for your knowledge base.
    Supports both project-specific and global configuration.
    
    \b
    Examples:
      kb config --list                    List all settings
      kb config sparql.endpoint           Show specific setting
      kb config name "My KB"               Set a configuration value
      kb config --edit                    Edit config file
      kb config --global --list           Show global configuration
    """
    console.print(f"\n⚙️ [heading]Configuration Management[/heading]\n")
    
    # Initialize orchestrator service
    orchestrator = OrchestratorService(Path(path) if path else None)
    
    # Check if knowledge base is initialized for local config
    if not is_global and not orchestrator.is_initialized():
        print_error("No knowledge base found. Run 'kb init' first.")
        return
    
    # Determine scope
    scope_name = "Global" if is_global else "Project"
    
    print_info(f"Configuration scope: [cyan]{scope_name}[/cyan]")
    if not is_global:
        config = orchestrator.get_project_config()
        if config:
            console.print(f"📁 Project: {format_path(config.configured_path)}")
    console.print()
    
    # Handle different operations
    if reset:
        if is_global:
            print_error("Global configuration reset not implemented")
            return
        else:
            if click.confirm(f"Reset {scope_name.lower()} configuration to defaults?"):
                # Re-initialize with same project name
                config = orchestrator.get_project_config()
                if config:
                    orchestrator.initialize_project(
                        path=config.configured_path,
                        project_name=config.project_name,
                        force=True
                    )
                    print_success("Configuration reset to defaults")
        return
    
    elif edit:
        # Open config file in editor
        if is_global:
            print_error("Global configuration editing not implemented")
        else:
            kbp_dir = orchestrator._find_kbp_directory()
            if kbp_dir:
                config_path = kbp_dir / "config.yaml"
                try:
                    click.edit(filename=str(config_path))
                    print_success("Configuration file updated")
                except Exception as e:
                    print_error(f"Error opening editor: {e}")
        return
    
    elif list or (not key and not value):
        # List all configuration using orchestrator
        if is_global:
            print_error("Global configuration not implemented")
        else:
            kbp_dir = orchestrator._find_kbp_directory()
            if kbp_dir:
                config_path = kbp_dir / "config.yaml"
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        config_data = yaml.safe_load(f) or {}
                    _display_config(config_data, scope_name)
        return
    
    elif key and not value:
        # Show specific key using orchestrator
        if is_global:
            print_error("Global configuration not implemented")
        else:
            value = orchestrator.get_config_value(key)
            if value is None:
                print_error(f"Configuration key '{key}' not found")
                
                # Suggest similar keys
                kbp_dir = orchestrator._find_kbp_directory()
                if kbp_dir:
                    config_path = kbp_dir / "config.yaml"
                    if config_path.exists():
                        with open(config_path, 'r') as f:
                            config_data = yaml.safe_load(f) or {}
                        all_keys = _get_all_keys(config_data)
                        similar = [k for k in all_keys if key.lower() in k.lower() or k.lower() in key.lower()]
                        
                        if similar:
                            console.print("\n[muted]Similar keys found:[/muted]")
                            for sim_key in similar[:5]:
                                console.print(f"  • {sim_key}")
            else:
                _display_value(key, value)
        return
    
    elif key and value:
        # Set configuration value using orchestrator
        if is_global:
            print_error("Global configuration not implemented")
        else:
            old_value = orchestrator.get_config_value(key)
            success = orchestrator.set_config_value(key, value)
            
            if success:
                print_success(f"Configuration updated: {key} = {value}")
                if old_value is not None:
                    console.print(f"  Previous value: [dim]{old_value}[/dim]")
                    
                # Special handling for SPARQL endpoint configuration
                if key == "sparql.endpoint" or key == "sparql.graph":
                    console.print("\n💡 [subheading]Next steps:[/subheading]")
                    console.print("  • Run [cyan]kb sync[/cyan] to upload to the configured endpoint")
            else:
                print_error(f"Failed to set configuration value")
        return
    
    else:
        click.echo("Invalid arguments. Use --help for usage information.")


def _get_default_config(is_global: bool) -> dict:
    """Get default configuration."""
    if is_global:
        return {
            'editor': 'code',
            'default_patterns': ['**/*.md', '**/*.txt'],
            'output_format': 'table',
            'auto_scan': False,
            'ui_theme': 'default'
        }
    else:
        return {
            'name': 'My Knowledge Base',
            'version': '2.0.0',
            'file_patterns': ['**/*.md', '**/*.txt'],
            'watch_enabled': False,
            'processing': {
                'batch_size': 100,
                'parallel_workers': 4,
                'extract_todos': True,
                'extract_tags': True,
                'extract_links': True
            },
            'search': {
                'fuzzy_matching': True,
                'case_sensitive': False,
                'max_results': 20
            }
        }


def _save_config(config_path: Path, config: dict):
    """Save configuration to file."""
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=True, indent=2)
    except Exception as e:
        print_error(f"Error saving config: {e}")


def _display_config(config: dict, scope_name: str):
    """Display all configuration values."""
    console.print(f"📋 [subheading]{scope_name} Configuration:[/subheading]\n")
    
    if not config:
        print_info("No configuration found")
        return
    
    # Create table for main settings
    table = create_table("Settings", [
        ("Key", "cyan"),
        ("Value", "white"),
        ("Type", "dim white")
    ])
    
    def add_config_items(cfg: dict, prefix: str = ""):
        for key, value in cfg.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                add_config_items(value, full_key)
            else:
                value_str = str(value)
                if len(value_str) > 50:
                    value_str = value_str[:47] + "..."
                
                value_type = type(value).__name__
                table.add_row(full_key, value_str, value_type)
    
    add_config_items(config)
    console.print(table)
    
    # Show usage tips
    console.print(f"\n💡 [subheading]Configuration Tips:[/subheading]")
    console.print("  • View specific setting: [cyan]kb config key.name[/cyan]")
    console.print("  • Update setting: [cyan]kb config key.name \"new value\"[/cyan]") 
    console.print("  • Edit file directly: [cyan]kb config --edit[/cyan]")


def _display_config_key(config: dict, key: str):
    """Display a specific configuration key."""
    # Navigate nested keys
    keys = key.split('.')
    value = config
    
    try:
        for k in keys:
            value = value[k]
    except (KeyError, TypeError):
        print_error(f"Configuration key '{key}' not found")
        
        # Suggest similar keys
        all_keys = _get_all_keys(config)
        similar = [k for k in all_keys if key.lower() in k.lower() or k.lower() in key.lower()]
        
        if similar:
            console.print("\n[muted]Similar keys found:[/muted]")
            for sim_key in similar[:5]:
                console.print(f"  • {sim_key}")
        
        return
    
    _display_value(key, value)


def _display_value(key: str, value):
    """Display a configuration value."""
    # Display the value
    console.print(f"🔧 [subheading]Configuration Value:[/subheading]\n")
    console.print(f"  Key: [cyan]{key}[/cyan]")
    console.print(f"  Value: [white]{value}[/white]")
    console.print(f"  Type: [dim]{type(value).__name__}[/dim]")
    
    if isinstance(value, (list, dict)):
        console.print(f"\n📋 [subheading]Details:[/subheading]")
        import json
        formatted = json.dumps(value, indent=2)
        show_panel(formatted, title="Value Details", style="dim")


def _set_config_value(config: dict, config_path: Path, key: str, value: str):
    """Set a configuration value."""
    # Navigate to the parent of the target key
    keys = key.split('.')
    target = config
    
    # Create nested structure if needed
    for k in keys[:-1]:
        if k not in target:
            target[k] = {}
        elif not isinstance(target[k], dict):
            print_error(f"Cannot set '{key}': parent '{k}' is not a dict")
            return
        target = target[k]
    
    final_key = keys[-1]
    old_value = target.get(final_key)
    
    # Try to preserve type if the key already exists
    if old_value is not None:
        try:
            if isinstance(old_value, bool):
                # Handle boolean values
                if value.lower() in ('true', '1', 'yes', 'on'):
                    new_value = True
                elif value.lower() in ('false', '0', 'no', 'off'):
                    new_value = False
                else:
                    print_error(f"Invalid boolean value: {value}")
                    return
            elif isinstance(old_value, int):
                new_value = int(value)
            elif isinstance(old_value, float):
                new_value = float(value)
            elif isinstance(old_value, list):
                # Handle lists (comma-separated values)
                new_value = [item.strip() for item in value.split(',')]
            else:
                new_value = value
        except (ValueError, TypeError) as e:
            print_error(f"Type conversion error: {e}")
            return
    else:
        # New key - try to infer type
        if value.lower() in ('true', 'false'):
            new_value = value.lower() == 'true'
        elif value.isdigit():
            new_value = int(value)
        elif ',' in value:
            new_value = [item.strip() for item in value.split(',')]
        else:
            new_value = value
    
    # Set the value
    target[final_key] = new_value
    
    # Save configuration
    _save_config(config_path, config)
    
    # Show confirmation
    print_success(f"Configuration updated: {key} = {new_value}")
    
    if old_value is not None:
        console.print(f"  Previous value: [dim]{old_value}[/dim]")


def _get_all_keys(config: dict, prefix: str = "") -> list:
    """Get all configuration keys (flattened)."""
    keys = []
    for key, value in config.items():
        full_key = f"{prefix}.{key}" if prefix else key
        keys.append(full_key)
        
        if isinstance(value, dict):
            keys.extend(_get_all_keys(value, full_key))
    
    return keys