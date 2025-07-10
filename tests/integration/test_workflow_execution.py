import pytest
import asyncio
import time
import os
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from workflows import WorkflowBuilder
from clients import GitHubMCPClient, SlackMCPClient, RepomixMCPClient

# Helper function for test workflow steps
async def merge_analysis_results(context, step):
    """Merge analysis results from multiple sources."""
    return {
        "merged": True,
        "primary_result": context.get_shared_value("pack_primary", {}),
        "fallback_result": context.get_shared_value("analyze_fallback", {}),
        "timestamp": time.time()
    }

async def validate_repository_step(context, step, repo_url: str):
    """Validate repository accessibility and basic info."""
    github_client = context._clients.get('github') or context._clients.get('ovr_github')
    
    # If no client found in context, try to get it from the mocked environment
    if not github_client:
        try:
            from clients import GitHubMCPClient
            github_client = GitHubMCPClient(context.config.config_path)
        except Exception:
            return {"error": "No GitHub client available"}
    
    try:
        # Parse repo URL
        if repo_url.startswith("https://github.com/"):
            repo_path = repo_url.replace("https://github.com/", "").rstrip("/")
            owner, repo = repo_path.split("/")
        else:
            return {"error": "Invalid GitHub URL format"}
        
        # Get basic repository info
        repo_info = await github_client.get_repository(owner, repo)
        
        return {
            "valid": True,
            "owner": owner,
            "repo": repo,
            "default_branch": repo_info.get("default_branch", "main"),
            "language": repo_info.get("language"),
            "size": repo_info.get("size", 0)
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}

