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
from concrete.db_decommission import create_db_decommission_workflow


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
            "ref": "refs/heads/decommission-example_database-1642678800",
            "node_id": "MDM6UmVmMTE3MDg4ODpyZWZzL2hlYWRzL3Rlc3Q=",
            "url": "https://api.github.com/repos/testuser/postgres-sample-dbs/git/refs/heads/decommission-example_database-1642678800",
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
                "decommission-example_database-1642678800"
            )
            
            # Verify the tool was called with correct parameters
            mock_call.assert_called_once_with("create_branch", {
                "owner": "testuser",
                "repo": "postgres-sample-dbs",
                "branch": "decommission-example_database-1642678800"
            })
            
            # Verify the result structure
            assert result["success"] is True
            assert result["ref"] == "refs/heads/decommission-example_database-1642678800"
            assert result["owner"] == "testuser"
            assert result["repo"] == "postgres-sample-dbs"
            assert result["branch"] == "decommission-example_database-1642678800"
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


class TestWorkflowCreation:
    """Unit tests for database decommissioning workflow creation."""

    def test_create_workflow_with_defaults(self):
        """Test creating workflow with default parameters."""
        workflow = create_db_decommission_workflow()
        
        # Verify workflow was created
        assert workflow is not None
        assert hasattr(workflow, 'steps')
        assert len(workflow.steps) == 4  # Should have 4 enhanced steps
        
        # Verify step names
        step_names = [step.id for step in workflow.steps]
        assert "validate_environment" in step_names
        assert "process_repositories" in step_names
        assert "quality_assurance" in step_names
        assert "workflow_summary" in step_names

    def test_create_workflow_with_custom_params(self):
        """Test creating workflow with custom parameters."""
        custom_repos = ["https://github.com/test/repo1", "https://github.com/test/repo2"]
        workflow = create_db_decommission_workflow(
            database_name="custom_db",
            target_repos=custom_repos,
            slack_channel="C98765432"
        )
        
        # Verify workflow configuration
        assert workflow is not None
        
        # Check if parameters are properly set in workflow steps
        process_step = next((step for step in workflow.steps if step.id == "process_repositories"), None)
        assert process_step is not None
        assert process_step.parameters["database_name"] == "custom_db"
        assert process_step.parameters["target_repos"] == custom_repos
        assert process_step.parameters["slack_channel"] == "C98765432"

    def test_workflow_step_dependencies(self):
        """Test that workflow steps have correct dependencies."""
        workflow = create_db_decommission_workflow()
        
        # Build a dependency map
        step_deps = {step.id: step.depends_on for step in workflow.steps}
        
        # Verify dependencies are set correctly
        assert step_deps["validate_environment"] == []  # No dependencies
        assert "validate_environment" in step_deps["process_repositories"]
        assert "process_repositories" in step_deps["quality_assurance"]
        assert "quality_assurance" in step_deps["workflow_summary"]

    def test_workflow_timeouts(self):
        """Test that workflow steps have appropriate timeouts."""
        workflow = create_db_decommission_workflow()
        
        # Create timeout map
        step_timeouts = {step.id: step.timeout_seconds for step in workflow.steps}
        
        # Verify timeout values are reasonable
        assert step_timeouts["validate_environment"] == 30
        assert step_timeouts["process_repositories"] == 600  # 10 minutes for processing
        assert step_timeouts["quality_assurance"] == 60
        assert step_timeouts["workflow_summary"] == 30


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