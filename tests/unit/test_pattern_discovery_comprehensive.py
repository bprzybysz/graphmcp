"""
Comprehensive unit tests for Pattern Discovery System

Tests core functionality to improve coverage:
- Pattern compilation and searching 
- Repository content parsing
- File type classification
- Directory structure analysis
- Error handling scenarios
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import re
from pathlib import Path

from concrete.pattern_discovery import PatternDiscoveryEngine, discover_patterns_step
from concrete.source_type_classifier import SourceType


class TestPatternDiscoveryEngine:
    """Comprehensive tests for PatternDiscoveryEngine functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.engine = PatternDiscoveryEngine()
    
    def test_init(self):
        """Test engine initialization."""
        assert self.engine.classifier is not None
        assert self.engine.database_patterns == {}
    
    def test_compile_database_patterns(self):
        """Test database pattern compilation."""
        database_name = "testdb"
        patterns = self.engine._compile_database_patterns(database_name)
        
        # Verify patterns were generated for multiple source types
        assert isinstance(patterns, dict)
        assert len(patterns) > 0
        
        # Verify pattern structure
        for source_type, pattern_list in patterns.items():
            assert isinstance(source_type, SourceType)
            assert isinstance(pattern_list, list)
            assert all(isinstance(p, str) for p in pattern_list)
    
    def test_search_content_for_patterns(self):
        """Test pattern searching in content."""
        content = """
        database: testdb
        DB_NAME="testdb"
        host: 'testdb'
        """
        
        patterns = [r'\btestdb\b', r'"testdb"', r"'testdb'"]
        matches = self.engine._search_content_for_patterns(content, patterns)
        
        # Verify matches found
        assert len(matches) > 0
        
        # Verify match structure
        for match in matches:
            assert "pattern" in match
            assert "line_number" in match
            assert "line_content" in match
            assert "match_confidence" in match
            assert match["match_confidence"] == 0.8
    
    def test_search_content_for_patterns_no_matches(self):
        """Test pattern searching with no matches."""
        content = "No database references here"
        patterns = [r'\btestdb\b']
        
        matches = self.engine._search_content_for_patterns(content, patterns)
        assert len(matches) == 0
    
    def test_search_content_for_patterns_invalid_regex(self):
        """Test handling of invalid regex patterns."""
        content = "Some content"
        patterns = ["[invalid regex"]  # Invalid regex
        
        # Should not raise exception, should skip invalid patterns
        matches = self.engine._search_content_for_patterns(content, patterns)
        assert len(matches) == 0
    
    def test_parse_repomix_content(self):
        """Test parsing of Repomix XML content."""
        repomix_content = '''<file path="config.py">
database_url = "postgresql://testdb"
</file>
<file path="deploy.yaml">
name: testdb-service
image: postgres:13
</file>'''
        
        files = self.engine._parse_repomix_content(repomix_content)
        
        assert len(files) == 2
        
        # Verify first file
        assert files[0]["path"] == "config.py"
        assert "database_url" in files[0]["content"]
        assert files[0]["type"] == "python"
        assert files[0]["size"] > 0
        
        # Verify second file
        assert files[1]["path"] == "deploy.yaml"
        assert "testdb-service" in files[1]["content"]
        assert files[1]["type"] == "yaml"
    
    def test_parse_repomix_content_empty(self):
        """Test parsing empty or malformed Repomix content."""
        # Empty content
        files = self.engine._parse_repomix_content("")
        assert len(files) == 0
        
        # Malformed content
        malformed_content = "This is not XML format"
        files = self.engine._parse_repomix_content(malformed_content)
        assert len(files) == 0
    
    def test_get_file_type(self):
        """Test file type classification from path."""
        test_cases = [
            ("main.py", "python"),
            ("app.js", "javascript"),
            ("types.ts", "typescript"),
            ("config.yaml", "yaml"),
            ("config.yml", "yaml"),
            ("data.json", "json"),
            ("query.sql", "sql"),
            ("README.md", "markdown"),
            ("notes.txt", "text"),
            ("app.ini", "config"),
            ("nginx.conf", "config"),
            ("app.env", "environment"),  # Changed from .env to app.env
            ("unknown.xyz", "unknown")
        ]
        
        for file_path, expected_type in test_cases:
            result = self.engine._get_file_type(file_path)
            assert result == expected_type, f"Expected {expected_type} for {file_path}, got {result}"
    
    def test_analyze_file_types(self):
        """Test file type distribution analysis."""
        files = [
            {"type": "python", "path": "app.py"},
            {"type": "python", "path": "config.py"},
            {"type": "yaml", "path": "deploy.yaml"},
            {"type": "json", "path": "package.json"},
            {"type": "unknown", "path": "weird.xyz"}
        ]
        
        type_counts = self.engine._analyze_file_types(files)
        
        assert type_counts["python"] == 2
        assert type_counts["yaml"] == 1
        assert type_counts["json"] == 1
        assert type_counts["unknown"] == 1
    
    def test_analyze_file_types_empty(self):
        """Test file type analysis with empty list."""
        type_counts = self.engine._analyze_file_types([])
        assert type_counts == {}
    
    def test_analyze_directory_structure(self):
        """Test directory structure analysis."""
        files = [
            {"path": "src/main.py"},
            {"path": "src/utils/helper.py"},
            {"path": "tests/test_main.py"},
            {"path": "docs/README.md"},
            {"path": "config.yaml"}
        ]
        
        structure = self.engine._analyze_directory_structure(files)
        
        assert "total_directories" in structure
        assert "max_depth" in structure
        assert "depth_distribution" in structure
        
        # Verify depth analysis
        assert structure["max_depth"] == 2  # src/utils/helper.py has depth 2
        assert structure["total_directories"] > 0
        
        # Verify depth distribution
        depth_dist = structure["depth_distribution"]
        assert 0 in depth_dist  # config.yaml at root
        assert 1 in depth_dist  # src/main.py, tests/test_main.py, docs/README.md
        assert 2 in depth_dist  # src/utils/helper.py
    
    def test_analyze_directory_structure_empty(self):
        """Test directory structure analysis with empty files."""
        structure = self.engine._analyze_directory_structure([])
        
        assert structure["total_directories"] == 0
        assert structure["max_depth"] == 0
        assert structure["depth_distribution"] == {}
    
    @pytest.mark.asyncio
    async def test_analyze_repository_structure_success(self):
        """Test successful repository structure analysis."""
        # Mock repomix client
        mock_client = AsyncMock()
        mock_client.pack_remote_repository.return_value = {"output_id": "test123"}
        mock_client.read_repomix_output.return_value = {
            "content": '''<file path="config.py">
database_url = "postgresql://testdb"
</file>'''
        }
        
        result = await self.engine.analyze_repository_structure(
            mock_client, "https://github.com/test/repo", "test", "repo"
        )
        
        # Verify successful analysis
        assert "files" in result
        assert "structure" in result
        assert "total_size" in result
        assert "output_id" in result
        
        assert len(result["files"]) == 1
        assert result["files"][0]["path"] == "config.py"
        
        # Verify client calls
        mock_client.pack_remote_repository.assert_called_once()
        mock_client.read_repomix_output.assert_called_once_with(output_id="test123")
    
    @pytest.mark.asyncio
    async def test_analyze_repository_structure_pack_failure(self):
        """Test repository analysis when pack fails."""
        mock_client = AsyncMock()
        mock_client.pack_remote_repository.return_value = None
        
        result = await self.engine.analyze_repository_structure(
            mock_client, "https://github.com/test/repo", "test", "repo"
        )
        
        # Should return empty result
        assert result["files"] == []
        assert result["structure"] == {}
        assert result["total_size"] == 0
    
    @pytest.mark.asyncio
    async def test_analyze_repository_structure_read_failure(self):
        """Test repository analysis when read fails."""
        mock_client = AsyncMock()
        mock_client.pack_remote_repository.return_value = {"output_id": "test123"}
        mock_client.read_repomix_output.return_value = None
        
        result = await self.engine.analyze_repository_structure(
            mock_client, "https://github.com/test/repo", "test", "repo"
        )
        
        # Should return empty result
        assert result["files"] == []
        assert result["structure"] == {}
        assert result["total_size"] == 0
    
    @pytest.mark.asyncio
    async def test_analyze_repository_structure_exception(self):
        """Test repository analysis with exception."""
        mock_client = AsyncMock()
        mock_client.pack_remote_repository.side_effect = Exception("Pack failed")
        
        result = await self.engine.analyze_repository_structure(
            mock_client, "https://github.com/test/repo", "test", "repo"
        )
        
        # Should return error result
        assert result["files"] == []
        assert result["structure"] == {}
        assert result["total_size"] == 0
        assert "error" in result
        assert "Pack failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_discover_patterns_in_repository_success(self):
        """Test successful pattern discovery in repository."""
        # Setup mock clients
        mock_repomix = AsyncMock()
        mock_github = AsyncMock()
        
        # Mock repository analysis
        with patch.object(self.engine, 'analyze_repository_structure') as mock_analyze:
            mock_analyze.return_value = {
                "files": [
                    {
                        "path": "config.py",
                        "content": 'DB_NAME = "testdb"',
                        "type": "python"
                    }
                ],
                "structure": {"total_files": 1},
                "total_size": 100
            }
            
            # Mock pattern compilation
            with patch.object(self.engine, '_compile_database_patterns') as mock_compile:
                mock_compile.return_value = {
                    SourceType.PYTHON: [r'\btestdb\b', r'"testdb"']
                }
                
                result = await self.engine.discover_patterns_in_repository(
                    mock_repomix, mock_github,
                    "https://github.com/test/repo",
                    "testdb", "test", "repo"
                )
        
        # Verify successful discovery
        assert result["database_name"] == "testdb"
        assert result["repository"] == "test/repo"
        assert result["total_files"] == 1
        assert result["matched_files"] > 0
        assert len(result["files"]) > 0
        
        # Verify confidence distribution
        conf_dist = result["confidence_distribution"]
        assert "high_confidence" in conf_dist
        assert "medium_confidence" in conf_dist
        assert "low_confidence" in conf_dist
        assert "average_confidence" in conf_dist
    
    @pytest.mark.asyncio
    async def test_discover_patterns_in_repository_no_files(self):
        """Test pattern discovery with no files found."""
        mock_repomix = AsyncMock()
        mock_github = AsyncMock()
        
        with patch.object(self.engine, 'analyze_repository_structure') as mock_analyze:
            mock_analyze.return_value = {
                "files": [],
                "structure": {},
                "total_size": 0
            }
            
            result = await self.engine.discover_patterns_in_repository(
                mock_repomix, mock_github,
                "https://github.com/test/repo",
                "testdb", "test", "repo"
            )
        
        # Should return empty results
        assert result["total_files"] == 0
        assert result["matched_files"] == []
        assert result["files_by_type"] == {}
    
    @pytest.mark.asyncio
    async def test_discover_patterns_in_repository_exception(self):
        """Test pattern discovery with exception."""
        mock_repomix = AsyncMock()
        mock_github = AsyncMock()
        
        with patch.object(self.engine, 'analyze_repository_structure') as mock_analyze:
            mock_analyze.side_effect = Exception("Analysis failed")
            
            result = await self.engine.discover_patterns_in_repository(
                mock_repomix, mock_github,
                "https://github.com/test/repo",
                "testdb", "test", "repo"
            )
        
        # Should return error result
        assert result["total_files"] == 0
        assert result["matched_files"] == []
        assert "error" in result
        assert "Analysis failed" in result["error"]


