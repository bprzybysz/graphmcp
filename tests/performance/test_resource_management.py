import pytest
import asyncio
import gc
from unittest.mock import patch, AsyncMock

# Try to import psutil, but skip tests if it's not available
try:
    import psutil
except ImportError:
    psutil = None

from graphmcp.workflows import WorkflowBuilder
from graphmcp.clients import GitHubMCPClient


@pytest.mark.skipif(psutil is None, reason="psutil library not found, skipping resource tests")
class TestResourceManagement:
    """Test memory usage and resource cleanup."""
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, mock_config_path):
        """Test memory usage with many concurrent workflows."""
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        workflows = []
        for i in range(10):
            workflow = (WorkflowBuilder(f"load-test-{i}", mock_config_path)
                .custom_step("step1", "Test Step", lambda ctx, step: {"result": f"test-{i}"})
                .custom_step("step2", "Test Step 2", lambda ctx, step: {"result": f"test2-{i}"})
                .build()
            )
            workflows.append(workflow)
        
        # Our mock executor is sequential, so we run them one by one.
        # A real parallel runner would use asyncio.gather.
        for w in workflows:
            await w.execute()
        
        gc.collect()
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable, e.g., < 50MB. This is a loose check.
        assert memory_increase < 50 * 1024 * 1024, f"Memory increased by {memory_increase / 1024 / 1024:.1f}MB"
    
    @pytest.mark.asyncio
    async def test_session_cleanup_mock(self, mock_config_path):
        """Test that client sessions are managed (mocked)."""
        # In our simplified model, clients are created per-step if not cached.
        # This test ensures the builder logic correctly calls the client constructor.
        
        with patch('graphmcp.clients.GitHubMCPClient', autospec=True) as MockGitHubClient:
            mock_instance = MockGitHubClient.return_value
            mock_instance.analyze_repo_structure = AsyncMock(return_value={"status": "ok"})
            
            workflow = (WorkflowBuilder("session-test", mock_config_path)
                .github_analyze_repo("analyze", "https://github.com/test/repo")
                .build()
            )
            
            await workflow.execute()
            
            # Verify the client was instantiated and its method was called
            MockGitHubClient.assert_called_once_with(mock_config_path)
            mock_instance.analyze_repo_structure.assert_called_once_with("https://github.com/test/repo") 