"""
Preview MCP Client implementation.

This client manages the preview MCP server that provides workflow streaming
and orchestration capabilities for live console output.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import BaseMCPClient
from .context import WorkflowContext
from .server import MCPWorkflowServer, WorkflowExecutor

logger = logging.getLogger(__name__)


class GraphMCPWorkflowExecutor(WorkflowExecutor):
    """
    Workflow executor that integrates with GraphMCP client ecosystem.

    This executor can be extended to use other MCP clients for step execution.
    """

    def __init__(self, mcp_clients: Optional[Dict[str, BaseMCPClient]] = None):
        """
        Initialize with optional MCP clients for workflow execution.

        Args:
            mcp_clients: Dictionary of MCP clients by name for executing steps
        """
        self.mcp_clients = mcp_clients or {}

    async def execute_step(
        self, context: WorkflowContext, step_id: str
    ) -> Dict[str, Any]:
        """
        Execute a workflow step using available MCP clients or mock execution.

        Args:
            context: Workflow context
            step_id: ID of step to execute

        Returns:
            Step execution result
        """
        # Find the step
        step = None
        for s in context.steps:
            if s.id == step_id:
                step = s
                break

        if not step:
            raise ValueError(f"Step {step_id} not found in workflow")

        logger.info(f"Executing step: {step.name}")

        # For now, simulate step execution
        # In a real implementation, this would route to appropriate MCP clients
        # based on step.name or step.input_data

        await asyncio.sleep(0.1)  # Simulate work

        result = {
            "step_name": step.name,
            "status": "completed",
            "message": f"Step '{step.name}' executed successfully",
            "input_data": step.input_data,
            "timestamp": context.updated_at.isoformat(),
        }

        logger.info(f"Step {step.name} completed with result: {result}")
        return result


class PreviewMCPClient(BaseMCPClient):
    """
    MCP client for the preview workflow server.

    This client provides workflow orchestration and streaming capabilities
    for live console output of workflow execution.
    """

    SERVER_NAME = "preview-mcp"

    def __init__(
        self,
        config_path: str | Path,
        mcp_clients: Optional[Dict[str, BaseMCPClient]] = None,
    ):
        """
        Initialize PreviewMCP client.

        Args:
            config_path: Path to MCP configuration file
            mcp_clients: Optional dictionary of other MCP clients for workflow execution
        """
        super().__init__(config_path)
        self.workflow_executor = GraphMCPWorkflowExecutor(mcp_clients)
        self._workflow_server: Optional[MCPWorkflowServer] = None

    async def _get_workflow_server(self) -> MCPWorkflowServer:
        """Get or create the workflow server instance."""
        if self._workflow_server is None:
            self._workflow_server = MCPWorkflowServer(self.workflow_executor)
        return self._workflow_server

    async def list_available_tools(self) -> List[str]:
        """
        List available tools for this MCP server.

        Returns:
            List of available tool names
        """
        try:
            result = await self._send_mcp_request("tools/list", {})
            return [tool["name"] for tool in result.get("tools", [])]
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return [
                "create_workflow",
                "execute_workflow",
                "get_workflow_status",
                "stream_workflow_events",
            ]

    async def health_check(self) -> bool:
        """
        Perform a health check on the MCP server.

        Returns:
            True if the server is healthy, False otherwise
        """
        try:
            # Try to list tools as a health check
            await self.list_available_tools()
            return True
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False

    async def create_workflow(
        self,
        workflow_name: str,
        steps: List[Dict[str, Any]],
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new workflow.

        Args:
            workflow_name: Name of the workflow
            steps: List of workflow steps with name and optional input_data
            user_id: Optional user ID

        Returns:
            Workflow creation result with workflow_id
        """
        params = {"workflow_name": workflow_name, "steps": steps}
        if user_id:
            params["user_id"] = user_id

        return await self.call_tool_with_retry("create_workflow", params)

    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Execute a workflow by ID.

        Args:
            workflow_id: ID of workflow to execute

        Returns:
            Execution result
        """
        return await self.call_tool_with_retry(
            "execute_workflow", {"workflow_id": workflow_id}
        )

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get workflow status.

        Args:
            workflow_id: ID of workflow

        Returns:
            Workflow status information
        """
        return await self.call_tool_with_retry(
            "get_workflow_status", {"workflow_id": workflow_id}
        )

    async def stream_workflow_events(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get streaming endpoint information for workflow events.

        Args:
            workflow_id: ID of workflow

        Returns:
            Streaming endpoint information
        """
        return await self.call_tool_with_retry(
            "stream_workflow_events", {"workflow_id": workflow_id}
        )

    async def run_workflow_end_to_end(
        self,
        workflow_name: str,
        steps: List[Dict[str, Any]],
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create and execute a workflow in one call.

        Args:
            workflow_name: Name of the workflow
            steps: List of workflow steps
            user_id: Optional user ID

        Returns:
            Complete workflow execution result
        """
        # Create workflow
        create_result = await self.create_workflow(workflow_name, steps, user_id)
        workflow_id = create_result["workflow_id"]

        # Execute workflow
        execution_result = await self.execute_workflow(workflow_id)

        return {
            "workflow_id": workflow_id,
            "creation": create_result,
            "execution": execution_result,
        }
