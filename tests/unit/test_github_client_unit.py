"""
Unit tests for GitHubMCPClient methods

Tests the specific GitHub client methods used in the database decommission workflow,
including fork_repository, create_branch, and workflow integration functions.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

from clients import GitHubMCPClient
from clients.base import MCPToolError
from concrete.db_decommission import create_feature_branch_step, create_pull_request_step


class TestGitHubMCPClientUnitTests:
    """Unit tests for GitHubMCPClient methods used in database decommission workflow."""

    @pytest.fixture
    def github_client(self, mock_config_path):
        """Create a GitHubMCPClient instance for testing."""
        return GitHubMCPClient(mock_config_path)

    @pytest.fixture
    def mock_mcp_response_fork_success(self):
        """Mock successful fork repository response in MCP format."""
        fork_data = {
            "name": "postgres-sample-dbs",
            "full_name": "testuser/postgres-sample-dbs",
            "owner": {
                "login": "testuser",
                "id": 12345,
                "type": "User"
            },
            "html_url": "https://github.com/testuser/postgres-sample-dbs",
            "clone_url": "https://github.com/testuser/postgres-sample-dbs.git",
            "default_branch": "main",
            "fork": True,
            "created_at": "2024-01-15T10:30:00Z"
        }
        
        # Return in MCP response format
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(fork_data)
                }
            ]
        }

    @pytest.fixture
    def mock_mcp_response_branch_success(self):
        """Mock successful create branch response in MCP format."""
        branch_data = {
            "ref": "refs/heads/decommission-periodic_table-1642678800",
            "node_id": "MDM6UmVmMTE3MDg4ODpyZWZzL2hlYWRzL3Rlc3Q=",
            "url": "https://api.github.com/repos/testuser/postgres-sample-dbs/git/refs/heads/decommission-periodic_table-1642678800",
            "object": {
                "sha": "abc123def456",
                "type": "commit",
                "url": "https://api.github.com/repos/testuser/postgres-sample-dbs/git/commits/abc123def456"
            }
        }
        
        # Return in MCP response format
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(branch_data)
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_fork_repository_success(self, github_client, mock_mcp_response_fork_success):
        """Test successful repository forking."""
        with patch.object(github_client, 'call_tool_with_retry', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_mcp_response_fork_success
            
            result = await github_client.fork_repository("bprzybys-nc", "postgres-sample-dbs")
            
            # Verify the tool was called with correct parameters
            mock_call.assert_called_once_with("fork_repository", {
                "owner": "bprzybys-nc",
                "repo": "postgres-sample-dbs"
            })
            
            # Verify the result structure
            assert result["success"] is True
            assert result["name"] == "postgres-sample-dbs"
            assert result["full_name"] == "testuser/postgres-sample-dbs"
            assert result["owner"]["login"] == "testuser"
            assert result["html_url"] == "https://github.com/testuser/postgres-sample-dbs"
            assert result["fork"] is True
            assert result["default_branch"] == "main"

    @pytest.mark.asyncio
    async def test_fork_repository_with_organization(self, github_client):
        """Test forking to an organization."""
        # Create org-specific fork data
        org_fork_data = {
            "name": "postgres-sample-dbs",
            "full_name": "test-org/postgres-sample-dbs",
            "owner": {
                "login": "test-org",
                "id": 54321,
                "type": "Organization"
            },
            "html_url": "https://github.com/test-org/postgres-sample-dbs",
            "clone_url": "https://github.com/test-org/postgres-sample-dbs.git",
            "default_branch": "main",
            "fork": True,
            "created_at": "2024-01-15T10:30:00Z"
        }
        
        mock_org_response = {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(org_fork_data)
                }
            ]
        }
        
        with patch.object(github_client, 'call_tool_with_retry', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_org_response
            
            result = await github_client.fork_repository(
                "bprzybys-nc", 
                "postgres-sample-dbs", 
                organization="test-org"
            )
            
            # Verify the tool was called with organization parameter
            mock_call.assert_called_once_with("fork_repository", {
                "owner": "bprzybys-nc",
                "repo": "postgres-sample-dbs",
                "organization": "test-org"
            })
            
            assert result["success"] is True
            assert result["owner"]["login"] == "test-org"

    @pytest.mark.asyncio
    async def test_fork_repository_error_handling(self, github_client):
        """Test fork repository error handling."""
        with patch.object(github_client, 'call_tool_with_retry', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = Exception("Repository already exists")
            
            result = await github_client.fork_repository("bprzybys-nc", "postgres-sample-dbs")
            
            assert result["success"] is False
            assert result["owner"] == "bprzybys-nc"
            assert result["repo"] == "postgres-sample-dbs"
            assert "Repository already exists" in result["error"]

    @pytest.mark.asyncio
    async def test_create_branch_success(self, github_client, mock_mcp_response_branch_success):
        """Test successful branch creation."""
        with patch.object(github_client, 'call_tool_with_retry', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_mcp_response_branch_success
            
            result = await github_client.create_branch(
                "testuser", 
                "postgres-sample-dbs", 
                "decommission-periodic_table-1642678800"
            )
            
            # Verify the tool was called with correct parameters
            mock_call.assert_called_once_with("create_branch", {
                "owner": "testuser",
                "repo": "postgres-sample-dbs",
                "branch": "decommission-periodic_table-1642678800"
            })
            
            # Verify the result structure
            assert result["success"] is True
            assert result["ref"] == "refs/heads/decommission-periodic_table-1642678800"
            assert result["owner"] == "testuser"
            assert result["repo"] == "postgres-sample-dbs"
            assert result["branch"] == "decommission-periodic_table-1642678800"
            assert "object" in result
            assert result["object"]["sha"] == "abc123def456"

    @pytest.mark.asyncio
    async def test_create_branch_with_from_branch(self, github_client, mock_mcp_response_branch_success):
        """Test branch creation with specified source branch."""
        with patch.object(github_client, 'call_tool_with_retry', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_mcp_response_branch_success
            
            result = await github_client.create_branch(
                "testuser", 
                "postgres-sample-dbs", 
                "feature-branch",
                from_branch="develop"
            )
            
            # Verify the tool was called with from_branch parameter
            mock_call.assert_called_once_with("create_branch", {
                "owner": "testuser",
                "repo": "postgres-sample-dbs",
                "branch": "feature-branch",
                "from_branch": "develop"
            })
            
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_create_branch_error_handling(self, github_client):
        """Test create branch error handling."""
        with patch.object(github_client, 'call_tool_with_retry', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = Exception("Branch already exists")
            
            result = await github_client.create_branch(
                "testuser", 
                "postgres-sample-dbs", 
                "existing-branch"
            )
            
            assert result["success"] is False
            assert result["owner"] == "testuser"
            assert result["repo"] == "postgres-sample-dbs"
            assert result["branch"] == "existing-branch"
            assert "Branch already exists" in result["error"]

    @pytest.mark.asyncio
    async def test_create_pull_request_success(self, github_client):
        """Test successful pull request creation (existing test coverage verification)."""
        mock_pr_response = {
            "number": 42,
            "html_url": "https://github.com/testuser/postgres-sample-dbs/pull/42",
            "state": "open",
            "draft": False
        }
        
        with patch.object(github_client, 'call_tool_with_retry', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_pr_response
            
            result = await github_client.create_pull_request(
                owner="testuser",
                repo="postgres-sample-dbs",
                title="Test PR",
                head="feature-branch",
                base="main",
                body="Test PR body"
            )
            
            mock_call.assert_called_once_with("create_pull_request", {
                "owner": "testuser",
                "repo": "postgres-sample-dbs",
                "title": "Test PR",
                "head": "feature-branch",
                "base": "main",
                "body": "Test PR body"
            })
            
            assert result["success"] is True
            assert result["number"] == 42
            assert result["url"] == "https://github.com/testuser/postgres-sample-dbs/pull/42"


class TestWorkflowStepFunctions:
    """Unit tests for workflow step functions that use GitHub client methods."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock workflow context."""
        context = MagicMock()
        context._clients = {}
        context.config = MagicMock()
        context.config.config_path = "mcp_config.json"
        context.get_shared_value = MagicMock()
        context.set_shared_value = MagicMock()
        return context

    @pytest.fixture
    def mock_step(self):
        """Create a mock workflow step."""
        step = MagicMock()
        step.id = "test_step"
        return step

    @pytest.mark.asyncio
    async def test_create_feature_branch_step_success(self, mock_context, mock_step):
        """Test successful feature branch creation step."""
        # Mock GitHub client and its methods
        mock_github_client = AsyncMock()
        mock_github_client.get_repository = AsyncMock(return_value={
            "default_branch": "main",
            "name": "postgres-sample-dbs"
        })
        mock_github_client.create_branch = AsyncMock(return_value={
            "success": True,
            "ref": "refs/heads/decommission-periodic_table-1642678800",
            "node_id": "test-node-id",
            "url": "https://api.github.com/test"
        })
        
        mock_context._clients = {"ovr_github": mock_github_client}
        
        # Mock time.time() to get predictable branch names
        with patch('time.time', return_value=1642678800):
            result = await create_feature_branch_step(
                mock_context, 
                mock_step, 
                database_name="periodic_table",
                repo_owner="testuser",
                repo_name="postgres-sample-dbs"
            )
        
        # Verify GitHub client methods were called correctly
        mock_github_client.get_repository.assert_called_once_with("testuser", "postgres-sample-dbs")
        mock_github_client.create_branch.assert_called_once_with(
            owner="testuser",
            repo="postgres-sample-dbs",
            branch="decommission-periodic_table-1642678800",
            from_branch="main"
        )
        
        # Verify the result
        assert result["success"] is True
        assert result["feature_branch"] == "decommission-periodic_table-1642678800"
        assert result["default_branch"] == "main"
        assert result["repo_owner"] == "testuser"
        assert result["repo_name"] == "postgres-sample-dbs"
        
        # Verify context was updated
        mock_context.set_shared_value.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_feature_branch_step_error(self, mock_context, mock_step):
        """Test feature branch creation step error handling."""
        # Mock GitHub client with error
        mock_github_client = AsyncMock()
        mock_github_client.get_repository = AsyncMock(side_effect=Exception("Repository not found"))
        
        mock_context._clients = {"ovr_github": mock_github_client}
        
        result = await create_feature_branch_step(
            mock_context, 
            mock_step, 
            database_name="periodic_table",
            repo_owner="nonexistent",
            repo_name="repo"
        )
        
        assert "error" in result
        assert "Repository not found" in result["error"]

    @pytest.mark.asyncio
    async def test_create_pull_request_step_success(self, mock_context, mock_step):
        """Test successful pull request creation step."""
        # Mock GitHub client
        mock_github_client = AsyncMock()
        mock_github_client.create_pull_request = AsyncMock(return_value={
            "success": True,
            "number": 42,
            "url": "https://github.com/testuser/postgres-sample-dbs/pull/42"
        })
        
        mock_context._clients = {"ovr_github": mock_github_client}
        
        # Mock shared values from previous steps
        mock_context.get_shared_value.side_effect = lambda key, default=None: {
            "branch_info": {
                "success": True,
                "feature_branch": "decommission-periodic_table-1642678800",
                "default_branch": "main"
            },
            "processing_result": {
                "processed_files": [
                    {"file_path": "chart1.yaml"},
                    {"file_path": "chart2.yaml"}
                ]
            },
            "qa_result": {"confidence_score": 95.5}
        }.get(key, default)
        
        # Mock time.strftime for predictable timestamps
        with patch('time.strftime', return_value="2024-01-15 10:30:00 UTC"), \
             patch('time.gmtime'):
            result = await create_pull_request_step(
                mock_context, 
                mock_step, 
                database_name="periodic_table",
                repo_owner="testuser",
                repo_name="postgres-sample-dbs"
            )
        
        # Verify PR creation was called with correct parameters
        mock_github_client.create_pull_request.assert_called_once()
        call_args = mock_github_client.create_pull_request.call_args[1]
        
        assert call_args["owner"] == "testuser"
        assert call_args["repo"] == "postgres-sample-dbs"
        assert call_args["title"] == "🗄️ Decommission periodic_table database references"
        assert call_args["head"] == "decommission-periodic_table-1642678800"
        assert call_args["base"] == "main"
        assert "periodic_table" in call_args["body"]
        assert "chart1.yaml" in call_args["body"]
        assert "chart2.yaml" in call_args["body"]
        
        # Verify the result
        assert result["success"] is True
        assert result["pr_number"] == 42
        assert result["pr_url"] == "https://github.com/testuser/postgres-sample-dbs/pull/42"
        assert result["feature_branch"] == "decommission-periodic_table-1642678800"
        assert result["files_modified"] == 2

    @pytest.mark.asyncio
    async def test_create_pull_request_step_no_branch_info(self, mock_context, mock_step):
        """Test pull request creation step when branch info is missing."""
        mock_context._clients = {}
        mock_context.get_shared_value.side_effect = lambda key, default=None: {
            "branch_info": {"success": False}
        }.get(key, default)
        
        result = await create_pull_request_step(
            mock_context, 
            mock_step, 
            database_name="periodic_table",
            repo_owner="testuser",
            repo_name="postgres-sample-dbs"
        )
        
        assert "error" in result
        assert "No feature branch available" in result["error"]

    @pytest.mark.asyncio
    async def test_create_pull_request_step_pr_creation_failure(self, mock_context, mock_step):
        """Test pull request creation step when PR creation fails."""
        # Mock GitHub client with failure
        mock_github_client = AsyncMock()
        mock_github_client.create_pull_request = AsyncMock(return_value={
            "success": False,
            "error": "Pull request already exists"
        })
        
        mock_context._clients = {"ovr_github": mock_github_client}
        mock_context.get_shared_value.side_effect = lambda key, default=None: {
            "branch_info": {
                "success": True,
                "feature_branch": "test-branch",
                "default_branch": "main"
            },
            "processing_result": {"processed_files": []},
            "qa_result": {"confidence_score": 90.0}
        }.get(key, default)
        
        with patch('time.strftime', return_value="2024-01-15 10:30:00 UTC"), \
             patch('time.gmtime'):
            result = await create_pull_request_step(
                mock_context, 
                mock_step, 
                database_name="periodic_table",
                repo_owner="testuser",
                repo_name="postgres-sample-dbs"
            )
        
        assert "error" in result
        assert "Pull request already exists" in result["error"]


