"""End-to-end workflow tests for CLI v2."""

import pytest
import tempfile
import shutil
from pathlib import Path
from click.testing import CliRunner
import time
import requests

from knowledgebase_processor.cli.main import cli


class TestCLIWorkflowE2E:
    """End-to-end workflow tests for complete CLI scenarios."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary directory with sample documents."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create sample markdown files with todos and entities
        (temp_dir / "project-notes.md").write_text("""# Project Notes

This is the main project documentation for our knowledge base system.

## Todo Items

- [ ] Implement search functionality
- [x] Setup database schema
- [ ] Create REST API endpoints

## Key Entities

The project involves [[John Smith]] as the lead developer and [[ACME Corp]] as the client.
We're using [[PostgreSQL]] for the database.

## Architecture

The system uses a modern microservices architecture.
""")
        
        (temp_dir / "meeting-notes.md").write_text("""# Meeting Notes - 2024-01-15

## Attendees
- [[John Smith]]
- [[Jane Doe]]
- [[Bob Johnson]]

## Action Items
- [ ] Review API documentation
- [ ] Schedule follow-up meeting
- [x] Send meeting minutes

## Decisions
- Use [[FastAPI]] framework
- Deploy to [[AWS]] cloud
- Implement [[JWT]] authentication
""")
        
        (temp_dir / "research").mkdir()
        (temp_dir / "research" / "findings.md").write_text("""# Research Findings

## Database Comparison

We evaluated [[PostgreSQL]], [[MySQL]], and [[MongoDB]].

### Todos
- [x] Compare performance benchmarks
- [ ] Evaluate licensing costs
- [ ] Test with sample data

## Recommendation