class TestDiscoverPatternsStep:
    """Tests for the discover_patterns_step function."""
    
    @pytest.mark.asyncio
    async def test_discover_patterns_step_success(self):
        """Test successful discover patterns step execution."""
        # Setup mock context
        mock_context = MagicMock()
        mock_context._clients = {}
        mock_context.config.config_path = "/test/path"
        mock_context.set_shared_value = MagicMock()
        
        # Setup mock clients
        mock_repomix = AsyncMock()
        mock_github = AsyncMock()
        
        with patch('clients.RepomixMCPClient') as mock_repomix_class, \
             patch('clients.GitHubMCPClient') as mock_github_class:
            
            mock_repomix_class.return_value = mock_repomix
            mock_github_class.return_value = mock_github
            
            # Mock pattern discovery
            with patch.object(PatternDiscoveryEngine, 'discover_patterns_in_repository') as mock_discover:
                mock_discover.return_value = {
                    "total_files": 10,
                    "matched_files": 3,
                    "files": [],
                    "database_name": "testdb"
                }
                
                result = await discover_patterns_step(
                    mock_context, None, "testdb", "test", "repo"
                )
        
        # Verify successful execution
        assert result["total_files"] == 10
        assert result["matched_files"] == 3
        assert result["database_name"] == "testdb"
        
        # Verify context was updated
        mock_context.set_shared_value.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_discover_patterns_step_existing_clients(self):
        """Test discover patterns step with existing clients."""
        # Setup mock context with existing clients
        mock_repomix = AsyncMock()
        mock_github = AsyncMock()
        
        mock_context = MagicMock()
        mock_context._clients = {
            'ovr_repomix': mock_repomix,
            'ovr_github': mock_github
        }
        mock_context.set_shared_value = MagicMock()
        
        # Mock pattern discovery
        with patch.object(PatternDiscoveryEngine, 'discover_patterns_in_repository') as mock_discover:
            mock_discover.return_value = {
                "total_files": 5,
                "matched_files": 2,
                "files": [],
                "database_name": "testdb"
            }
            
            result = await discover_patterns_step(
                mock_context, None, "testdb", "test", "repo"
            )
        
        # Verify execution used existing clients
        assert result["total_files"] == 5
        mock_discover.assert_called_once_with(
            repomix_client=mock_repomix,
            github_client=mock_github,
            repo_url="https://github.com/test/repo",
            database_name="testdb",
            repo_owner="test",
            repo_name="repo"
        )
    
    @pytest.mark.asyncio
    async def test_discover_patterns_step_exception(self):
        """Test discover patterns step with exception."""
        # Setup mock context
        mock_context = MagicMock()
        mock_context._clients = {}
        mock_context.config.config_path = "/test/path"
        
        # Setup mock to raise exception
        with patch('clients.RepomixMCPClient') as mock_class:
            mock_class.side_effect = Exception("Client creation failed")
            
            result = await discover_patterns_step(
                mock_context, None, "testdb", "test", "repo"
            )
        
        # Should return error result
        assert result["database_name"] == "testdb"
        assert result["total_files"] == 0
        assert result["matched_files"] == 0
        assert result["files"] == []
        assert "error" in result
        assert "Client creation failed" in result["error"]


