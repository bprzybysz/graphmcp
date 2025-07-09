"""MCP Server implementation with workflow orchestration."""

import asyncio
import json
from typing import Dict, Any, List, Optional, AsyncGenerator, Protocol
from datetime import datetime

from mcp import server, types
from mcp.server import Server
from mcp.server.models import InitializationOptions

from .context import WorkflowContext, WorkflowResult, WorkflowStatus
from .logging import create_workflow_logger, WorkflowLogger, configure_logging


class WorkflowExecutor(Protocol):
    """Protocol for workflow execution dependencies."""
    
    async def execute_step(self, context: WorkflowContext, step_id: str) -> Dict[str, Any]:
        """Execute a workflow step."""
        ...


class MCPWorkflowServer:
    """MCP Server for workflow management and agent orchestration."""
    
    def __init__(self, workflow_executor: WorkflowExecutor, log_level: str = "INFO"):
        """Initialize MCP server with dependencies."""
        self.workflow_executor = workflow_executor
        self.active_workflows: Dict[str, WorkflowContext] = {}
        self.workflow_loggers: Dict[str, WorkflowLogger] = {}
        
        # Configure logging
        configure_logging(log_level)
        
        # Create MCP server instance
        self.server = Server("langchain-workflow-server")
        self._setup_tools()
        self._setup_resources()
    
    def _setup_tools(self) -> None:
        """Setup MCP tools for workflow management."""
        
        @self.server.list_tools()
        async def list_tools() -> List[types.Tool]:
            """List available workflow tools."""
            return [
                types.Tool(
                    name="create_workflow",
                    description="Create a new workflow with specified steps",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow_name": {"type": "string"},
                            "steps": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "input_data": {"type": "object"}
                                    },
                                    "required": ["name"]
                                }
                            },
                            "user_id": {"type": "string"}
                        },
                        "required": ["workflow_name", "steps"]
                    }
                ),
                types.Tool(
                    name="execute_workflow",
                    description="Execute a workflow by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow_id": {"type": "string"}
                        },
                        "required": ["workflow_id"]
                    }
                ),
                types.Tool(
                    name="get_workflow_status",
                    description="Get workflow execution status",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow_id": {"type": "string"}
                        },
                        "required": ["workflow_id"]
                    }
                ),
                types.Tool(
                    name="stream_workflow_events",
                    description="Stream workflow execution events",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow_id": {"type": "string"}
                        },
                        "required": ["workflow_id"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Handle tool calls."""
            try:
                if name == "create_workflow":
                    result = await self._create_workflow(arguments)
                elif name == "execute_workflow":
                    result = await self._execute_workflow(arguments)
                elif name == "get_workflow_status":
                    result = await self._get_workflow_status(arguments)
                elif name == "stream_workflow_events":
                    result = await self._stream_workflow_events(arguments)
                else:
                    result = {"error": f"Unknown tool: {name}"}
                
                return [types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            
            except Exception as e:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)}, indent=2)
                )]
    
    def _setup_resources(self) -> None:
        """Setup MCP resources for workflow data access."""
        
        @self.server.list_resources()
        async def list_resources() -> List[types.Resource]:
            """List available workflow resources."""
            resources = []
            
            for workflow_id in self.active_workflows:
                resources.append(types.Resource(
                    uri=f"workflow://{workflow_id}",
                    name=f"Workflow {workflow_id}",
                    description=f"Workflow execution context and logs",
                    mimeType="application/json"
                ))
            
            return resources
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read workflow resource data."""
            if uri.startswith("workflow://"):
                workflow_id = uri[11:]  # Remove "workflow://" prefix
                if workflow_id in self.active_workflows:
                    context = self.active_workflows[workflow_id]
                    return json.dumps(context.dict(), indent=2)
                else:
                    raise ValueError(f"Workflow {workflow_id} not found")
            else:
                raise ValueError(f"Unknown resource URI: {uri}")
    
    async def _create_workflow(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new workflow."""
        workflow_name = args["workflow_name"]
        steps_data = args["steps"]
        user_id = args.get("user_id")
        
        # Create workflow context
        context = WorkflowContext(user_id=user_id)
        
        # Add steps to workflow
        for step_data in steps_data:
            context.add_step(
                name=step_data["name"],
                input_data=step_data.get("input_data", {})
            )
        
        # Store workflow and create logger
        self.active_workflows[context.workflow_id] = context
        self.workflow_loggers[context.workflow_id] = create_workflow_logger(
            context.workflow_id, 
            context.session_id
        )
        
        logger = self.workflow_loggers[context.workflow_id]
        logger.logger.info(
            "Workflow created",
            workflow_name=workflow_name,
            total_steps=len(steps_data),
            event_type="workflow_created"
        )
        
        return {
            "success": True,
            "workflow_id": context.workflow_id,
            "session_id": context.session_id,
            "total_steps": len(context.steps),
            "status": context.status
        }
    
    async def _execute_workflow(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow."""
        workflow_id = args["workflow_id"]
        
        if workflow_id not in self.active_workflows:
            return {"error": f"Workflow {workflow_id} not found"}
        
        context = self.active_workflows[workflow_id]
        logger = self.workflow_loggers[workflow_id]
        
        try:
            context.status = WorkflowStatus.IN_PROGRESS
            start_time = datetime.utcnow()
            
            logger.logger.info(
                "Workflow execution started",
                event_type="workflow_start"
            )
            
            # Execute each step
            for step in context.steps:
                if context.status == WorkflowStatus.FAILED:
                    break
                
                # Start step
                context.start_step(step.id)
                logger.log_step_start(step.id, step.name, step.input_data)
                
                try:
                    # Execute step using injected executor
                    output_data = await self.workflow_executor.execute_step(context, step.id)
                    
                    # Complete step
                    context.complete_step(step.id, output_data)
                    logger.log_step_complete(step.id, step.name, output_data)
                    
                except Exception as e:
                    error_msg = str(e)
                    context.fail_step(step.id, error_msg)
                    logger.log_step_error(step.id, step.name, error_msg)
                    break
            
            # Calculate execution time
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            # Log completion
            if context.status == WorkflowStatus.COMPLETED:
                logger.log_workflow_complete(
                    duration, 
                    len([s for s in context.steps if s.status == WorkflowStatus.COMPLETED]),
                    len(context.steps)
                )
            else:
                logger.log_workflow_error("Workflow execution failed")
            
            # Create result
            result = WorkflowResult.from_context(context)
            result.execution_time_seconds = duration
            
            return {
                "success": context.status == WorkflowStatus.COMPLETED,
                "workflow_id": workflow_id,
                "status": context.status,
                "execution_time_seconds": duration,
                "steps_completed": result.steps_completed,
                "total_steps": result.total_steps,
                "result_data": result.result_data
            }
        
        except Exception as e:
            logger.log_workflow_error(str(e))
            context.status = WorkflowStatus.FAILED
            return {
                "success": False,
                "error": str(e),
                "workflow_id": workflow_id
            }
    
    async def _get_workflow_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get workflow status."""
        workflow_id = args["workflow_id"]
        
        if workflow_id not in self.active_workflows:
            return {"error": f"Workflow {workflow_id} not found"}
        
        context = self.active_workflows[workflow_id]
        return context.get_summary()
    
    async def _stream_workflow_events(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Stream workflow events (placeholder for WebSocket implementation)."""
        workflow_id = args["workflow_id"]
        
        if workflow_id not in self.active_workflows:
            return {"error": f"Workflow {workflow_id} not found"}
        
        # This would be implemented with WebSocket streaming in the FastAPI layer
        return {
            "message": "Streaming endpoint available via WebSocket",
            "websocket_path": f"/ws/workflow/{workflow_id}",
            "workflow_id": workflow_id
        }
    
    async def run(self, transport_type: str = "stdio") -> None:
        """Run the MCP server."""
        if transport_type == "stdio":
            from mcp.server.stdio import stdio_server
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="langchain-workflow-server",
                        server_version="0.1.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=None,
                            experimental_capabilities={}
                        )
                    )
                )
        else:
            raise ValueError(f"Unsupported transport type: {transport_type}")


async def create_mcp_server(workflow_executor: WorkflowExecutor, log_level: str = "INFO") -> MCPWorkflowServer:
    """Factory function to create MCP server with dependencies."""
    return MCPWorkflowServer(workflow_executor, log_level) 