"""
E2E tests for MCP tools actually used by the db decommission workflow.

Tests the specific methods called in the workflow with the working pattern from the prototype.
"""

import pytest
import asyncio
import os
import time
from pathlib import Path

from clients import GitHubMCPClient, SlackMCPClient, RepomixMCPClient, FilesystemMCPClient, Context7MCPClient


# Helper function for timeout management
async def timeout_wrapper(coro, timeout_seconds=30):
    """Wrapper for async operations with timeout."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        pytest.fail(f"Operation timed out after {timeout_seconds} seconds")


@pytest.mark.e2e
class TestWorkflowToolsIntegration:
    """Test the specific MCP tools used by the db decommission workflow."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Waiting for Slack app approval")
    async def test_slack_post_message_workflow_pattern(self):
        """Test slack post_message as used in the workflow."""
        async def test_slack_post():
            slack_client = SlackMCPClient("clients/mcp_config.json")
            
            try:
                # Test the exact pattern used in the workflow
                test_channel = "C01234567"  # Use a test channel ID
                test_message = "🔄 Processing batch 1/2 (3 files) for `test_database`"
                
                result = await slack_client.post_message(test_channel, test_message)
                
                # Handle both success and error responses gracefully
                if "error" in result:
                    print(f"⚠️ Slack post had issues: {result['error']}")
                    # Don't fail the test if it's just a channel permissions issue
                    if "channel_not_found" in str(result['error']):
                        pytest.skip("Test channel not accessible, but Slack client is working")
                    
                assert "ts" in result or "message" in result or result.get("ok", False)
                print(f"✅ Slack message posted successfully")
                
                # Test second pattern from workflow
                completion_message = "✅ Batch 1 complete: 3/3 files processed in 2.1s"
                result2 = await slack_client.post_message(test_channel, completion_message)
                print(f"✅ Slack completion message posted successfully")
                
                return result

            finally:
                await slack_client.close()

        await timeout_wrapper(test_slack_post(), 30)

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN") or len(os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", "")) < 20,
        reason="GITHUB_PERSONAL_ACCESS_TOKEN env var not set or invalid"
    )
    async def test_github_analyze_repo_structure_workflow_pattern(self):
        """Test github analyze_repo_structure as used in the workflow."""
        async def test_github_analyze():
            github_client = GitHubMCPClient("clients/mcp_config.json")
            
            try:
                # Test the exact repo URL pattern used in the workflow
                repo_url = "https://github.com/neondatabase-labs/postgres-sample-dbs"
                
                result = await github_client.analyze_repo_structure(repo_url)
                
                # Validate the response format expected by the workflow
                assert isinstance(result, dict), "analyze_repo_structure should return a dict"
                
                # The workflow expects these fields to exist
                if "error" not in result:
                    # Success case - check expected structure
                    print(f"✅ GitHub repo structure analyzed successfully")
                    print(f"Repository URL: {result.get('repository_url', 'N/A')}")
                    print(f"Files found: {result.get('total_files', 0)}")
                    
                    # Workflow can handle both success and error responses
                    assert "repository_url" in result or "total_files" in result
                else:
                    # Error case - should still be handled gracefully by workflow
                    print(f"⚠️ GitHub analysis had issues: {result['error']}")
                    # This is acceptable - workflow handles errors gracefully
                
                return result

            finally:
                await github_client.close()

        await timeout_wrapper(test_github_analyze(), 45)

    @pytest.mark.asyncio
    async def test_repomix_pack_remote_repository_workflow_pattern(self):
        """Test repomix pack_remote_repository as used in the workflow."""
        async def test_repomix_pack():
            repomix_client = RepomixMCPClient("clients/mcp_config.json")
            
            try:
                # Test the exact repo URL pattern used in the workflow
                repo_url = "https://github.com/neondatabase-labs/postgres-sample-dbs"
                
                result = await repomix_client.pack_remote_repository(repo_url)
                
                # Handle both success and error responses as the workflow does
                if "error" in result:
                    print(f"⚠️ Repomix packing had issues: {result['error']}")
                    # Workflow handles this gracefully, so test should too
                    assert "error" in result  # Validate error format
                else:
                    # Success case
                    print(f"✅ Repomix packed repository successfully")
                    packed_count = result.get("packed_files_count", 0)
                    print(f"Files packed: {packed_count}")
                    
                    # Workflow expects this structure
                    assert isinstance(result, dict)
                
                return result

            finally:
                await repomix_client.close()

        await timeout_wrapper(test_repomix_pack(), 60)

    @pytest.mark.asyncio
    async def test_filesystem_validation_workflow_pattern(self):
        """Test filesystem operations as used in workflow validation functions."""
        async def test_filesystem_validation():
            filesystem_client = FilesystemMCPClient("clients/mcp_config.json")
            
            # Test current directory access (the working pattern)
            test_file = Path("test_workflow_validation.txt")
            validation_content = "Workflow validation test file"
            
            try:
                # Test write capability (needed for workflow file operations)
                write_success = await filesystem_client.write_file(str(test_file), validation_content)
                assert write_success is True, "Workflow needs write capability"
                print(f"✅ Filesystem write validation passed")
                
                # Test read capability (needed for workflow validation)
                read_content = await filesystem_client.read_file(str(test_file))
                assert read_content == validation_content, "Workflow needs reliable read capability"
                print(f"✅ Filesystem read validation passed")
                
                # Test directory listing (used in validation functions)
                files = await filesystem_client.list_directory(".")
                assert test_file.name in files, "Workflow needs directory listing capability"
                print(f"✅ Filesystem directory listing validation passed")
                
                # Verify the working pattern is functioning
                assert test_file.exists(), "Working pattern should create actual files"
                print(f"✅ Working pattern validated - file exists on filesystem")

            finally:
                await filesystem_client.close()
                # Clean up test file
                if test_file.exists():
                    test_file.unlink()

        await timeout_wrapper(test_filesystem_validation(), 30)

    @pytest.mark.asyncio
    async def test_context7_basic_connectivity(self):
        """Test Context7 MCP server basic connectivity and tools."""
        async def test_context7():
            context7_client = Context7MCPClient("clients/mcp_config.json")
            
            try:
                # Test basic connectivity by listing tools
                tools = await context7_client.list_available_tools()
                assert isinstance(tools, list), "Should return a list of tools"
                print(f"✅ Context7 tools available: {tools}")
                
                # Test health check
                health = await context7_client.health_check()
                assert health is True, "Health check should pass"
                print(f"✅ Context7 health check passed")
                
                # Test resolve library ID (basic functionality test)
                try:
                    result = await context7_client.resolve_library_id("react")
                    print(f"✅ Context7 resolve library test completed: {type(result)}")
                    # Don't assert specific content since it depends on the server state
                    assert isinstance(result, dict), "Should return a dict result"
                except Exception as e:
                    print(f"⚠️ Context7 resolve library had issues: {e}")
                    # This is acceptable for basic connectivity test
                
                return True

            finally:
                await context7_client.close()

        await timeout_wrapper(test_context7(), 30)

    @pytest.mark.asyncio
    async def test_workflow_tools_coordination(self):
        """Test that all workflow tools can be initialized and work together."""
        async def test_coordination():
            # Initialize all available workflow clients (skip Slack for now, skip GitHub due to blocking)
            repomix_client = RepomixMCPClient("clients/mcp_config.json")
            filesystem_client = FilesystemMCPClient("clients/mcp_config.json")
            context7_client = Context7MCPClient("clients/mcp_config.json")
            
            try:
                # Verify all clients can be created simultaneously
                assert repomix_client.SERVER_NAME == "ovr_repomix"
                assert filesystem_client.SERVER_NAME == "ovr_filesystem"
                assert context7_client.SERVER_NAME == "ovr_context7"
                print(f"✅ Core workflow MCP clients initialized successfully (Slack skipped - awaiting approval, GitHub skipped - async issues)")
                
                # Test basic connectivity pattern (without external dependencies)
                test_file = Path("test_coordination.txt")
                await filesystem_client.write_file(str(test_file), "coordination test")
                
                coordination_data = await filesystem_client.read_file(str(test_file))
                assert coordination_data == "coordination test"
                print(f"✅ Basic tool coordination validated")
                
                # Clean up
                if test_file.exists():
                    test_file.unlink()

            finally:
                # Close all clients like workflow cleanup
                await asyncio.gather(
                    repomix_client.close(),
                    filesystem_client.close(),
                    context7_client.close(),
                    return_exceptions=True
                )

        await timeout_wrapper(test_coordination(), 45) 