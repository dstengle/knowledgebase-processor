"""Integration tests for the orchestrator service."""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from knowledgebase_processor.services.orchestrator import (
    OrchestratorService, 
    ProcessingResult, 
    SearchResult, 
    ProjectStats, 
    ProjectConfig
)


class TestOrchestratorIntegration:
    """Integration tests for orchestrator service with real file operations."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary directory with sample documents."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create sample markdown files
        (temp_dir / "doc1.md").write_text("""# Project Overview

This is our main project documentation.

- [ ] Implement user authentication
- [x] Setup database schema
- [ ] Create API endpoints

Key points:
- Use FastAPI framework
- PostgreSQL database
- JWT authentication

## Architecture

The system consists of three main components.
""")
        
        (temp_dir / "doc2.md").write_text("""# Meeting Notes

## Daily Standup 2024-01-15

- [ ] Review pull requests
- [ ] Update documentation
- [x] Deploy to staging

### Decisions
- Migration to new framework approved
- Timeline: 2 weeks

Links: [[project-overview]] and [[architecture-decisions]]
""")
        
        (temp_dir / "notes.txt").write_text("""Development Notes

Important considerations:
- Security first approach
- Performance benchmarks
- User experience focus

TODO: Schedule code review session
""")
        
        # Create subdirectory with more files
        subdir = temp_dir / "archive"
        subdir.mkdir()
        (subdir / "old-notes.md").write_text("""# Archived Notes

Historical project information.

