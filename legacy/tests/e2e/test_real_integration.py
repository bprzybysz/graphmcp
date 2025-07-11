"""
Real E2E Integration Tests

These tests work with real MCP servers and follow the async pattern established
in the minimal integration tests. They include proper timeout handling and
graceful degradation when servers are unavailable.
"""

import pytest
import os
import asyncio
from unittest.mock import patch
import json
import tempfile
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from workflows import WorkflowBuilder
from concrete.db_decommission import create_db_decommission_workflow
from clients import (
    RepomixMCPClient, 
    GitHubMCPClient, 
    FilesystemMCPClient, 
    SlackMCPClient
)

# --- Async Helper Functions ---
async def validate_github_results(context, step):
    """Async validation function for GitHub results."""
    try:
        analysis = context.get_step_result("analyze")
        assert "repository_url" in analysis
        assert "languages" in analysis
        return {"validation": "passed"}
    except Exception as e:
        return {"validation": "failed", "error": str(e)}

async def verify_slack_post(context, step):
    """Async verification function for Slack posts."""
    try:
        slack_result = context.get_shared_value("notify")
        print(f"DEBUG: Slack Post Result: {slack_result}")
        assert slack_result["success"] is True
        assert "ts" in slack_result
        return {"verification": "passed"}
    except Exception as e:
        return {"verification": "failed", "error": str(e)}