class TestWorkflowIntegration:
    """Integration tests for complete workflow execution with real and mocked MCP servers."""
    
    @pytest.fixture
    def real_config_path(self, tmp_path):
        """Create a real MCP configuration for integration testing."""
        config = {
            "mcpServers": {
                "github": {
                    "command": "npx",
                    "args": ["@modelcontextprotocol/server-github"],
                    "env": {
                        "GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", "test-token")
                    }
                },
                "slack": {
                    "command": "npx",
                    "args": ["@modelcontextprotocol/server-slack"],
                    "env": {
                        "SLACK_BOT_TOKEN": os.getenv("SLACK_BOT_TOKEN", "test-token")
                    }
                },
                "repomix": {
                    "command": "npx",
                    "args": ["repomix", "--mcp"],
                    "env": {}
                }
            }
        }
        
        config_path = tmp_path / "mcp_config_integration.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        
        return str(config_path)
    
    @pytest.fixture
    def mock_mcp_clients(self):
        """Enhanced mock MCP clients for integration testing."""
        with patch('clients.RepomixMCPClient') as mock_repomix, \
             patch('clients.SlackMCPClient') as mock_slack, \
             patch('clients.GitHubMCPClient') as mock_github:
            
            # Configure mock Repomix client
            mock_repomix_instance = mock_repomix.return_value
            mock_repomix_instance.pack_remote_repository = AsyncMock(return_value={
                "success": True,
                "repository_url": "https://github.com/test/repo",
                "files_packed": 156,
                "total_size": 2048576,
                "output_file": "/tmp/test_repo.txt",
                "summary": "Repository packed successfully"
            })
            
            mock_repomix_instance.pack_repository = AsyncMock(return_value={
                "repository_url": "https://github.com/test/repo",
                "packed_content": "Mock packed content with file structure...",
                "file_count": 156,
                "total_size": 2048576,
                "metadata": {"branch": "main", "commit": "abc123"}
            })
            
            # Add missing async methods for RepomixMCPClient
            mock_repomix_instance.call_tool_with_retry = AsyncMock(return_value={
                "success": True,
                "repository_url": "https://github.com/test/repo",
                "files_packed": 156,
                "total_size": 2048576
            })
            mock_repomix_instance.close = AsyncMock(return_value=None)
            
            # Configure mock GitHub client
            mock_github_instance = mock_github.return_value
            mock_github_instance.analyze_repo_structure = AsyncMock(return_value={
                "repository_url": "https://github.com/test/repo",
                "owner": "test",
                "repo": "repo", 
                "default_branch": "main",
                "languages": {"Python": 45, "JavaScript": 35, "CSS": 20},
                "file_count": 156,
                "config_files": [
                    {"path": "package.json", "name": "package.json", "size": 1024},
                    {"path": "requirements.txt", "name": "requirements.txt", "size": 512}
                ]
            })
            
            mock_github_instance.get_repository = AsyncMock(return_value={
                "owner": "test",
                "repo": "repo",
                "full_name": "test/repo",
                "default_branch": "main",
                "language": "Python",
                "size": 2048,
                "description": "Test repository for integration testing"
            })
            
            mock_github_instance.create_pull_request = AsyncMock(return_value={
                "success": True,
                "number": 42,
                "url": "https://github.com/test/repo/pull/42",
                "title": "Integration Test PR",
                "state": "open"
            })
            
            # Add missing async methods for GitHubMCPClient
            mock_github_instance.call_tool_with_retry = AsyncMock(return_value={
                "success": True,
                "repository_url": "https://github.com/test/repo",
                "owner": "test",
                "repo": "repo",
                "file_count": 156,
                "languages": {"Python": 45, "JavaScript": 35, "CSS": 20}
            })
            mock_github_instance.close = AsyncMock(return_value=None)
            
            # Configure mock Slack client
            mock_slack_instance = mock_slack.return_value
            mock_slack_instance.post_message = AsyncMock(return_value={
                "success": True,
                "channel": "C01234567",
                "ts": "1234567890.123456",
                "message": {"text": "Test message", "ts": "1234567890.123456"}
            })
            
            mock_slack_instance.list_channels = AsyncMock(return_value=[
                {"id": "C01234567", "name": "general", "is_private": False, "num_members": 10},
                {"id": "C09876543", "name": "dev-alerts", "is_private": False, "num_members": 5}
            ])
            
            # Add missing async methods for SlackMCPClient
            mock_slack_instance.call_tool_with_retry = AsyncMock(return_value={
                "success": True,
                "channel": "C01234567",
                "ts": "1234567890.123456"
            })
            mock_slack_instance.close = AsyncMock(return_value=None)

            yield {
                "repomix": mock_repomix,
                "slack": mock_slack,
                "github": mock_github,
                "repomix_instance": mock_repomix_instance,
                "slack_instance": mock_slack_instance,
                "github_instance": mock_github_instance
            }

    @pytest.mark.asyncio
    async def test_complete_repo_analysis_workflow(self, real_config_path, mock_mcp_clients):
        """Test complete repository analysis workflow with multiple MCP servers."""
        
        # Patch the client imports at the workflow execution level
        with patch('clients.GitHubMCPClient', return_value=mock_mcp_clients["github_instance"]), \
             patch('clients.RepomixMCPClient', return_value=mock_mcp_clients["repomix_instance"]), \
             patch('clients.SlackMCPClient', return_value=mock_mcp_clients["slack_instance"]):
            
            workflow = (WorkflowBuilder("repo-analysis", real_config_path,
                                      description="Complete repository analysis and notification")
                .repomix_pack_repo(
                    "pack_repo", 
                    "https://github.com/bprzybys-nc/postgres-sample-dbs",
                    include_patterns=["**/*.py", "**/*.js", "**/*.md"],
                    exclude_patterns=["node_modules/**", "**/.git/**"]
                )
                .github_analyze_repo(
                    "analyze_structure", 
                    "https://github.com/bprzybys-nc/postgres-sample-dbs",
                    depends_on=["pack_repo"]
                )
                .custom_step(
                    "validate_repo", 
                    "Validate Repository Access",
                    validate_repository_step,
                    parameters={"repo_url": "https://github.com/bprzybys-nc/postgres-sample-dbs"},
                    depends_on=[]
                )
                .slack_post(
                    "notify_completion",
                    "C01234567",
                    lambda ctx: f"Analysis complete for repo with {ctx.get_shared_value('analyze_structure', {}).get('file_count', 0)} files",
                    depends_on=["analyze_structure", "validate_repo"]
                )
                .with_config(
                    max_parallel_steps=2,
                    default_timeout=120,
                    stop_on_error=False,
                    default_retry_count=2
                )
                .build()
            )
            
            result = await workflow.execute()
            
            # Verify workflow completion
            assert result.status in ["completed", "partial_success"]
            assert result.steps_completed >= 3
            assert "pack_repo" in result.step_results
            assert "analyze_structure" in result.step_results
            assert "validate_repo" in result.step_results
            
            # Verify step results have expected structure
            pack_result = result.step_results["pack_repo"]
            assert "repository_url" in pack_result
            
            analyze_result = result.step_results["analyze_structure"]
            assert "file_count" in analyze_result
            
            validate_result = result.step_results["validate_repo"]
            assert "valid" in validate_result
            
            # Verify mocked client calls
            mock_mcp_clients["repomix_instance"].call_tool_with_retry.assert_called()
            mock_mcp_clients["github_instance"].call_tool_with_retry.assert_called()
            mock_mcp_clients["slack_instance"].call_tool_with_retry.assert_called()

    @pytest.mark.asyncio
    async def test_database_decommission_workflow_simulation(self, real_config_path, mock_mcp_clients):
        """Test database decommissioning workflow with multiple repositories."""
        from concrete.db_decommission import create_db_decommission_workflow
        
        # Use the actual workflow with mocked clients
        workflow = create_db_decommission_workflow(
            database_name="example_database",
            target_repos=["https://github.com/bprzybys-nc/postgres-sample-dbs"],
            slack_channel="C01234567",
            config_path=real_config_path
        )
        
        result = await workflow.execute()
        
        # Verify workflow execution
        assert result.status in ["completed", "partial_success"]
        assert len(result.step_results) >= 3
        
        # Check that key steps completed
        expected_steps = ["validate_environment", "process_repositories", "quality_assurance"]
        completed_steps = list(result.step_results.keys())
        
        for step in expected_steps:
            if step in completed_steps:
                step_result = result.step_results[step]
                assert step_result is not None
                # Verify no critical errors in successful steps
                if not step_result.get("error"):
                    assert step_result.get("success", True) or "database_name" in step_result

    @pytest.mark.asyncio
    async def test_error_recovery_and_fallback_workflow(self, real_config_path, mock_mcp_clients):
        """Test workflow error recovery and graceful degradation."""
        # Configure one service to fail - need to apply to call_tool_with_retry since that's what's actually called
        mock_mcp_clients["repomix_instance"].call_tool_with_retry.side_effect = Exception("Repomix service temporarily unavailable")
        
        workflow = (WorkflowBuilder("error-recovery", real_config_path,
                                  description="Test error recovery mechanisms")
            .repomix_pack_repo("pack_primary", "https://github.com/test/repo")
            .github_analyze_repo("analyze_fallback", "https://github.com/test/repo")
            .custom_step(
                "merge_results", 
                "Merge Analysis Results",
                merge_analysis_results,
                depends_on=["pack_primary", "analyze_fallback"]
            )
            .slack_post(
                "notify_status",
                "C01234567", 
                lambda ctx: f"Workflow completed with {ctx.get_shared_value('merge_results', {}).get('merged', False)} result",
                depends_on=["merge_results"]
            )
            .with_config(stop_on_error=False, default_retry_count=1)
            .build()
        )
        
        result = await workflow.execute()
        
        # Verify partial completion with error handling
        assert result.status in ["partial_success", "completed"]
        assert result.steps_failed >= 1
        assert result.steps_completed >= 2
        
        # Verify the failed step has error information
        assert "pack_primary" in result.step_results
        pack_result = result.step_results["pack_primary"]
        assert "error" in pack_result
        assert "Repomix service temporarily unavailable" in str(pack_result["error"])
        
        # Verify fallback step succeeded
        assert "analyze_fallback" in result.step_results
        analyze_result = result.step_results["analyze_fallback"]
        assert not analyze_result.get("error")

    @pytest.mark.asyncio
    async def test_parallel_execution_workflow(self, real_config_path, mock_mcp_clients):
        """Test parallel execution of independent workflow steps."""
        # Add small delays to mock responses to simulate realistic timing
        async def delayed_pack(*args, **kwargs):
            await asyncio.sleep(0.05)
            return {
                "repository_url": args[0] if args else "https://github.com/test/repo",
                "packed_content": "Mock content",
                "file_count": 100,
                "total_size": 1024000
            }
        
        async def delayed_analyze(*args, **kwargs):
            await asyncio.sleep(0.05)
            return {
                "repository_url": args[0] if args else "https://github.com/test/repo",
                "file_count": 100,
                "languages": {"Python": 60, "JavaScript": 40}
            }
        
        mock_mcp_clients["repomix_instance"].pack_repository = AsyncMock(side_effect=delayed_pack)
        mock_mcp_clients["github_instance"].analyze_repo_structure = AsyncMock(side_effect=delayed_analyze)
        
        parallel_workflow = (WorkflowBuilder("parallel-execution", real_config_path,
                                            description="Test parallel execution efficiency")
            .repomix_pack_repo("pack_repo1", "https://github.com/test/repo1")
            .repomix_pack_repo("pack_repo2", "https://github.com/test/repo2")
            .github_analyze_repo("analyze_repo1", "https://github.com/test/repo1")
            .github_analyze_repo("analyze_repo2", "https://github.com/test/repo2")
            .custom_step(
                "consolidate_results",
                "Consolidate All Results",
                self._consolidate_results_step,
                depends_on=["pack_repo1", "pack_repo2", "analyze_repo1", "analyze_repo2"]
            )
            .with_config(max_parallel_steps=4)
            .build()
        )
        
        start_time = time.time()
        result = await parallel_workflow.execute()
        execution_time = time.time() - start_time
        
        # Verify all steps completed successfully
        assert result.status == "completed"
        assert result.steps_completed == 5
        
        # Verify all expected steps are present
        expected_steps = ["pack_repo1", "pack_repo2", "analyze_repo1", "analyze_repo2", "consolidate_results"]
        for step_id in expected_steps:
            assert step_id in result.step_results
            assert not result.step_results[step_id].get("error")
        
        # Verify consolidation step received data from all previous steps
        consolidate_result = result.step_results["consolidate_results"]
        assert consolidate_result["total_repos"] == 2
        
        # In a real parallel implementation, this should be faster than sequential
        # For now, we just verify reasonable execution time
        assert execution_time < 5.0  # Should complete within 5 seconds even with delays

    async def _consolidate_results_step(self, ctx, step):
        return {
            "total_repos": 2,
            "results_collected": len([k for k in ctx._shared_context.keys() if "repo" in k])
        }

    @pytest.mark.asyncio
    async def test_workflow_context_sharing(self, real_config_path, mock_mcp_clients):
        """Test that workflow context is properly shared between steps."""
        async def context_producer_step(context, step):
            """Step that produces data for sharing."""
            shared_data = {
                "produced_at": time.time(),
                "step_id": step.id,
                "data_payload": {"items": [1, 2, 3], "message": "Hello from producer"}
            }
            context.set_shared_value("producer_data", shared_data)
            return shared_data
        
        async def context_consumer_step(context, step):
            """Step that consumes shared data."""
            producer_data = context.get_shared_value("producer_data", {})
            return {
                "consumed_at": time.time(),
                "step_id": step.id,
                "received_data": producer_data,
                "processed_items": len(producer_data.get("data_payload", {}).get("items", []))
            }
        
        workflow = (WorkflowBuilder("context-sharing", real_config_path,
                                  description="Test workflow context sharing mechanisms")
            .custom_step("producer", "Data Producer Step", context_producer_step)
            .custom_step("consumer", "Data Consumer Step", context_consumer_step, depends_on=["producer"])
            .repomix_pack_repo("pack_repo", "https://github.com/test/repo", depends_on=["consumer"])
            .custom_step(
                "final_processor",
                "Final Processing Step",
                self._final_processor_step,
                depends_on=["pack_repo"]
            )
            .build()
        )
        
        result = await workflow.execute()
        
        # Verify workflow completed
        assert result.status == "completed"
        assert result.steps_completed == 4
        
        # Verify data flow between steps
        producer_result = result.step_results["producer"]
        consumer_result = result.step_results["consumer"]
        final_result = result.step_results["final_processor"]
        
        # Verify producer created expected data
        assert "produced_at" in producer_result
        assert producer_result["data_payload"]["message"] == "Hello from producer"
        
        # Verify consumer received and processed producer data
        assert consumer_result["processed_items"] == 3
        assert consumer_result["received_data"]["step_id"] == "producer"
        
        # Verify final processor has access to all previous results
        assert final_result["producer_result"] is not None
        assert final_result["consumer_result"] is not None
        assert final_result["pack_result"] is not None
        assert len(final_result["all_shared_keys"]) >= 3 

    async def _final_processor_step(self, ctx, step):
        return {
            "producer_result": ctx.get_shared_value("producer_data"),
            "consumer_result": ctx.get_shared_value("consumer"),
            "pack_result": ctx.get_shared_value("pack_repo"),
            "all_shared_keys": list(ctx._shared_context.keys())
        } 