- [x] Migrated from old system
- [ ] Archive cleanup needed
""")
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_orchestrator_initialization(self, temp_project_dir):
        """Test orchestrator service initialization."""
        orchestrator = OrchestratorService(temp_project_dir)
        
        # Should not be initialized initially
        assert not orchestrator.is_initialized()
        assert orchestrator.get_project_config() is None
        
        # Working directory should be set
        assert orchestrator.working_directory == temp_project_dir
    
    def test_project_initialization(self, temp_project_dir):
        """Test project initialization creates proper configuration."""
        orchestrator = OrchestratorService(temp_project_dir)
        
        # Initialize project
        config = orchestrator.initialize_project(
            path=temp_project_dir,
            project_name="Test Project",
            file_patterns=["**/*.md", "**/*.txt"],
            watch_enabled=True,
            sparql_endpoint="http://localhost:3030/test",
            sparql_graph="http://example.org/test"
        )
        
        # Verify configuration
        assert config.project_name == "Test Project"
        assert config.configured_path == temp_project_dir
        assert config.file_patterns == ["**/*.md", "**/*.txt"]
        assert config.watch_enabled is True
        assert config.sparql_endpoint == "http://localhost:3030/test"
        assert config.sparql_graph == "http://example.org/test"
        
        # Verify directories were created
        kbp_dir = temp_project_dir / ".kbp"
        assert kbp_dir.exists()
        assert (kbp_dir / "cache").exists()
        assert (kbp_dir / "logs").exists()
        assert (kbp_dir / "config.yaml").exists()
        
        # Should now be initialized
        assert orchestrator.is_initialized()
    
    def test_project_initialization_force_overwrite(self, temp_project_dir):
        """Test force overwrite of existing project."""
        orchestrator = OrchestratorService(temp_project_dir)
        
        # Initialize project first time
        orchestrator.initialize_project(
            path=temp_project_dir,
            project_name="Original Project",
            watch_enabled=False
        )
        
        # Try to initialize again without force - should fail
        with pytest.raises(ValueError, match="already initialized"):
            orchestrator.initialize_project(
                path=temp_project_dir,
                project_name="New Project"
            )
        
        # Initialize with force - should succeed
        config = orchestrator.initialize_project(
            path=temp_project_dir,
            project_name="New Project",
            watch_enabled=True,
            force=True
        )
        
        assert config.project_name == "New Project"
        assert config.watch_enabled is True
    
    def test_document_counting(self, temp_project_dir):
        """Test document counting with different patterns."""
        orchestrator = OrchestratorService(temp_project_dir)
        orchestrator.initialize_project(temp_project_dir, "Test Project")
        
        # Count all markdown files
        md_count = orchestrator.count_documents(["**/*.md"])
        assert md_count == 3  # doc1.md, doc2.md, archive/old-notes.md
        
        # Count all text files
        txt_count = orchestrator.count_documents(["**/*.txt"])
        assert txt_count == 1  # notes.txt
        
        # Count all files
        all_count = orchestrator.count_documents(["**/*.md", "**/*.txt"])
        assert all_count == 4
        
        # Count with different orchestrator instance (already initialized)
        orchestrator2 = OrchestratorService(temp_project_dir)
        
        # Should be able to count documents in subdirectories too
        total_docs = orchestrator.count_documents()
        assert total_docs >= 3  # At least the main directory files
    
    def test_document_processing(self, temp_project_dir):
        """Test document processing integration."""
        orchestrator = OrchestratorService(temp_project_dir)
        orchestrator.initialize_project(temp_project_dir, "Test Project")
        
        # Process documents
        result = orchestrator.process_documents()
        
        # Verify result structure
        assert isinstance(result, ProcessingResult)
        assert result.files_processed >= 0
        assert result.files_failed >= 0
        assert result.entities_extracted >= 0
        assert result.todos_found >= 0
        assert result.processing_time > 0
        assert isinstance(result.error_messages, list)
        
        # Should have processed some files
        total_files = orchestrator.count_documents()
        if total_files > 0:
            # Either processed successfully or failed
            assert result.files_processed + result.files_failed > 0
    
    def test_search_functionality(self, temp_project_dir):
        """Test search functionality."""
        orchestrator = OrchestratorService(temp_project_dir)
        orchestrator.initialize_project(temp_project_dir, "Test Project")
        
        # Process documents first
        orchestrator.process_documents()
        
        # Search for content
        results = orchestrator.search("authentication", limit=5)
        
        # Verify result structure
        assert isinstance(results, list)
        for result in results:
            assert isinstance(result, SearchResult)
            assert hasattr(result, 'type')
            assert hasattr(result, 'title')
            assert hasattr(result, 'path')
            assert hasattr(result, 'snippet')
            assert hasattr(result, 'score')
    
    def test_project_stats(self, temp_project_dir):
        """Test project statistics gathering."""
        orchestrator = OrchestratorService(temp_project_dir)
        orchestrator.initialize_project(temp_project_dir, "Test Project")
        
        # Get stats
        stats = orchestrator.get_project_stats()
        
        # Verify stats structure
        assert isinstance(stats, ProjectStats)
        assert stats.total_documents > 0
        assert stats.processed_documents >= 0
        assert stats.failed_documents >= 0
        assert stats.total_entities >= 0
        assert stats.todos_total >= 0
        assert stats.todos_completed >= 0
        assert stats.todos_pending >= 0
        assert stats.tags >= 0
        assert stats.wikilinks >= 0
        assert stats.database_size >= 0
        assert stats.processing_time >= 0
        
        # Last scan might be None if no processing yet
        if stats.last_scan:
            assert isinstance(stats.last_scan, datetime)
    
    def test_configuration_management(self, temp_project_dir):
        """Test configuration get/set operations."""
        orchestrator = OrchestratorService(temp_project_dir)
        orchestrator.initialize_project(temp_project_dir, "Test Project")
        
        # Test getting configuration values
        project_name = orchestrator.get_config_value("project_name")
        assert project_name == "Test Project"
        
        version = orchestrator.get_config_value("version")
        assert version == "2.0.0"
        
        # Test getting nested values
        patterns = orchestrator.get_config_value("file_patterns")
        assert isinstance(patterns, list)
        
        # Test getting non-existent values
        non_existent = orchestrator.get_config_value("non_existent", "default")
        assert non_existent == "default"
        
        # Test setting configuration values
        success = orchestrator.set_config_value("test_setting", "test_value")
        assert success is True
        
        # Verify the value was set
        retrieved = orchestrator.get_config_value("test_setting")
        assert retrieved == "test_value"
        
        # Test setting nested values
        success = orchestrator.set_config_value("nested.setting", "nested_value")
        assert success is True
        
        nested_retrieved = orchestrator.get_config_value("nested.setting")
        assert nested_retrieved == "nested_value"
    
    def test_sparql_sync_configuration(self, temp_project_dir):
        """Test SPARQL sync configuration and error handling."""
        orchestrator = OrchestratorService(temp_project_dir)
        orchestrator.initialize_project(
            temp_project_dir, 
            "Test Project",
            sparql_endpoint="http://localhost:3030/test"
        )
        
        # Test sync with configured endpoint
        # This will likely fail since we don't have a real SPARQL endpoint
        # but it should handle the error gracefully
        result = orchestrator.sync_to_sparql()
        
        # Verify result structure
        assert isinstance(result, dict)
        assert "success" in result
        assert "sync_time" in result
        
        if not result["success"]:
            assert "error" in result
    
    def test_uninitialized_operations(self, temp_project_dir):
        """Test operations on uninitialized project."""
        orchestrator = OrchestratorService(temp_project_dir)
        
        # Operations should fail gracefully
        assert orchestrator.get_project_config() is None
        assert orchestrator.get_project_stats() is None
        
        # These should raise ValueError
        with pytest.raises(ValueError, match="not initialized"):
            orchestrator.process_documents()
        
        with pytest.raises(ValueError, match="not initialized"):
            orchestrator.search("test")
        
        with pytest.raises(ValueError, match="not initialized"):
            orchestrator.sync_to_sparql()
    
    def test_config_caching(self, temp_project_dir):
        """Test configuration caching behavior."""
        orchestrator = OrchestratorService(temp_project_dir)
        orchestrator.initialize_project(temp_project_dir, "Test Project")
        
        # Get config first time (should cache)
        config1 = orchestrator.get_project_config()
        
        # Get config second time (should use cache)
        config2 = orchestrator.get_project_config()
        
        # Should be the same object (cached)
        assert config1 is config2
        
        # After setting a config value, cache should be cleared
        orchestrator.set_config_value("test", "value")
        
        # Get config again (should reload)
        config3 = orchestrator.get_project_config()
        
        # Should be different object (cache cleared)
        assert config1 is not config3