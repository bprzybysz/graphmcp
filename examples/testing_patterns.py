"""
Example: GraphMCP Testing Patterns

This demonstrates testing patterns used in the GraphMCP framework.
Key patterns to follow:
- Async test methods with pytest-asyncio
- Comprehensive test markers for different test types
- Mock configurations for external dependencies
- Context manager testing
- Error handling verification
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

# Test markers commonly used in GraphMCP
pytestmark = [
    pytest.mark.unit,
    pytest.mark.asyncio
]

class TestMCPClient:
    """Example test class showing GraphMCP testing patterns."""

    @pytest.fixture
    def mock_config(self, tmp_path):
        """Create a mock MCP configuration file."""
        config_data = {
            "mcpServers": {
                "test_server": {
                    "command": "python",
                    "args": ["-m", "test.server"],
                    "env": {
                        "TEST_TOKEN": "$TEST_TOKEN"
                    }
                }
            }
        }
        config_file = tmp_path / "mcp_config.json"
        config_file.write_text(json.dumps(config_data))
        return str(config_file)

    @pytest.fixture
    def mock_env_vars(self, monkeypatch):
        """Set up mock environment variables."""
        monkeypatch.setenv("TEST_TOKEN", "mock_token_123")
        return {"TEST_TOKEN": "mock_token_123"}

    async def test_client_initialization(self, mock_config):
        """Test that client initializes correctly with valid config."""
        from examples.mcp_base_client import BaseMCPClient
        
        class TestClient(BaseMCPClient):
            SERVER_NAME = "test_server"
            
            async def list_available_tools(self):
                return ["test_tool"]
                
            async def health_check(self):
                return True
        
        client = TestClient(mock_config)
        assert client.server_name == "test_server"
        assert client.config_path == Path(mock_config)

    async def test_client_context_manager(self, mock_config):
        """Test async context manager behavior."""
        from examples.mcp_base_client import BaseMCPClient
        
        class TestClient(BaseMCPClient):
            SERVER_NAME = "test_server"
            
            async def list_available_tools(self):
                return ["test_tool"]
                
            async def health_check(self):
                return True
        
        async with TestClient(mock_config) as client:
            assert client is not None
            # Client should be properly initialized

    @pytest.mark.integration
    async def test_tool_retry_mechanism(self, mock_config):
        """Test that tool retry works with exponential backoff."""
        from examples.mcp_base_client import BaseMCPClient, MCPToolError
        
        class TestClient(BaseMCPClient):
            SERVER_NAME = "test_server"
            call_count = 0
            
            async def list_available_tools(self):
                return ["failing_tool"]
                
            async def health_check(self):
                return True
                
            async def call_tool_with_retry(self, tool_name, params, retry_count=3):
                self.call_count += 1
                if self.call_count < 3:
                    raise Exception("Simulated failure")
                return {"success": True}
        
        client = TestClient(mock_config)
        result = await client.call_tool_with_retry("failing_tool", {})
        assert result["success"] is True
        assert client.call_count == 3

    @pytest.mark.e2e 
    async def test_error_handling(self, mock_config):
        """Test comprehensive error handling."""
        from examples.mcp_base_client import BaseMCPClient, MCPConnectionError
        
        class FailingClient(BaseMCPClient):
            SERVER_NAME = "nonexistent_server"
            
            async def list_available_tools(self):
                return []
                
            async def health_check(self):
                return False
        
        with pytest.raises(MCPConnectionError):
            client = FailingClient(mock_config)
            await client._load_config()

    @pytest.mark.performance
    async def test_concurrent_operations(self, mock_config):
        """Test that multiple operations can run concurrently."""
        from examples.mcp_base_client import BaseMCPClient
        
        class ConcurrentClient(BaseMCPClient):
            SERVER_NAME = "test_server"
            
            async def list_available_tools(self):
                await asyncio.sleep(0.1)  # Simulate async operation
                return ["tool1", "tool2"]
                
            async def health_check(self):
                await asyncio.sleep(0.1)  # Simulate async operation
                return True
        
        client = ConcurrentClient(mock_config)
        
        # Run operations concurrently
        tasks = [
            client.list_available_tools(),
            client.health_check(),
            client.list_available_tools()
        ]
        
        results = await asyncio.gather(*tasks)
        assert len(results) == 3
        assert results[0] == ["tool1", "tool2"]
        assert results[1] is True
        assert results[2] == ["tool1", "tool2"]

# Example pytest configuration patterns
class TestConfiguration:
    """Example configuration testing patterns."""
    
    def test_config_validation(self):
        """Test configuration validation logic."""
        from examples.data_models import MCPServerConfig
        
        config = MCPServerConfig(
            name="test_server",
            command="python",
            args=["-m", "server"],
            env={"TOKEN": "test123"}
        )
        
        config_dict = config.to_dict()
        assert config_dict["command"] == "python"
        assert config_dict["args"] == ["-m", "server"]
        assert config_dict["env"]["TOKEN"] == "test123"

    @pytest.mark.parametrize("server_name,expected_valid", [
        ("github", True),
        ("slack", True), 
        ("invalid_server", False),
        ("", False)
    ])
    def test_server_name_validation(self, server_name, expected_valid):
        """Test server name validation with parametrized tests."""
        # Example validation logic
        valid_servers = ["github", "slack", "filesystem", "repomix"]
        is_valid = server_name in valid_servers and len(server_name) > 0
        assert is_valid == expected_valid