"""
Workflow Execution Engine

Handles the actual execution of workflow steps, managing MCP clients,
dependencies, retry logic, and parallel execution.

This follows GraphMCP's design principles for session management
and error handling.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Set

from .models import (
    StepStatus,
    StepType,
    WorkflowExecutionContext,
    WorkflowResult,
    WorkflowStep,
)
from ..clients import (
    BrowserMCPClient,
    Context7MCPClient,
    FilesystemMCPClient,
    GitHubMCPClient,
)
from ..utils import (
    MCPConfigManager,
    MCPRetryHandler,
    MCPUtilityError,
    ensure_serializable,
)

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """
    Executes workflows with proper dependency management, parallel execution,
    and error handling following GraphMCP's proven patterns.
    """

    def __init__(self, config_manager: MCPConfigManager):
        """
        Initialize workflow engine.
        
        Args:
            config_manager: MCP configuration manager
        """
        self.config_manager = config_manager
        self.retry_handler = MCPRetryHandler()
        
        # Client cache (created fresh for each execution)
        self._clients: Dict[str, Any] = {}

    async def execute_workflow(
        self,
        steps: List[WorkflowStep],
        context: WorkflowExecutionContext
    ) -> WorkflowResult:
        """
        Execute a complete workflow.
        
        Args:
            steps: List of workflow steps to execute
            context: Execution context with shared state
            
        Returns:
            WorkflowResult with execution results and metadata
        """
        result = WorkflowResult(
            workflow_name=context.config.name,
            status="running",
            total_steps=len(steps)
        )
        
        try:
            logger.info(f"Starting workflow execution: {context.config.name}")
            
            # Initialize clients
            await self._initialize_clients(context)
            
            # Get execution order (dependency-sorted batches)
            execution_batches = self._get_execution_batches(steps)
            
            # Execute batches
            for batch_idx, batch in enumerate(execution_batches):
                logger.info(f"Executing batch {batch_idx + 1}/{len(execution_batches)}: {batch}")
                
                # Execute steps in parallel within the batch
                batch_results = await self._execute_batch(batch, steps, context, result)
                
                # Check if we should stop on error
                if context.config.stop_on_error and any(
                    step.status == StepStatus.FAILED for step in batch_results
                ):
                    logger.error("Stopping workflow due to step failure")
                    result.status = "failed"
                    break
            
            # Finalize result
            self._finalize_result(result, steps)
            
            logger.info(f"Workflow completed: {result.status} ({result.success_rate:.1f}% success)")
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            result.status = "failed"
            result.errors.append(str(e))
        
        finally:
            result.end_time = time.time()
            # Cleanup clients
            self._clients.clear()
        
        return result

    async def _initialize_clients(self, context: WorkflowExecutionContext) -> None:
        """Initialize MCP clients for the workflow."""
        config_path = context.config.config_path
        
        # Initialize clients that might be needed
        available_servers = self.config_manager.list_servers()
        
        if "github" in available_servers:
            self._clients["github"] = GitHubMCPClient(config_path, "github")
        
        if "context7" in available_servers:
            self._clients["context7"] = Context7MCPClient(config_path, "context7")
        
        if "filesystem" in available_servers:
            self._clients["filesystem"] = FilesystemMCPClient(config_path, "filesystem")
        
        if "browser" in available_servers:
            self._clients["browser"] = BrowserMCPClient(config_path, "browser")
        
        logger.debug(f"Initialized {len(self._clients)} MCP clients")

    def _get_execution_batches(self, steps: List[WorkflowStep]) -> List[List[WorkflowStep]]:
        """
        Get execution order as batches of steps that can run in parallel.
        
        Args:
            steps: List of workflow steps
            
        Returns:
            List of batches, where each batch is a list of steps that can run in parallel
        """
        step_map = {step.id: step for step in steps}
        remaining = set(step.id for step in steps)
        completed = set()
        batches = []
        
        while remaining:
            # Find steps that can run (all dependencies completed)
            ready_steps = []
            for step_id in list(remaining):
                step = step_map[step_id]
                if all(dep in completed for dep in step.depends_on):
                    ready_steps.append(step)
                    remaining.remove(step_id)
            
            if not ready_steps:
                raise ValueError("Circular dependency or missing dependency detected")
            
            batches.append(ready_steps)
            for step in ready_steps:
                completed.add(step.id)
        
        return batches

    async def _execute_batch(
        self,
        batch: List[WorkflowStep],
        all_steps: List[WorkflowStep],
        context: WorkflowExecutionContext,
        result: WorkflowResult
    ) -> List[WorkflowStep]:
        """
        Execute a batch of steps in parallel.
        
        Args:
            batch: Steps to execute in parallel
            all_steps: All workflow steps (for reference)
            context: Execution context
            result: Result object to update
            
        Returns:
            List of executed steps with updated status
        """
        # Limit parallel execution
        max_parallel = min(len(batch), context.config.max_parallel_steps)
        
        if len(batch) <= max_parallel:
            # Execute all steps in parallel
            tasks = [
                self._execute_step(step, context, result)
                for step in batch
            ]
            executed_steps = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Execute in chunks
            executed_steps = []
            for i in range(0, len(batch), max_parallel):
                chunk = batch[i:i + max_parallel]
                tasks = [
                    self._execute_step(step, context, result)
                    for step in chunk
                ]
                chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
                executed_steps.extend(chunk_results)
        
        # Handle any exceptions from parallel execution
        final_steps = []
        for i, step_result in enumerate(executed_steps):
            if isinstance(step_result, Exception):
                # Step execution failed with exception
                step = batch[i]
                step.status = StepStatus.FAILED
                step.error = str(step_result)
                step.end_time = time.time()
                logger.error(f"Step {step.id} failed with exception: {step_result}")
            else:
                step = step_result
            
            final_steps.append(step)
        
        return final_steps

    async def _execute_step(
        self,
        step: WorkflowStep,
        context: WorkflowExecutionContext,
        result: WorkflowResult
    ) -> WorkflowStep:
        """
        Execute a single workflow step.
        
        Args:
            step: Step to execute
            context: Execution context
            result: Result object to update
            
        Returns:
            Updated step with execution results
        """
        step.status = StepStatus.RUNNING
        step.start_time = time.time()
        context.current_step = step.id
        
        logger.info(f"Executing step: {step.id} ({step.step_type.value})")
        
        try:
            # Check condition if present
            if step.condition and not self._evaluate_condition(step.condition, context, result):
                step.status = StepStatus.SKIPPED
                step.result = "Condition not met"
                result.steps_skipped += 1
                logger.info(f"Step {step.id} skipped: condition not met")
                return step
            
            # Execute step based on type
            step_result = await self._execute_step_by_type(step, context)
            
            # Ensure result is serializable
            ensure_serializable(step_result)
            
            # Update step and result
            step.status = StepStatus.COMPLETED
            step.result = step_result
            result.step_results[step.id] = step_result
            result.steps_completed += 1
            
            logger.info(f"Step {step.id} completed successfully")
            
        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)
            result.steps_failed += 1
            result.errors.append(f"Step {step.id}: {str(e)}")
            result.failed_steps.append(step.id)
            
            logger.error(f"Step {step.id} failed: {e}")
        
        finally:
            step.end_time = time.time()
            context.current_step = None
        
        return step

    async def _execute_step_by_type(
        self,
        step: WorkflowStep,
        context: WorkflowExecutionContext
    ) -> Any:
        """
        Execute step based on its type.
        
        Args:
            step: Step to execute
            context: Execution context
            
        Returns:
            Step execution result
        """
        if step.step_type == StepType.CUSTOM:
            return await self._execute_custom_step(step, context)
        
        elif step.step_type == StepType.CONDITIONAL:
            return self._evaluate_condition(step.condition, context, None)
        
        else:
            # MCP tool execution
            return await self._execute_mcp_step(step, context)

    async def _execute_custom_step(
        self,
        step: WorkflowStep,
        context: WorkflowExecutionContext
    ) -> Any:
        """Execute a custom step function."""
        step_function = step.parameters.get("function")
        params = step.parameters.get("params", {})
        
        if not step_function:
            raise ValueError("Custom step missing function parameter")
        
        # Execute function with context and parameters
        if asyncio.iscoroutinefunction(step_function):
            return await step_function(context, step, **params)
        else:
            return step_function(context, step, **params)

    async def _execute_mcp_step(
        self,
        step: WorkflowStep,
        context: WorkflowExecutionContext
    ) -> Any:
        """Execute an MCP tool step."""
        server_name = step.server_name
        tool_name = step.tool_name
        params = step.parameters
        
        if server_name not in self._clients:
            raise ValueError(f"No client available for server: {server_name}")
        
        client = self._clients[server_name]
        
        # Use retry handler for MCP operations
        async def _tool_operation():
            return await client.call_tool_with_retry(tool_name, params)
        
        try:
            result = await self.retry_handler.with_retry(_tool_operation)
            return result
        except Exception as e:
            raise MCPUtilityError(f"MCP tool call failed: {e}")

    def _evaluate_condition(
        self,
        condition: str,
        context: WorkflowExecutionContext,
        result: WorkflowResult
    ) -> bool:
        """
        Evaluate a condition expression.
        
        Args:
            condition: Python expression as string
            context: Execution context
            result: Current workflow result
            
        Returns:
            Boolean result of condition evaluation
        """
        try:
            # Create evaluation context with access to step results and shared state
            eval_context = {
                "context": context,
                "result": result,
                "shared": context.shared_state,
                # Add step results for easy access
                **context.shared_state
            }
            
            # Add step results directly to context
            if result:
                for step_id, step_result in result.step_results.items():
                    eval_context[step_id] = step_result
            
            # Evaluate the condition
            return bool(eval(condition, {"__builtins__": {}}, eval_context))
            
        except Exception as e:
            logger.error(f"Condition evaluation failed: {condition} - {e}")
            return False

    def _finalize_result(self, result: WorkflowResult, steps: List[WorkflowStep]) -> None:
        """Finalize workflow result with final status and metadata."""
        if result.steps_failed > 0:
            if result.steps_completed > 0:
                result.status = "partial"
            else:
                result.status = "failed"
        else:
            result.status = "completed"
        
        # Set final result to the last completed step's result if available
        if result.step_results:
            # Find the last step that completed
            for step in reversed(steps):
                if step.id in result.step_results:
                    result.final_result = result.step_results[step.id]
                    break 