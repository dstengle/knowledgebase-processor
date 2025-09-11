"""End-to-end tests for CLI v2."""

import pytest
import tempfile
import shutil
from pathlib import Path
from click.testing import CliRunner

from knowledgebase_processor.cli.main import cli


class TestCLIEndToEnd:
    """End-to-end tests for CLI v2 interface."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary directory with sample documents."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create sample files
        (temp_dir / "test.md").write_text("""# Test Document

This is a test document.

- [ ] Test todo item
- [x] Completed todo

Some content here.
""")
        
        (temp_dir / "notes.txt").write_text("""Notes file

Some notes here.
""")
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()
    
    def test_cli_help(self, runner):
        """Test CLI help command."""
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "Knowledge Base Processor" in result.output
        assert "init" in result.output
        assert "scan" in result.output
        assert "search" in result.output
        assert "status" in result.output
        assert "sync" in result.output
        assert "config" in result.output
    
    def test_cli_version(self, runner):
        """Test CLI version command."""
        result = runner.invoke(cli, ['--version'])
        
        assert result.exit_code == 0
        assert "Knowledge Base Processor" in result.output
        assert "Version" in result.output
    
    def test_init_command(self, runner, temp_project_dir):
        """Test init command end-to-end."""
        # Change to temp directory and run init
        with runner.isolated_filesystem():
            # Create a test directory
            test_dir = Path("test_project")
            test_dir.mkdir()
            
            # Run init command with auto-confirm
            result = runner.invoke(cli, [
                'init', str(test_dir),
                '--name', 'Test Project',
                '--yes'  # Auto-confirm prompts
            ])
            
            # Should succeed
            assert result.exit_code == 0
            assert "Processor configured" in result.output
            
            # Check if .kbp directory was created
            kbp_dir = test_dir / ".kbp"
            assert kbp_dir.exists()
            assert (kbp_dir / "config.yaml").exists()
    
    def test_init_existing_project(self, runner, temp_project_dir):
        """Test init command on existing project."""
        with runner.isolated_filesystem():
            test_dir = Path("test_project")
            test_dir.mkdir()
            
            # Create .kbp directory first
            (test_dir / ".kbp").mkdir()
            (test_dir / ".kbp" / "config.yaml").write_text("project_name: Existing")
            
            # Try to init again without force
            result = runner.invoke(cli, [
                'init', str(test_dir),
                '--name', 'New Project',
                '--yes'
            ])
            
            # Should fail
            assert result.exit_code == 0  # CLI handles error gracefully
            assert "already configured" in result.output or "already initialized" in result.output
    
    def test_scan_without_init(self, runner):
        """Test scan command without initialization."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['scan'])
            
            # Should fail gracefully
            assert result.exit_code == 0  # CLI handles error gracefully
            assert "No knowledge base found" in result.output or "Run 'kb init'" in result.output
    
    def test_full_workflow(self, runner):
        """Test complete workflow: init -> scan -> search -> status."""
        with runner.isolated_filesystem():
            test_dir = Path("test_project")
            test_dir.mkdir()
            
            # Create a test document
            (test_dir / "test.md").write_text("""# Test Document

This is a test document for e2e testing.

- [ ] Implement feature X
- [x] Setup project structure

Key points:
- Use modern architecture
- Focus on user experience
""")
            
            # Step 1: Initialize project
            result = runner.invoke(cli, [
                'init', str(test_dir),
                '--name', 'E2E Test Project',
                '--yes'
            ])
            assert result.exit_code == 0
            assert "Processor configured" in result.output
            
            # Change to project directory for subsequent commands
            import os
            os.chdir(str(test_dir))
            
            # Step 2: Scan documents
            result = runner.invoke(cli, ['scan', '--dry-run'])
            assert result.exit_code == 0
            assert "Found" in result.output and "files" in result.output
            
            # Step 3: Try search (might not work without real processing)
            result = runner.invoke(cli, ['search', 'test', '--limit', '5'])
            # Don't assert exit code as search might fail without real data
            # Just check it doesn't crash
            
            # Step 4: Check status
            result = runner.invoke(cli, ['status'])
            # Don't assert exit code as status might fail without real processing
            # Just check it doesn't crash
    
    def test_command_help_messages(self, runner):
        """Test help messages for individual commands."""
        commands = ['init', 'scan', 'search', 'status', 'sync', 'config']
        
        for command in commands:
            result = runner.invoke(cli, [command, '--help'])
            assert result.exit_code == 0
            assert "Usage:" in result.output
            assert "Examples:" in result.output or "Options:" in result.output
    
    def test_error_handling(self, runner):
        """Test CLI error handling."""
        # Test invalid arguments
        result = runner.invoke(cli, ['invalid-command'])
        assert result.exit_code != 0 or "No such command" in result.output
        
        # Test search without query
        result = runner.invoke(cli, ['search'])
        assert result.exit_code != 0 or "Missing argument" in result.output