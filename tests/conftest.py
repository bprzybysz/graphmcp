"""
Shared fixtures for GraphMCP tests.
"""

import pytest
import json
import logging
from clients import GitHubMCPClient, RepomixMCPClient, SlackMCPClient, Context7MCPClient, BrowserMCPClient, FilesystemMCPClient
from pathlib import Path

logger = logging.getLogger(__name__)

@pytest.fixture
def mock_config_path(tmp_path):
    """Create a mock MCP config file for testing and return its path."""
    config = {
        "mcpServers": {
            "repomix": {"command": "npx", "args": ["-y", "repomix", "--mcp"]},
            "slack": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-slack"]},
            "github": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]},
            "filesystem": {"command": "echo", "args": ["mock-fs-server"]},
            "context7": {"command": "echo", "args": ["mock-c7-server"]},
            "browser": {"command": "echo", "args": ["mock-browser-server"]},
        }
    }
    config_file = tmp_path / "test_mcp_config.json"
    config_file.write_text(json.dumps(config))
    return str(config_file)

@pytest.fixture(scope="session")
async def session_client_health_check(real_config_path):
    """Perform health checks on all MCP clients once per test session."""
    logger.info("Performing MCP client health checks...")
    
    client_classes = [
        GitHubMCPClient,
        RepomixMCPClient,
        SlackMCPClient,
        Context7MCPClient,
        BrowserMCPClient,
        FilesystemMCPClient
    ]
    
    for client_class in client_classes:
        client = None
        try:
            client = client_class(real_config_path)
            if not await client.health_check():
                pytest.skip(f"MCP client {client_class.SERVER_NAME} is not healthy. Skipping E2E tests.")
            logger.info(f"MCP client {client_class.SERVER_NAME} is healthy.")
        except Exception as e:
            pytest.skip(f"Failed to initialize or health check MCP client {client_class.SERVER_NAME}: {e}. Skipping E2E tests.")
        finally:
            if client:
                await client.close()
    
    yield 