class TestPatternDiscoveryIntegration:
    """Integration tests for pattern discovery components."""
    
    @pytest.mark.asyncio
    async def test_full_pattern_discovery_workflow(self):
        """Test the full pattern discovery workflow integration."""
        
        # Mock clients and engine
        mock_repomix_client = AsyncMock()
        
        # This will be the mock return from analyze_repository_structure
        mock_analysis_result = {
            "files": [
                {"path": "config.py", "content": "DB_NAME = 'testdb'", "type": "python", "size": 100},
                {"path": "schema.sql", "content": "CREATE TABLE testdb.users", "type": "sql", "size": 200},
                {"path": "service.yaml", "content": "database: testdb", "type": "yaml", "size": 50},
                {"path": "README.md", "content": "The testdb is used for...", "type": "markdown", "size": 75}
            ],
            "structure": {"total_directories": 1, "max_depth": 1},
            "total_size": 425
        }
        
        with patch.object(PatternDiscoveryEngine, 'analyze_repository_structure', return_value=mock_analysis_result) as mock_analyze:
            engine = PatternDiscoveryEngine()
            
            result = await engine.discover_patterns_in_repository(
                repomix_client=mock_repomix_client, 
                github_client=AsyncMock(),
                repo_url="https://github.com/test/myapp",
                repo_owner="test", 
                repo_name="myapp", 
                database_name="testdb"
            )
            
            # Verify results
            assert "total_files" in result
            assert result["total_files"] == 4
            assert "files_matched" in result
            assert len(result["files_matched"]) > 0
            
            # Verify that high-confidence matches are found
            high_confidence_files = [f for f in result["files_matched"] if f["match_confidence"] > 0.7]
            assert len(high_confidence_files) > 0
            
            mock_analyze.assert_called_once() 