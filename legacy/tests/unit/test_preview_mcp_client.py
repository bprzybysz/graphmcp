"""
Unit tests for Preview MCP Client integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from clients.preview_mcp import PreviewMCPClient, GraphMCPWorkflowExecutor
from clients.preview_mcp.context import WorkflowContext, WorkflowStep, WorkflowStatus


class TestGraphMCPWorkflowExecutor:
    """Test the GraphMCP workflow executor."""
    
    def test_init(self):
        """Test executor initialization."""
        executor = GraphMCPWorkflowExecutor()
        assert executor.mcp_clients == {}
        
        # Test with MCP clients
        mock_clients = {"github": Mock(), "slack": Mock()}
        executor = GraphMCPWorkflowExecutor(mock_clients)
        assert executor.mcp_clients == mock_clients
    
    @pytest.mark.asyncio
    async def test_execute_step(self):
        """Test step execution."""
        executor = GraphMCPWorkflowExecutor()
        
        # Create a workflow context with a step
        context = WorkflowContext()
        step = context.add_step("test_step", {"input": "test"})
        
        # Execute the step
        result = await executor.execute_step(context, step.id)
        
        # Verify result
        assert result["step_name"] == "test_step"
        assert result["status"] == "completed"
        assert result["input_data"] == {"input": "test"}
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_execute_step_not_found(self):
        """Test step execution with invalid step ID."""
        executor = GraphMCPWorkflowExecutor()
        context = WorkflowContext()
        
        with pytest.raises(ValueError, match="Step invalid_id not found"):
            await executor.execute_step(context, "invalid_id")


class TestPreviewMCPClient:
    """Test the Preview MCP Client."""
    
    def test_init(self):
        """Test client initialization."""
        client = PreviewMCPClient("mcp_config.json")
        assert client.SERVER_NAME == "preview-mcp"
        assert client.server_name == "preview-mcp"
        assert isinstance(client.workflow_executor, GraphMCPWorkflowExecutor)
    
    def test_init_with_mcp_clients(self):
        """Test client initialization with other MCP clients."""
        mock_clients = {"github": Mock(), "slack": Mock()}
        client = PreviewMCPClient("mcp_config.json", mock_clients)
        assert client.workflow_executor.mcp_clients == mock_clients
    
    @pytest.mark.asyncio
    async def test_list_available_tools_fallback(self):
        """Test listing tools with fallback when request fails."""
        client = PreviewMCPClient("mcp_config.json")
        
        # Mock the _send_mcp_request to raise an exception
        with patch.object(client, '_send_mcp_request', side_effect=Exception("Connection failed")):
            tools = await client.list_available_tools()
        
        # Should return fallback tools
        expected_tools = [
            "create_workflow",
            "execute_workflow", 
            "get_workflow_status",
            "stream_workflow_events"
        ]
        assert tools == expected_tools
    
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check."""
        client = PreviewMCPClient("mcp_config.json")
        
        # Mock successful tool listing
        with patch.object(client, 'list_available_tools', return_value=["create_workflow"]):
            result = await client.health_check()
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test failed health check."""
        client = PreviewMCPClient("mcp_config.json")
        
        # Mock failed tool listing
        with patch.object(client, 'list_available_tools', side_effect=Exception("Connection failed")):
            result = await client.health_check()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_create_workflow(self):
        """Test workflow creation."""
        client = PreviewMCPClient("mcp_config.json")
        
        expected_result = {
            "workflow_id": "test-workflow-id",
            "status": "pending",
            "total_steps": 2
        }
        
        with patch.object(client, 'call_tool_with_retry', return_value=expected_result) as mock_call:
            result = await client.create_workflow(
                "test_workflow", 
                [{"name": "step1"}, {"name": "step2"}],
                "user123"
            )
        
        # Verify the call
        mock_call.assert_called_once_with("create_workflow", {
            "workflow_name": "test_workflow",
            "steps": [{"name": "step1"}, {"name": "step2"}],
            "user_id": "user123"
        })
        assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_execute_workflow(self):
        """Test workflow execution."""
        client = PreviewMCPClient("mcp_config.json")
        
        expected_result = {
            "success": True,
            "workflow_id": "test-workflow-id",
            "status": "completed"
        }
        
        with patch.object(client, 'call_tool_with_retry', return_value=expected_result) as mock_call:
            result = await client.execute_workflow("test-workflow-id")
        
        mock_call.assert_called_once_with("execute_workflow", {"workflow_id": "test-workflow-id"})
        assert result == expected_result
    
    @pytest.mark.asyncio
    async def test_run_workflow_end_to_end(self):
        """Test end-to-end workflow execution."""
        client = PreviewMCPClient("mcp_config.json")
        
        create_result = {"workflow_id": "test-workflow-id", "status": "pending"}
        execute_result = {"success": True, "status": "completed"}
        
        with patch.object(client, 'create_workflow', return_value=create_result) as mock_create, \
             patch.object(client, 'execute_workflow', return_value=execute_result) as mock_execute:
            
            result = await client.run_workflow_end_to_end(
                "test_workflow",
                [{"name": "step1"}],
                "user123"
            )
        
        # Verify calls
        mock_create.assert_called_once_with("test_workflow", [{"name": "step1"}], "user123")
        mock_execute.assert_called_once_with("test-workflow-id")
        
        # Verify result structure
        assert result["workflow_id"] == "test-workflow-id"
        assert result["creation"] == create_result
        assert result["execution"] == execute_result


@pytest.mark.asyncio
async def test_workflow_context_integration():
    """Test integration between executor and workflow context."""
    executor = GraphMCPWorkflowExecutor()
    
    # Create a workflow with multiple steps
    context = WorkflowContext(user_id="test_user")
    step1 = context.add_step("analysis", {"repo": "test/repo"})
    step2 = context.add_step("processing", {"data": "test_data"})
    
    # Execute steps
    result1 = await executor.execute_step(context, step1.id)
    result2 = await executor.execute_step(context, step2.id)
    
    # Verify results
    assert result1["step_name"] == "analysis"
    assert result2["step_name"] == "processing"
    assert result1["input_data"] == {"repo": "test/repo"}
    assert result2["input_data"] == {"data": "test_data"}


if __name__ == "__main__":
    # Simple test runner for development
    import asyncio
    
    async def run_simple_test():
        executor = GraphMCPWorkflowExecutor()
        context = WorkflowContext()
        step = context.add_step("test_step", {"test": "data"})
        
        result = await executor.execute_step(context, step.id)
        print(f"✓ Simple test passed: {result}")
    
    asyncio.run(run_simple_test()) 