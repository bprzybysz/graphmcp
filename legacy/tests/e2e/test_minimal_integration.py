"""
Minimal E2E Integration Test

This test follows the working prototype pattern from mcp_conductor/workbench
to ensure basic functionality works before running complex e2e tests.
"""

import pytest
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test environment setup
_github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")

@pytest.mark.e2e
class TestMinimalIntegration:
    """Minimal e2e tests based on working prototype patterns."""
    
    @pytest.mark.asyncio
    async def test_basic_workflow_import(self):
        """Test that we can import and create a basic workflow like the working prototype."""
        try:
            from workflows import WorkflowBuilder
            
            # Create a minimal workflow similar to db-demo pattern
            workflow = (WorkflowBuilder("minimal-test", "clients/mcp_config.json")
                .build()
            )
            
            assert workflow is not None
            assert workflow.config.name == "minimal-test"
            print("✅ Basic workflow import and creation successful")
            
        except Exception as e:
            pytest.fail(f"Basic workflow import failed: {e}")

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not _github_token or len(_github_token) < 20,
        reason="GITHUB_PERSONAL_ACCESS_TOKEN env var not set"
    )
    async def test_simple_github_workflow(self):
        """Test a simple GitHub workflow like the working prototype."""
        try:
            from workflows import WorkflowBuilder
            
            # Simple validation function
            async def validate_result(context, step):
                return {"status": "validated"}
            
            # Create minimal GitHub workflow
            workflow = (WorkflowBuilder("github-test", "clients/mcp_config.json")
                .custom_step("validate", "Simple Validation", validate_result)
                .build()
            )
            
            # Execute workflow
            result = await workflow.execute()
            
            assert result.status in ["completed", "partial_success"]
            assert "validate" in result.step_results
            print("✅ Simple GitHub workflow execution successful")
            
        except Exception as e:
            pytest.fail(f"Simple GitHub workflow failed: {e}")

    @pytest.mark.asyncio
    async def test_client_imports(self):
        """Test that all client imports work like in the working prototype."""
        try:
            from clients import (
                GitHubMCPClient,
                FilesystemMCPClient
            )
            
            # Test client instantiation
            github_client = GitHubMCPClient("clients/mcp_config.json")
            filesystem_client = FilesystemMCPClient("clients/mcp_config.json")
            
            assert github_client is not None
            assert filesystem_client is not None
            print("✅ Client imports and instantiation successful")
            
            # Clean up
            await github_client.close()
            await filesystem_client.close()
            
        except Exception as e:
            pytest.fail(f"Client imports failed: {e}") 