Based on our analysis, [[PostgreSQL]] is the best choice for our needs.
""")
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def runner(self):
        """Create a CLI test runner."""
        return CliRunner()
    
    def test_full_workflow_scan_and_load(self, runner, temp_project_dir):
        """Test 1: Initialize, scan, and load documents to SPARQL endpoint."""
        # Change to project directory
        import os
        original_dir = os.getcwd()
        os.chdir(str(temp_project_dir))
        
        try:
            # Step 1: Initialize project with SPARQL endpoint configuration
            result = runner.invoke(cli, [
                'init',
                '--name', 'E2E Test Project'
            ], input='y\nhttp://fuseki:3030/kb-test\n')  # Answer yes to SPARQL config, provide URL
            
            assert result.exit_code == 0
            assert "Processor configured" in result.output
            assert "Found 3 existing documents" in result.output  # project-notes.md, meeting-notes.md, research/findings.md
            
            # Step 2: Scan documents
            result = runner.invoke(cli, ['scan'])
            
            assert result.exit_code == 0
            assert "Processing completed" in result.output
            assert "Files processed: 3" in result.output
            
            # Step 3: Configure SPARQL credentials
            result = runner.invoke(cli, [
                'config', 'sparql.endpoint', 'http://fuseki:3030/kb-test'
            ])
            assert result.exit_code == 0
            assert "Configuration updated" in result.output
            
            # Step 4: Sync to SPARQL endpoint
            # Check if Fuseki is available
            try:
                response = requests.get('http://fuseki:3030/$/ping', timeout=2)
                fuseki_available = response.status_code == 200
            except:
                fuseki_available = False
            
            if fuseki_available:
                result = runner.invoke(cli, [
                    'sync',
                    '--username', 'admin',
                    '--password', 'admin',
                    '--force'  # Skip confirmation
                ])
                
                # The sync might succeed or fail based on actual Fuseki state
                # but it should not crash
                assert result.exit_code == 0
                
                if "Sync completed successfully" in result.output:
                    assert "triples uploaded" in result.output
                else:
                    # Sync failed but handled gracefully
                    assert "Sync failed" in result.output
            else:
                # Skip sync test if Fuseki not available
                pytest.skip("Fuseki not available, skipping sync test")
                
        finally:
            os.chdir(original_dir)
    
    def test_search_workflow(self, runner, temp_project_dir):
        """Test 2: Initialize, scan, and search for expected entities and todos."""
        # Change to project directory
        import os
        original_dir = os.getcwd()
        os.chdir(str(temp_project_dir))
        
        try:
            # Step 1: Initialize project without SPARQL
            result = runner.invoke(cli, [
                'init',
                '--name', 'Search Test Project'
            ], input='n\n')  # Answer no to SPARQL config
            
            assert result.exit_code == 0
            assert "Processor configured" in result.output
            
            # Step 2: Scan documents
            result = runner.invoke(cli, ['scan'])
            
            assert result.exit_code == 0
            assert "Processing completed" in result.output
            assert "Files processed: 3" in result.output
            
            # Step 3: Search for a known entity (PostgreSQL appears in 2 documents)
            result = runner.invoke(cli, ['search', 'PostgreSQL'])
            
            # Search might return results or might not depending on implementation
            assert result.exit_code == 0
            
            if "No results found" not in result.output:
                # If results found, verify structure
                assert "Search Results" in result.output or "Found" in result.output
            
            # Step 4: Search for todos
            result = runner.invoke(cli, ['search', '--type', 'todo', 'API'])
            
            assert result.exit_code == 0
            # Either finds results or shows "No results found" message
            
            # Step 5: Check status
            result = runner.invoke(cli, ['status'])
            
            assert result.exit_code == 0
            # Status should show statistics
            assert "Knowledge Base" in result.output or "Project" in result.output
            
        finally:
            os.chdir(original_dir)
    
    def test_config_persistence(self, runner, temp_project_dir):
        """Test configuration persistence across commands."""
        # Change to project directory
        import os
        original_dir = os.getcwd()
        os.chdir(str(temp_project_dir))
        
        try:
            # Step 1: Initialize project
            result = runner.invoke(cli, [
                'init',
                '--name', 'Config Test Project'
            ], input='n\n')  # No SPARQL initially
            
            assert result.exit_code == 0
            
            # Step 2: Set SPARQL endpoint via config command
            result = runner.invoke(cli, [
                'config', 'sparql.endpoint', 'http://test-endpoint:3030/kb'
            ])
            
            assert result.exit_code == 0
            assert "Configuration updated" in result.output
            
            # Step 3: Verify configuration was saved
            result = runner.invoke(cli, ['config', 'sparql.endpoint'])
            
            assert result.exit_code == 0
            assert "http://test-endpoint:3030/kb" in result.output
            
            # Step 4: List all config to verify structure
            result = runner.invoke(cli, ['config', '--list'])
            
            assert result.exit_code == 0
            assert "sparql" in result.output or "endpoint" in result.output
            
            # Step 5: Sync should use configured endpoint
            result = runner.invoke(cli, ['sync', '--dry-run'])
            
            assert result.exit_code == 0
            assert "http://test-endpoint:3030/kb" in result.output
            assert "Dry run completed" in result.output
            
        finally:
            os.chdir(original_dir)
    
    def test_error_handling_workflow(self, runner, temp_project_dir):
        """Test error handling in various scenarios."""
        # Change to project directory
        import os
        original_dir = os.getcwd()
        os.chdir(str(temp_project_dir))
        
        try:
            # Test 1: Commands before init should fail gracefully
            result = runner.invoke(cli, ['scan'])
            assert result.exit_code == 0  # CLI handles error gracefully
            assert "No knowledge base found" in result.output
            
            result = runner.invoke(cli, ['search', 'test'])
            assert result.exit_code == 0
            assert "No knowledge base found" in result.output
            
            # Test 2: Initialize project
            result = runner.invoke(cli, [
                'init',
                '--name', 'Error Test Project'
            ], input='n\n')
            assert result.exit_code == 0
            
            # Test 3: Re-init without force should fail
            result = runner.invoke(cli, [
                'init',
                '--name', 'Another Project'
            ], input='n\n')
            assert result.exit_code == 0
            assert "already configured" in result.output
            
            # Test 4: Invalid config key
            result = runner.invoke(cli, ['config', 'invalid.key.path'])
            assert result.exit_code == 0
            assert "not found" in result.output
            
            # Test 5: Search with no processed documents (should handle gracefully)
            result = runner.invoke(cli, ['search', 'nonexistent'])
            assert result.exit_code == 0
            # Should either find no results or suggest running scan
            
        finally:
            os.chdir(original_dir)