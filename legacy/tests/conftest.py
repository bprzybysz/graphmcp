"""
Shared fixtures for GraphMCP tests.
"""

import pytest
import pytest_asyncio # Import pytest_asyncio
import json
import logging
from clients import GitHubMCPClient, RepomixMCPClient, SlackMCPClient, Context7MCPClient, BrowserMCPClient, FilesystemMCPClient
from pathlib import Path
import os
import time

logger = logging.getLogger(__name__)

@pytest.fixture(scope="session")
def mock_config_path(tmp_path_factory):
    """
    Creates a mock MCP server configuration for unit testing.
    This uses fake/mock servers that don't require actual network connections.
    """
    tmp_path = tmp_path_factory.mktemp("mock_config")
    
    # Mock configuration with fake servers
    config = {
        "mcpServers": {
            "ovr_github": {
                "command": "echo",
                "args": ["mock-github-server"],
                "env": {}
            },
            "ovr_slack": {
                "command": "echo", 
                "args": ["mock-slack-server"],
                "env": {}
            },
            "ovr_repomix": {
                "command": "echo",
                "args": ["mock-repomix-server"],
                "env": {}
            },
            "ovr_context7": {
                "command": "echo",
                "args": ["mock-context7-server"],
                "env": {}
            },
            "ovr_browser": {
                "command": "echo",
                "args": ["mock-browser-server"],
                "env": {}
            },
            "ovr_filesystem": {
                "command": "echo",
                "args": ["mock-filesystem-server"],
                "env": {}
            }
        }
    }
    
    config_file = tmp_path / "mock_config.json"
    config_file.write_text(json.dumps(config, indent=2))
    return str(config_file)

@pytest.fixture(scope="session")
def real_config_path(tmp_path_factory):
    """
    Loads MCP server configurations from clients/mcp_config.json and
    appends/overrides with e2e-specific settings and environment variables.
    """
    tmp_path = tmp_path_factory.mktemp("real_config")
    config_file_path = Path("clients/mcp_config.json")
    with open(config_file_path, 'r') as f:
        config = json.load(f)

    # Ensure mcpServers key exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}

    # Define common args for server-github and server-slack
    common_args_npx_y = ["-y"]

    # Configure GitHub server - using the updated server names
    github_config = {
        "command": "npx",
        "args": common_args_npx_y + ["@modelcontextprotocol/server-github@2025.4.8"], # Explicit version
        "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", "") }
    }
    config["mcpServers"]["ovr_github"] = github_config

    # Configure Slack server
    slack_config = {
        "command": "npx",
        "args": common_args_npx_y + ["@modelcontextprotocol/server-slack"],
        "env": { "SLACK_BOT_TOKEN": os.getenv("SLACK_BOT_TOKEN", "") }
    }
    config["mcpServers"]["ovr_slack"] = slack_config

    # Configure Repomix server
    repomix_config = {
        "command": "npx",
        "args": common_args_npx_y + ["repomix", "--mcp"]
    }
    config["mcpServers"]["ovr_repomix"] = repomix_config

    # Configure Filesystem server
    filesystem_config = {
        "command": "npx",
        "args": common_args_npx_y + ["@modelcontextprotocol/server-filesystem@2025.7.1", str(tmp_path)], # Added tmp_path as allowed dir
        "env": {
            "ALLOWED_EXTENSIONS": ".py,.js,.ts,.yaml,.yml,.md,.txt,.json"
        }
    }
    config["mcpServers"]["ovr_filesystem"] = filesystem_config

    config_file = tmp_path / "real_config.json"
    config_file.write_text(json.dumps(config, indent=2))
    return str(config_file)

@pytest_asyncio.fixture(scope="session") # Changed to pytest_asyncio.fixture
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

@pytest_asyncio.fixture(scope="session") # Changed to pytest_asyncio.fixture
async def github_test_fork(real_config_path):
    """Setup and teardown a GitHub fork for testing."""
    # We're using real_config_path to ensure the environment is set up
    # before we attempt to get the GITHUB_PERSONAL_ACCESS_TOKEN
    GITHUB_PERSONAL_ACCESS_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not GITHUB_PERSONAL_ACCESS_TOKEN:
        pytest.skip("GITHUB_PERSONAL_ACCESS_TOKEN not available")
    
    fork_data = {
        "source_repo": "https://github.com/bprzybys-nc/postgres-sample-dbs",
        "source_owner": "bprzybys-nc", 
        "source_name": "postgres-sample-dbs",
        "fork_owner": None,  # Will be set from GitHub API
        "fork_name": "postgres-sample-dbs",
        "test_branch": f"test-e2e-{int(time.time())}",
        "created_fork": False,
        "created_branch": False
    }
    
    yield fork_data  # Provide fork data to test
    
    # Cleanup in finally block
    try:
        if fork_data.get("created_branch") or fork_data.get("created_fork"):
            import subprocess
            
            # Delete test branch if created
            if fork_data.get("created_branch") and fork_data.get("fork_owner"):
                try:
                    subprocess.run([
                        "gh", "api", "-X", "DELETE",
                        f"/repos/{fork_data['fork_owner']}/{fork_data['fork_name']}/git/refs/heads/{fork_data['test_branch']}"
                    ], check=True, capture_output=True)
                    logger.info(f"✅ Deleted test branch: {fork_data['test_branch']}")
                except subprocess.CalledProcessError as e:
                    logger.warning(f"⚠️ Failed to delete branch: {e.stderr}")
            
            # Delete fork if created  
            if fork_data.get("created_fork") and fork_data.get("fork_owner"):
                try:
                    subprocess.run([
                        "gh", "api", "-X", "DELETE", 
                        f"/repos/{fork_data['fork_owner']}/{fork_data['fork_name']}"
                    ], check=True, capture_output=True)
                    logger.info(f"✅ Deleted fork: {fork_data['fork_owner']}/{fork_data['fork_name']}")
                except subprocess.CalledProcessError as e:
                    logger.warning(f"⚠️ Failed to delete fork: {e.stderr}")
                    
    except Exception as e:
        logger.warning(f"⚠️ Error during GitHub cleanup: {e}") 