class TestGitHubClientIntegration:
    """Integration tests for GitHub client methods working together."""

    @pytest.mark.asyncio
    async def test_fork_and_branch_workflow_integration(self, mock_config_path):
        """Test the complete fork -> branch creation workflow."""
        github_client = GitHubMCPClient(mock_config_path)
        
        # Mock the fork operation in MCP format
        fork_data = {
            "name": "postgres-sample-dbs",
            "full_name": "testuser/postgres-sample-dbs",
            "owner": {"login": "testuser"},
            "html_url": "https://github.com/testuser/postgres-sample-dbs",
            "clone_url": "https://github.com/testuser/postgres-sample-dbs.git",
            "default_branch": "main",
            "fork": True
        }
        
        fork_response = {
            "content": [{"type": "text", "text": json.dumps(fork_data)}]
        }
        
        # Mock the branch creation in MCP format
        branch_data = {
            "ref": "refs/heads/test-branch",
            "node_id": "test-node",
            "url": "https://api.github.com/test",
            "object": {"sha": "abc123", "type": "commit"}
        }
        
        branch_response = {
            "content": [{"type": "text", "text": json.dumps(branch_data)}]
        }
        
        with patch.object(github_client, 'call_tool_with_retry', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = [fork_response, branch_response]
            
            # Execute the workflow: fork then create branch
            fork_result = await github_client.fork_repository("bprzybys-nc", "postgres-sample-dbs")
            assert fork_result["success"] is True
            
            branch_result = await github_client.create_branch(
                fork_result["owner"]["login"],
                fork_result["name"],
                "test-branch"
            )
            assert branch_result["success"] is True
            
            # Verify both operations were called
            assert mock_call.call_count == 2
            
            # Verify parameters for fork
            fork_call = mock_call.call_args_list[0]
            assert fork_call[0][0] == "fork_repository"
            assert fork_call[0][1]["owner"] == "bprzybys-nc"
            assert fork_call[0][1]["repo"] == "postgres-sample-dbs"
            
            # Verify parameters for branch creation
            branch_call = mock_call.call_args_list[1]
            assert branch_call[0][0] == "create_branch"
            assert branch_call[0][1]["owner"] == "testuser"
            assert branch_call[0][1]["repo"] == "postgres-sample-dbs"
            assert branch_call[0][1]["branch"] == "test-branch"

    @pytest.mark.asyncio
    async def test_serialization_safety(self, mock_config_path):
        """Test that GitHub client results are serialization-safe."""
        from utils import ensure_serializable
        
        github_client = GitHubMCPClient(mock_config_path)
        
        # Mock response in MCP format
        fork_data = {
            "name": "test-repo",
            "full_name": "user/test-repo",
            "owner": {"login": "user", "id": 123},
            "created_at": "2024-01-15T10:30:00Z"
        }
        
        fork_response = {
            "content": [{"type": "text", "text": json.dumps(fork_data)}]
        }
        
        with patch.object(github_client, 'call_tool_with_retry', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = fork_response
            
            result = await github_client.fork_repository("source", "repo")
            
            # Verify result is serialization-safe
            serialized = ensure_serializable(result)
            assert serialized is not None
            assert serialized["success"] is True
            assert serialized["name"] == "test-repo" 