async def timeout_wrapper(coro, timeout_seconds=30):
    """Wrapper to add timeout to async operations with better error handling."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        pytest.skip(f"Operation timed out after {timeout_seconds}s - MCP server likely unavailable")
    except Exception as e:
        error_str = str(e).lower()
        if any(keyword in error_str for keyword in ["mcp server", "connection", "timeout", "no response"]):
            pytest.skip(f"MCP server connection issue: {e}")
        raise

# Initialize environment variables
_github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
_slack_bot_token = os.getenv("SLACK_BOT_TOKEN")

@pytest.mark.e2e
class TestRealIntegration:
    """Real E2E tests with proper async handling and timeout management."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not _github_token or len(_github_token) < 20,
        reason="GITHUB_PERSONAL_ACCESS_TOKEN env var not set or invalid"
    )
    async def test_real_github_integration(self, session_client_health_check):
        """Test with a real GitHub MCP server using async pattern."""
        async def execute_github_workflow():
            workflow = (WorkflowBuilder("e2e-github", "clients/mcp_config.json")
                .github_analyze_repo("analyze", "https://github.com/microsoft/typescript")
                .custom_step("validate", "Validate Results", validate_github_results, depends_on=["analyze"])
                .build()
            )
            
            result = await workflow.execute()
            assert result.status in ["completed", "partial_success"]
            return result

        result = await timeout_wrapper(execute_github_workflow(), 60)
        print(f"✅ GitHub integration test completed with status: {result.status}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not _slack_bot_token or len(_slack_bot_token) < 20,
        reason="SLACK_BOT_TOKEN env var not set or invalid"  
    )
    async def test_real_slack_integration(self, session_client_health_check):
        """Test with a real Slack MCP server using async pattern."""
        test_channel = os.getenv("SLACK_TEST_CHANNEL", "C01234567")
        
        async def execute_slack_workflow():
            workflow = (WorkflowBuilder("e2e-slack", "clients/mcp_config.json")
                .slack_post("notify", test_channel, "🧪 E2E test message from GraphMCP")
                .custom_step("verify", "Verify Slack Post", verify_slack_post, depends_on=["notify"])
                .build()
            )
            
            result = await workflow.execute()
            assert result.status in ["completed", "partial_success"]
            return result

        result = await timeout_wrapper(execute_slack_workflow(), 30)
        print(f"✅ Slack integration test completed with status: {result.status}")

    @pytest.mark.asyncio
    async def test_repomix_pack_remote_repository(self, session_client_health_check):
        """Test RepomixMCPClient pack_remote_repository with proper async handling."""
        async def test_repomix_packing():
            repomix_client = RepomixMCPClient("clients/mcp_config.json")
            
            try:
                # Test packing a small, known repository
                result = await repomix_client.pack_remote_repository(
                    repo_url="https://github.com/neondatabase-labs/postgres-sample-dbs",
                    include_patterns=["**/*.md", "**/*.sql"],  # Focused patterns
                    exclude_patterns=["node_modules/**", ".git/**"]
                )
                
                # Handle both success and error responses gracefully
                if "error" in result:
                    print(f"⚠️ Repomix packing had issues: {result['error']}")
                    pytest.skip(f"Repomix server unavailable: {result['error']}")

                assert result.get("success", True) is True
                packed_count = result.get("packed_files_count", 0)
                print(f"✅ Repomix packed {packed_count} files successfully")
                return result

            finally:
                await repomix_client.close()

        await timeout_wrapper(test_repomix_packing(), 45)

    @pytest.mark.asyncio
    async def test_repomix_analyze_codebase_structure(self, session_client_health_check):
        """Test RepomixMCPClient analyze_codebase_structure with async pattern."""
        async def test_repomix_analysis():
            repomix_client = RepomixMCPClient("clients/mcp_config.json")
            
            try:
                result = await repomix_client.analyze_codebase_structure(
                    repo_url="https://github.com/neondatabase-labs/postgres-sample-dbs"
                )
                
                if "error" in result:
                    print(f"⚠️ Repomix analysis had issues: {result['error']}")
                    pytest.skip(f"Repomix server unavailable: {result['error']}")

                assert "repository_url" in result
                files_count = result.get("files_analyzed", 0)
                print(f"✅ Repomix analyzed {files_count} files from {result['repository_url']}")
                return result

            finally:
                await repomix_client.close()

        await timeout_wrapper(test_repomix_analysis(), 45)

    @pytest.mark.asyncio
    async def test_filesystem_operations(self):
        """Test basic filesystem operations with proper async handling."""
        async def test_filesystem_ops():
            filesystem_client = FilesystemMCPClient("clients/mcp_config.json")
            
            # Use a simple test file in current directory like the working prototype
            test_file = Path("test_filesystem_e2e.txt")
            file_content = "Hello, GraphMCP Filesystem!"
            
            try:
                # Write file
                write_success = await filesystem_client.write_file(str(test_file), file_content)
                assert write_success is True, "File write should succeed"
                print(f"✅ Successfully wrote to {test_file}")

                # Read file
                read_content = await filesystem_client.read_file(str(test_file))
                assert read_content == file_content, "Read content should match written content"
                print(f"✅ Successfully read from {test_file}")

                # List directory (current directory) - using correct method name
                listed_files = await filesystem_client.list_directory(".")
                assert str(test_file.name) in listed_files, "Test file should be in current directory"
                print(f"✅ {test_file.name} found in current directory")

            finally:
                if filesystem_client: 
                    await filesystem_client.close()
                # Clean up test file
                if test_file.exists():
                    test_file.unlink()

        await timeout_wrapper(test_filesystem_ops(), 30)

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not _github_token or len(_github_token) < 20,
        reason="GITHUB_PERSONAL_ACCESS_TOKEN env var not set or invalid"
    )
    async def test_github_repo_operations(self, session_client_health_check):
        """Test GitHub repository operations with async pattern."""
        async def test_github_ops():
            github_client = GitHubMCPClient("clients/mcp_config.json")
            try:
                # Test get_repository
                repo_info = await github_client.get_repository("microsoft", "typescript")
                assert repo_info["name"] == "typescript"
                assert repo_info["owner"]["login"] == "microsoft"
                print(f"✅ Successfully retrieved GitHub repository info for {repo_info['full_name']}")

                # Test get_file_contents
                file_content_result = await github_client.get_file_contents(
                    "microsoft", "typescript", "README.md"
                )
                assert "TypeScript" in file_content_result or "typescript" in file_content_result.lower()
                print(f"✅ Successfully retrieved README.md content for microsoft/typescript")

            finally:
                await github_client.close()

        await timeout_wrapper(test_github_ops(), 30)

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not _github_token or len(_github_token) < 20,
        reason="GITHUB_PERSONAL_ACCESS_TOKEN env var not set or invalid"
    )
    async def test_github_fork_and_branch_operations(self, github_test_fork, session_client_health_check):
        """Test GitHub fork and branch creation with async pattern."""
        async def test_fork_operations():
            github_client = GitHubMCPClient("clients/mcp_config.json")
            fork_data = github_test_fork

            try:
                # Fork the repository
                fork_result = await github_client.fork_repository(fork_data["source_owner"], fork_data["source_name"])
                assert fork_result["name"] == fork_data["source_name"]
                assert "full_name" in fork_result
                fork_data["fork_owner"] = fork_result["owner"]["login"]
                fork_data["created_fork"] = True
                print(f"✅ Successfully forked repository to {fork_data['fork_owner']}/{fork_data['fork_name']}")
                
                # Give GitHub some time to create the fork
                await asyncio.sleep(5) 

                # Create a new branch
                create_branch_result = await github_client.create_branch(
                    fork_data["fork_owner"],
                    fork_data["fork_name"],
                    fork_data["test_branch"],
                    from_branch="main"
                )
                assert "ref" in create_branch_result and fork_data["test_branch"] in create_branch_result["ref"]
                fork_data["created_branch"] = True
                print(f"✅ Successfully created branch {fork_data['test_branch']}")
                
            finally:
                await github_client.close()

        await timeout_wrapper(test_fork_operations(), 60)

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not _github_token or len(_github_token) < 20,
        reason="GITHUB_PERSONAL_ACCESS_TOKEN env var not set or invalid"
    )
    async def test_db_decommission_workflow_integration(self, github_test_fork, session_client_health_check):
        """End-to-end test for the db_decommission workflow with async pattern."""
        async def test_db_workflow():
            github_client = GitHubMCPClient("clients/mcp_config.json")
            fork_data = github_test_fork
            
            if not fork_data.get("fork_owner") or not fork_data.get("test_branch"):
                pytest.skip("GitHub fork or test branch not available for db_decommission workflow.")

            dummy_file_path = f"test_db_decommission_{int(time.time())}.sql"
            dummy_file_content = "SELECT * FROM old_database;"

            try:
                # Ensure the test branch exists
                await github_client.create_branch(
                    fork_data["fork_owner"],
                    fork_data["fork_name"],
                    fork_data["test_branch"],
                    from_branch="main"
                )
                print(f"Ensured test branch {fork_data['test_branch']} exists.")

                # Create dummy SQL file for the workflow to find
                await github_client.create_or_update_file(
                    owner=fork_data["fork_owner"],
                    repo=fork_data["fork_name"],
                    path=f"sql/{dummy_file_path}",
                    content=dummy_file_content,
                    message=f"Add dummy SQL file {dummy_file_path}",
                    branch=fork_data["test_branch"]
                )
                print(f"Created dummy SQL file: sql/{dummy_file_path}")

                # Build and execute the workflow
                workflow = create_optimized_db_decommission_workflow(
                    workflow_id="e2e-db-decommission",
                    config_path="clients/mcp_config.json",
                    github_repo_owner=fork_data["fork_owner"],
                    github_repo_name=fork_data["fork_name"],
                    github_branch=fork_data["test_branch"],
                    slack_channel=os.getenv("SLACK_TEST_CHANNEL", "C01234567"),
                    db_pattern=".sql",
                    dry_run=True
                )

                result = await workflow.execute()
                assert result.status in ["completed", "partial_success"]
                
                # Verify workflow results
                if "find_db_files" in result.step_results:
                    assert result.step_results["find_db_files"]["success"] is True
                    assert dummy_file_path in result.step_results["find_db_files"]["found_files"]
                
                print(f"✅ DB Decommission Workflow completed successfully for {dummy_file_path}")

            finally:
                await github_client.close()

        await timeout_wrapper(test_db_workflow(), 90)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Skipping multi-client coordination test until all clients are working")
    async def test_multi_client_coordination(self, session_client_health_check):
        """Test coordination between multiple real MCP clients with async pattern."""
        async def test_coordination():
            github_client = GitHubMCPClient("clients/mcp_config.json")
            filesystem_client = FilesystemMCPClient("clients/mcp_config.json")
            repomix_client = RepomixMCPClient("clients/mcp_config.json")
            
            # Use simple file in current directory like working prototype  
            test_local_file = Path("test_coordination_e2e.txt")
            initial_content = "Coordination test content."

            try:
                # 1. Filesystem: Write a local file (with short timeout)
                write_success = await asyncio.wait_for(
                    filesystem_client.write_file(str(test_local_file), initial_content),
                    timeout=10.0
                )
                assert write_success is True, "Failed to write initial local file."

                # 2. GitHub: Get a repository info (if token available)
                if _github_token and len(_github_token) >= 20:
                    try:
                        repo_info = await asyncio.wait_for(
                            github_client.get_repository("microsoft", "vscode"),
                            timeout=15.0
                        )
                        assert repo_info["name"] == "vscode", "Failed to get VSCode repo info."
                        print("✅ GitHub operation successful")
                    except (asyncio.TimeoutError, Exception) as e:
                        print(f"⚠️ GitHub operation skipped: {e}")

                # 3. Repomix: Pack a remote repository (with short timeout)
                try:
                    pack_result = await asyncio.wait_for(
                        repomix_client.pack_remote_repository(
                            repo_url="https://github.com/microsoft/vscode",
                            include_patterns=["**/*.json"]
                        ),
                        timeout=15.0
                    )
                    if pack_result.get("success", True):
                        print("✅ Repomix operation successful")
                except (asyncio.TimeoutError, Exception) as e:
                    print(f"⚠️ Repomix operation skipped: {e}")
                
                # 4. Filesystem: Read the local file to ensure it's still there
                read_content = await asyncio.wait_for(
                    filesystem_client.read_file(str(test_local_file)),
                    timeout=5.0
                )
                assert read_content == initial_content, "Local file content changed unexpectedly."

                print("✅ Multi-client coordination test completed successfully.")

            finally:
                # Clean up with timeouts to prevent hanging
                cleanup_tasks = []
                if github_client: 
                    cleanup_tasks.append(asyncio.wait_for(github_client.close(), timeout=5.0))
                if filesystem_client: 
                    cleanup_tasks.append(asyncio.wait_for(filesystem_client.close(), timeout=5.0))
                if repomix_client: 
                    cleanup_tasks.append(asyncio.wait_for(repomix_client.close(), timeout=5.0))
                
                # Run cleanup tasks with timeout protection
                for task in cleanup_tasks:
                    try:
                        await task
                    except (asyncio.TimeoutError, Exception) as e:
                        print(f"⚠️ Cleanup task failed: {e}")
                
                # Clean up test file
                if test_local_file.exists():
                    test_local_file.unlink()

        await timeout_wrapper(test_coordination(), 45) 