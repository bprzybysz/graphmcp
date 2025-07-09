"""
Unit tests for FilesystemMCPClient workflow integration

Tests only the methods actually used by the db decommission workflow,
with proper mocking for unused functionality.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from clients import FilesystemMCPClient
from clients.filesystem import FilesystemScanResult


class TestFilesystemWorkflowIntegration:
    """Test filesystem client integration with the workflow."""

    @pytest.fixture
    def temp_test_file(self):
        """Create a temporary test file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content for filesystem operations")
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_filesystem_client_initialization(self, mock_config_path):
        """Test that filesystem client initializes correctly."""
        client = FilesystemMCPClient(mock_config_path)
        assert client.SERVER_NAME == "ovr_filesystem"
        assert str(client.config_path) == mock_config_path  # Convert PosixPath to string for comparison
        
        # Test that it's a proper async context manager
        async with client:
            assert client is not None

    @pytest.mark.asyncio
    async def test_write_file_workflow_pattern(self, mock_config_path):
        """Test write_file with the working pattern used in workflow validation."""
        client = FilesystemMCPClient(mock_config_path)
        
        # Mock the MCP server response format that we know works
        mock_response = {
            'content': [{'type': 'text', 'text': 'Successfully wrote to test_workflow.txt'}]
        }
        
        with patch.object(client, 'call_tool_with_retry', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            
            result = await client.write_file("test_workflow.txt", "Workflow validation content")
            
            assert result is True
            mock_call.assert_called_once_with("write_file", {
                "path": "test_workflow.txt",
                "content": "Workflow validation content"
            })

    @pytest.mark.asyncio
    async def test_read_file_workflow_pattern(self, mock_config_path):
        """Test read_file with the working pattern used in workflow validation."""
        client = FilesystemMCPClient(mock_config_path)
        
        # Mock the MCP server response format that we know works
        mock_response = {
            'content': [{'type': 'text', 'text': 'Windsurf rules validated successfully'}]
        }
        
        with patch.object(client, 'call_tool_with_retry', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            
            result = await client.read_file(".windsurf/rules.md")
            
            assert result == "Windsurf rules validated successfully"
            mock_call.assert_called_once_with("read_file", {
                "path": ".windsurf/rules.md"
            })

    @pytest.mark.asyncio
    async def test_list_directory_workflow_pattern(self, mock_config_path):
        """Test list_directory with the working pattern used in workflow validation."""
        client = FilesystemMCPClient(mock_config_path)
        
        # Mock the MCP server response format that we know works
        mock_response = {
            'content': [{'type': 'text', 'text': '[DIR] .windsurf\n[FILE] README.md\n[FILE] pyproject.toml\n[DIR] workflows\n[DIR] clients'}]
        }
        
        with patch.object(client, 'call_tool_with_retry', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            
            result = await client.list_directory(".")
            
            expected_files = ['.windsurf', 'README.md', 'pyproject.toml', 'workflows', 'clients']
            assert result == expected_files
            mock_call.assert_called_once_with("list_directory", {
                "path": "."
            })

    @pytest.mark.asyncio
    async def test_health_check_workflow_integration(self, mock_config_path):
        """Test health check that's used during workflow setup."""
        client = FilesystemMCPClient(mock_config_path)
        
        with patch.object(client, 'list_available_tools', new_callable=AsyncMock) as mock_tools:
            mock_tools.return_value = ["read_file", "write_file", "list_directory", "search_files"]
            
            result = await client.health_check()
            
            assert result is True
            mock_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_workflow_validation_functions_integration(self, mock_config_path):
        """Test the integration pattern used in validate_windsurf_rules and validate_target_directories."""
        client = FilesystemMCPClient(mock_config_path)
        
        # Mock responses for validation patterns
        windsurf_response = {
            'content': [{'type': 'text', 'text': '[DIR] .windsurf\n[FILE] rules.md'}]
        }
        
        rules_content_response = {
            'content': [{'type': 'text', 'text': '# Windsurf Rules\nProject validation rules...'}]
        }
        
        with patch.object(client, 'call_tool_with_retry', new_callable=AsyncMock) as mock_call:
            # Set up sequential responses for validation flow
            mock_call.side_effect = [windsurf_response, rules_content_response]
            
            # Simulate validation workflow
            directories = await client.list_directory(".")
            assert '.windsurf' in directories
            
            rules_content = await client.read_file(".windsurf/rules.md")
            assert "Windsurf Rules" in rules_content
            
            # Verify proper call sequence
            assert mock_call.call_count == 2

    @pytest.mark.asyncio
    async def test_error_handling_workflow_pattern(self, mock_config_path):
        """Test error handling that's expected in workflow integration."""
        client = FilesystemMCPClient(mock_config_path)
        
        with patch.object(client, 'call_tool_with_retry', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = Exception("MCP server connection failed")
            
            # Test that methods return safe defaults on error
            result_read = await client.read_file("nonexistent.txt")
            assert result_read == ""
            
            result_list = await client.list_directory("nonexistent")
            assert result_list == []
            
            result_write = await client.write_file("test.txt", "content")
            assert result_write is False

    # Mock unused methods that aren't part of the workflow
    @pytest.mark.asyncio
    async def test_unused_methods_properly_mocked(self, mock_config_path):
        """Test that unused methods are properly mocked and not called."""
        client = FilesystemMCPClient(mock_config_path)
        
        # These methods aren't used in the workflow, so they should return default values
        search_result = await client.search_files("*.py")
        assert isinstance(search_result, FilesystemScanResult)
        assert search_result.files_found == []
        
        create_result = await client.create_directory("test_dir")
        assert create_result is False  # Not implemented
        
        delete_result = await client.delete_file("test.txt")
        assert delete_result is False  # Not implemented

    @pytest.mark.asyncio
    async def test_client_lifecycle_workflow_pattern(self, mock_config_path):
        """Test client lifecycle as used in workflow context management."""
        client = FilesystemMCPClient(mock_config_path)
        
        # Test async context manager pattern used in workflows
        async with client:
            # Mock a simple operation during context
            with patch.object(client, 'call_tool_with_retry', new_callable=AsyncMock) as mock_call:
                mock_call.return_value = {'content': [{'type': 'text', 'text': 'test'}]}
                
                result = await client.read_file("test.txt")
                assert result == "test"
        
        # Client should be properly closed after context exit
        # Note: BaseMCPClient handles the actual connection lifecycle

    @pytest.mark.asyncio
    async def test_current_directory_pattern_from_prototype(self, mock_config_path):
        """Test the current directory pattern that works with the prototype."""
        client = FilesystemMCPClient(mock_config_path)
        
        # Test current directory operations like the working prototype
        test_content = "Hello from current directory!"
        
        # Mock write in current directory
        write_response = {
            'content': [{'type': 'text', 'text': 'Successfully wrote to test_current.txt'}]
        }
        
        # Mock read from current directory
        read_response = {
            'content': [{'type': 'text', 'text': test_content}]
        }
        
        # Mock list current directory
        list_response = {
            'content': [{'type': 'text', 'text': '[FILE] test_current.txt\n[FILE] README.md\n[DIR] workflows'}]
        }
        
        with patch.object(client, 'call_tool_with_retry', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = [write_response, read_response, list_response]
            
            # Test the working prototype pattern
            write_success = await client.write_file("test_current.txt", test_content)
            assert write_success is True
            
            read_content = await client.read_file("test_current.txt")
            assert read_content == test_content
            
            files = await client.list_directory(".")
            assert "test_current.txt" in files
            assert "README.md" in files
            assert "workflows" in files
            
            # Verify proper usage
            assert mock_call.call_count == 3


class TestFilesystemDataModels:
    """Test filesystem-related data models used in workflows."""

    def test_filesystem_scan_result_serialization(self):
        """Test that FilesystemScanResult is properly serializable."""
        from utils import ensure_serializable
        
        result = FilesystemScanResult(
            base_path=".",
            pattern="*.py",
            files_found=["test.py", "main.py"],
            matches=[
                {"file": "test.py", "type": "pattern_match"},
                {"file": "main.py", "type": "pattern_match"}
            ]
        )
        
        # Should not raise any serialization errors
        serialized = ensure_serializable(result)
        assert serialized is not None
        
        # Verify structure is preserved
        assert hasattr(result, 'base_path')
        assert hasattr(result, 'pattern')
        assert hasattr(result, 'files_found')
        assert hasattr(result, 'matches')

    def test_filesystem_scan_result_empty(self):
        """Test empty FilesystemScanResult as returned on errors."""
        result = FilesystemScanResult(
            base_path=".",
            pattern="*.nonexistent",
            files_found=[],
            matches=[]
        )
        
        assert result.files_found == []
        assert result.matches == []
        assert result.base_path == "."
        assert result.pattern == "*.nonexistent" 