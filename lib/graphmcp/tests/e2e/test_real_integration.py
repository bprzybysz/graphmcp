import asyncio
import os
import pytest
from graphmcp import MultiServerMCPClient, GitHubMCPClient
from concrete.secret_manager import load_application_secrets

# Load environment variables from .env file
load_application_secrets()

# Define constants for the test
SOURCE_OWNER = "bprzybys-nc"
SOURCE_REPO = "postgres-sample-dbs"
SLACK_CHANNEL = "C01234567"
CONFIG_PATH = "clients/mcp_config.json"


async def _perform_cleanup(github_client: GitHubMCPClient, fork_owner: str, fork_name: str, branch_name: str):
    try:
        # Attempt to delete the branch on the fork
        await github_client.delete_branch(fork_owner, fork_name, branch_name)
        print(f"Cleanup: Deleted branch {branch_name} on {fork_owner}/{fork_name}")
    except Exception as e:
        print(f"Cleanup: Failed to delete branch {branch_name} on {fork_owner}/{fork_name}: {e}")

    try:
        # Attempt to delete the forked repository
        await github_client.delete_repository(fork_owner, fork_name)
        print(f"Cleanup: Deleted forked repository {fork_owner}/{fork_name}")
    except Exception as e:
        print(f"Cleanup: Failed to delete forked repository {fork_owner}/{fork_name}: {e}")


@pytest.mark.e2e
async def test_full_github_decommission_workflow(): 