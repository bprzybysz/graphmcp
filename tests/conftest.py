"""
Shared fixtures for GraphMCP tests.
"""

import pytest
import json

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